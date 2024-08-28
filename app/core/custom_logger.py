import sys
from loguru import logger as loguru_logger


def get_logger():
    loguru_logger.configure(extra={"kpm_id": "", "jira_id": ""})
    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "[{extra[jira_id]}][{extra[kpm_id]}] "
        "- <level>{message}</level>"
    )
    loguru_logger.remove()  # removes existing default logger
    loguru_logger.add(sys.stderr, format=logger_format)
    return loguru_logger


logger = get_logger()
