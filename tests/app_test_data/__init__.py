# 3rd party
import yaml
import json


TEST_DATA_DIR = "tests/app_test_data"


def read_test_data(relative_filepath: str, base_dir: str = TEST_DATA_DIR) -> dict:
    with open(f"{base_dir}/{relative_filepath}", "r") as f:
        file_extension = relative_filepath.split(".")[-1]
        if file_extension in ("yaml", "yml"):
            return yaml.safe_load(f)
        if file_extension in ("json"):
            return json.load(f)


JIRA_TICKET = read_test_data("jira/ticket.yml")
