from os import getenv as env


from app.service.hcp5.kpm2jira.config import SECRETS_TO_SET
from tests.ext.ahcp5.mocks.mocked_config import SECRETS_TO_MOCK


def test_env_vars():
    for secret in SECRETS_TO_SET + SECRETS_TO_MOCK:
        assert env(secret) == "mocked_env_var_for_testing"
