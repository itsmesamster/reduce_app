# standard
from enum import Enum
from os import environ


class ENV(Enum):
    DEV = "development"
    TEST = "test"


USE_KPM_SERVER = ENV.TEST
USE_JIRA_SERVER = ENV.TEST
POST_BACK_TO_KPM = False


SECRETS_TO_MOCK = [
    "KPM_USER_ID",
    "KPM_CERT",
    "KPM_CERT_FILE_PATH",
    "JIRA_EMAIL",
    "JIRA_TOKEN",
    "JIRA_ACCOUNT_ID",
    "VAULT_URL",
    "VAULT_TOKEN",
]
for secret in SECRETS_TO_MOCK:
    environ[secret] = "mocked_env_var_for_testing"
