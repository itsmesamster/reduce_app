from math import floor
import re
import sys
from os import listdir, remove
from shutil import rmtree
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from functools import wraps, lru_cache
from pathlib import Path
from os import environ, getenv as env
from time import perf_counter, sleep
from asyncio import iscoroutinefunction
import json
import shutil
import requests

# 3rd party
import yaml

# project core
from app.core.custom_logger import logger
from app.core.processors.exceptions import APIServerConnectionError


REPORTS_DIR = "app/__reports"


def since_timestamp(hours=36) -> str:
    """Generate a timestamp from now minus HOURS in form of '2022-11-29 10:43:17.0'."""
    now = datetime.now()
    if now.weekday() == 0:  # Monday
        hours += 48
    delta = timedelta(hours=hours)
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S.0")


def setup_logging():
    """Setup general logging."""
    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>pid({process})</cyan>:<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "[{extra[jira_id]}][{extra[kpm_id]}] - <level>{message}</level>"
    )
    logger.configure(
        extra={"kpm_id": "", "jira_id": ""},
        handlers=[{"sink": sys.stdout, "format": logger_format}],
    )


def xml_to_dict(xml_elem: str | ET.Element) -> dict:
    if isinstance(xml_elem, ET.Element):
        root = xml_elem
    elif isinstance(xml_elem, str):
        root = ET.fromstring(xml_elem)
    result = {}
    for child in root:
        if len(child) == 0:
            result[child.tag] = child.text
        else:
            result[child.tag] = xml_to_dict(child)
    return result


def xml_to_yaml(xml_elem: str) -> str:
    return yaml.safe_dump(xml_to_dict(xml_elem))


def check_disk_space_left(path: str = ".") -> float:
    """Check the disk space left in a given path.
    return free space in percentage
    """
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
    stat = shutil.disk_usage(path)
    free_percentage = (stat.free / stat.total * 100).__round__(2)
    used_percentage = (stat.used / stat.total * 100).__round__(2)
    logger.info(
        f"Disk space: {(stat.free / GB).__round__(2)}GB free | "
        f"{free_percentage}% free | {used_percentage}% used "
    )
    if free_percentage < 5:
        logger.error("Less than 5% disk space left.")
    elif free_percentage < 10:
        logger.warning("Less than 10% disk space left.")
    return free_percentage


def clean_cache_dir(cache_dir: str, older_than_days: int = 4):
    logger.info(f"Cleaning cache dir [{cache_dir}]")
    if check_disk_space_left(cache_dir) < 5:
        older_than_days = 1
    elif check_disk_space_left(cache_dir) < 10 and older_than_days > 1:
        older_than_days -= 1
    try:
        dirs = listdir(cache_dir)
        limit = datetime.now() - timedelta(days=older_than_days)

        for dir_name in dirs:
            try:
                if datetime.strptime(dir_name, "%Y-%m-%d") < limit:
                    logger.info(f"Removing old cache dir: {dir_name}")
                    rmtree(f"{cache_dir}/{dir_name}")
            except ValueError:
                logger.error(
                    f"Check the dir/file {dir_name} found in "
                    f"{cache_dir} . Should be a timestamp."
                )
    except (NotADirectoryError, FileNotFoundError) as e:
        logger.error(f'Cache dir "{cache_dir}" not found: {e}')


def clean_reports_dir(older_than_days: int = 30, reports_dir: str = REPORTS_DIR):
    logger.info(f"Cleaning sync reports dir [{reports_dir}]")
    try:
        reports = listdir(reports_dir)
        limit = datetime.now() - timedelta(days=older_than_days)

        for filename in reports:
            try:
                split_filename = filename.split("_")
                if split_filename:
                    prefix = split_filename[0]
                    if datetime.strptime(prefix, "%Y-%m-%d") < limit:
                        logger.info(f"Removing old sync report [{filename}]")
                        remove(f"{reports_dir}/{filename}")
            except ValueError:
                logger.error(
                    f"Check the file name {filename} found in "
                    f"{reports_dir} . Should start with a date stamp."
                )
    except (NotADirectoryError, FileNotFoundError) as e:
        logger.error(f'Reports dir "{reports_dir}" not found: {e}')


def save_json_sync_report(data: str, file_name: str, dir_path: str = REPORTS_DIR):
    """Save env var data to file."""
    try:
        date = datetime.now().strftime("%F")
        time = datetime.now().strftime("%T.%f")[:-3]
        file_name = f"{date}_finished_at_{time}_{file_name}.json"
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        full_path = f"{dir_path}/{file_name}"
        with open(f"{full_path}", "w") as f:
            json.dump(data, f, indent=4)
            logger.info(f"Saved file: {full_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save file: {e}")


def save_var_as_file(data: str, file_name: str, dir_path: str = "saved_files"):
    """Save env var data to file."""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        full_path = f"{dir_path}/{file_name}"
        if Path(full_path).is_file():
            logger.warning(
                f"File exists: {full_path} . Overwriting it with new data ..."
            )
        with open(f"{full_path}", "w") as f:
            f.write(data)
            logger.info(f"Saved file: {full_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save file: {e}")


