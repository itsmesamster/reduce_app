from pathlib import Path


# TODO: convert paths to work also on Windows
APP_CACHE_DIR = "app/__cache"
Path(APP_CACHE_DIR).mkdir(parents=True, exist_ok=True)

APP_CACHE_HOLD_DAYS = 4
ATTACHMENTS_VALIDATION_SIZE_TOLERANCE = 2  # in bytes
