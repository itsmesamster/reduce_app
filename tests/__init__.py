# standard
from unittest import mock

# 3rd party
import pytest

# project
from tests.ext.ahcp5.mocks import mocked_config

# import the mocked config before the real one.
from app.service.hcp5.kpm2jira import config


@pytest.fixture(scope="session", autouse=True)
def auto_mock_config():
    with mock.patch.object(config, new=mocked_config) as _fixture:
        yield _fixture