def save_vault_secret_as_file(
    env_var_name: str, data: str | bytes, file_name: str = None, dir_path: str = None
) -> bool:
    """Save a secret from Vault as a file, save the file path to another env var as
    env_var_name + '_FILE_PATH' and return that file path."""
    if not file_name:
        file_name = env_var_name
    if not dir_path:
        dir_path = "secrets"

    full_path = f"{dir_path}/{file_name}"

    if save_var_as_file(data, file_name, dir_path):
        logger.info(f"Saved secret {env_var_name} as file: {full_path}")
        new_env_var_name = f"{env_var_name}_FILE_PATH"
        environ[new_env_var_name] = full_path
        logger.info(f"Saved file path [{full_path}] to env var {new_env_var_name}")
        return True
    logger.error(f"Failed to save secret as file: {full_path}")


def performance_check(fn: callable):
    """Decorator to check the performance of a function."""

    @wraps(fn)
    def sync_perf_check(*args, **kwargs):
        start = perf_counter()
        fn_return = fn(*args, **kwargs)
        diff = perf_counter() - start
        if diff >= 60:
            minutes, secs = floor(diff / 60), diff % 60
            logger.info(
                f"{fn.__name__} executed in "
                f"{minutes} minutes and {secs:.2f} seconds"
            )
        else:
            logger.info(f"{fn.__name__} executed in {diff:.2f} seconds")
        return fn_return

    @wraps(fn)
    async def async_perf_check(*args, **kwargs):
        start = perf_counter()
        fn_return = fn(*args, **kwargs)
        diff = perf_counter() - start
        if diff >= 60:
            minutes, secs = floor(diff / 60), diff % 60
            logger.info(
                f"{fn.__name__} executed in "
                f"{minutes} minutes and {secs:.2f} seconds"
            )
        else:
            logger.info(f"{fn.__name__} executed in {diff:.2f} seconds")
        return fn_return

    if iscoroutinefunction(fn):
        return async_perf_check
    return sync_perf_check


def clean_str(string: str) -> str:
    """Replace multiple spaces with one space and
    strip whitespaces from the beginning and end of the string."""
    return re.sub(" +", " ", string.strip())


def compare_clean_str(str1: str, str2: str) -> bool:
    """Compare strings after cleaning them by
    replacing multiple spaces with one space and
    striping whitespaces from the beginning and end of the string."""
    return clean_str(str1) == clean_str(str2)


def clean_str_list(str_list: list[str]) -> list[str]:
    """Clean a list of strings by
    replacing multiple spaces with one space and
    striping whitespaces from the beginning and end of the string."""
    return [clean_str(string) for string in str_list]


def timed_cache(fn):
    """Decorator to cache the return value of a function for 1 hour.
    datetime acts as a renewable token to force a new cache entry
    when changed -> in this case when the hour changes
    """

    @lru_cache(maxsize=5)
    def cached(datetime: str, func, *args, **kwargs):
        return func(*args, **kwargs)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        time = str(datetime.now()).split(":")[0]
        return cached(time, fn, *args, **kwargs)

    return wrapper


def strip_date_prefix(string: str) -> str:
    """Remove date prefix from string.

    Date format: 'DD.MM.YYYY:'
    """
    year = datetime.now().year
    parts = string.split(f".{year}:", 1)
    if len(parts) > 1:
        return parts[-1]
    if datetime.now().month == 1:
        year -= 1
    return string.split(f".{year}:", 1)[-1]


def uniformed_text(text: str, remove: list[str] = None) -> str:
    text = (
        text.strip()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("”", '"')
        .replace("“", '"')
        .replace("–", "-")
        .replace("\t", " ")
        .replace("\n", " ")
        .replace("  ", " ")
        .replace("   ", " ")
        .replace("    ", " ")
    )
    if not remove:
        remove = ["📆", "📝"]
    for r in remove:
        text = text.replace(r, "")
    return strip_date_prefix(text.strip())


def difference_part(
    text_to_check_for: list[str] | str, text_to_look_in: list[str] | str
) -> bool:
    identical = 0
    different = 0
    len_text_to_look_in = len(text_to_look_in)
    for i, word in enumerate(text_to_check_for):
        if i < len_text_to_look_in and word == text_to_look_in[i]:
            identical += 1
        else:
            different += 1

    return different / len(text_to_check_for)


# find text in long string for approximate comparison
def approximate_comparison(text_to_check_for: str, text_to_look_in: str) -> bool:
    """Find text in long string for approximate comparison."""
    text_to_check_for = uniformed_text(text_to_check_for)
    text_to_look_in = uniformed_text(text_to_look_in)

    logger.debug(f"Text to check for:\n{text_to_check_for}")
    logger.debug(f"Text to look in:\n{text_to_look_in}")

    if text_to_check_for in text_to_look_in:
        return True

    for_txt_list: list[str] = text_to_check_for.split(" ")
    in_txt_list: list[str] = text_to_look_in.split(" ")

    logger.debug(f"Text to check for list:\n{for_txt_list}")
    logger.debug(f"Text to look in list:\n{in_txt_list}")

    index = -1
    str_index = 0
    for word in for_txt_list:
        for i, val in enumerate(in_txt_list):
            if val == word:
                index = i
                break
            str_index += len(f" {val}")
        if index != -1:
            # ignore prefixes like dates in in_txt_list
            in_txt_list = in_txt_list[index:]
            break

    if difference_part(for_txt_list, in_txt_list) < 0.2:
        return True

    # ignore prefixes like dates in text_to_look_in
    text_to_look_in = text_to_look_in[str_index:]
    logger.debug(
        f"Text to look in after prefix removal: {text_to_look_in[str_index:]=}"
    )

    if difference_part(text_to_check_for, text_to_look_in) < 0.2:
        return True


def connection_retry(times: int = 8, delay_minutes: int = 3):
    """Retry decorator for connection functions."""

    def decorate(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            for i in range(times):
                try:
                    logger.info(f"Connecting to {func.__name__}. Try number {i+1}")
                    return func(*args, **kwargs)
                except Exception as ex:
                    logger.error(f"Failed to connect to {func.__name__}: {ex}")
                    logger.info(f"Retrying in {delay_minutes} minutes...")
                    sleep(delay_minutes * 60)
            logger.error(
                f"Failed to connect to {func.__name__} after {times} attempts."
            )
            raise APIServerConnectionError

        return wrap

    return decorate


def convert_size(
    size_in_bytes: str | int | float,
    multiplication: int = 1000,
) -> tuple[int | float, str]:
    """Convert bytes to KB, MB, GB and
    return a tuple with size and unit."""

    units = ["B", "KB", "MB", "GB"]

    size = size_in_bytes
    if isinstance(size, str):
        size = int(size)

    for i in range(5, 0, -1):
        if size >= multiplication**i:
            size = round(size / (multiplication**i), 2)
            if str(size).split(".")[-1] == "0":
                return int(size), units[i]
            return size, units[i]
    return size, units[0]


def get_vault_secrets(vault_secrets_url: str, vault_token: str) -> dict:
    logger.info("Getting secrets from ESR LABS Vault")
    try:
        response = requests.request(
            "GET", vault_secrets_url, headers={"X-Vault-Token": vault_token}
        )
        if response.status_code != 200:
            logger.error(
                f"Could not read secret from Vault [{vault_secrets_url}]: "
                f"{response.status_code} -> {response.content}"
            )
            return {}
        secrets = response.json()
        if not secrets:
            logger.error(f"No secrets found in Vault @[{vault_secrets_url}]: ")
            return {}
        secrets: dict = secrets.get("data", {}).get("data", {})
        logger.info(f"Found {secrets.keys()} secrets in Vault")
        return secrets
    except requests.exceptions.MissingSchema as e:
        logger.error(f"Could not read secret from Vault: {e}")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Is the service connected to ESR Labs VPN? "
            f"Could not connect to Vault [{vault_secrets_url.split('/')[0]}]"
        )
        return {}


def set_vault_secrets(
    vault_secrets_url: str, vault_token: str, secrets_to_set: list[str] = None
):
    """Get secrets from ESR Labs Vault servce and set them as ENV VARS"""
    if not secrets_to_set:
        secrets_to_set = []
    vault_secrets = get_vault_secrets(vault_secrets_url, vault_token)
    for secret_name, secret_value in vault_secrets.items():
        logger.info(f"Setting/exporting secret: {secret_name} to ENV VARS")
        if not env(secret_name):
            environ[secret_name] = secret_value
        if secret_name in secrets_to_set:
            secrets_to_set.remove(secret_name)
    if secrets_to_set:
        logger.warning(
            "The following secrets were not found in the VAULT "
            f"to be set as ENV VARS: {secrets_to_set}"
        )


def names_are_equal(name_1: str, name_2: str) -> bool | None:
    name_1 = name_1.lower()
    name_2 = name_2.lower()

    remove = [",", "-"]
    for r in remove:
        name_1 = name_1.replace(r, "")
        name_2 = name_2.replace(r, "")

    if sorted(name_1.split(" ")) == sorted(name_2.split(" ")):
        return True


def check_get_set_secrets(
    vault_secrets_url: str, vault_token: str, secrets_to_set: list[str] = None
):
    if not all([env(secret) for secret in secrets_to_set]):
        logger.debug(
            "Missing secrets: "
            f"{[secret for secret in secrets_to_set if not env(secret)]}"
        )
        if not vault_token:
            logger.error(" ----- !!!! Vault token missing !!!! ----- ")
        set_vault_secrets(vault_secrets_url, vault_token, secrets_to_set)

    for secret in secrets_to_set:
        if not env(secret):
            logger.error(f"Missing {secret} environment variable.")

    if not all([env(secret) for secret in secrets_to_set]):
        logger.error("Service cannot run with missing secrets. Exiting ...")
        exit()


def build_auto_comment(comment: str, source: str = "") -> str:
    auto_comment_line = "🤖 *[issue-sync]* automated comment 📟\n"
    comment = auto_comment_line + comment
    if source:
        comment = comment.replace(" comment 📟\n", f" comment (from {source}) 📟\n")
    return comment
