import pytest
from unittest.mock import patch


@pytest.fixture
def kpm_jira_ids():
    return b"12345<-->6789"


@pytest.fixture
def kpm_issue_mock():
    with patch(
        "app.ext.ahcp5.kpm_audi.soap_responses.development_problem_data_response.DevelopmentProblemDataResponse"
    ) as MockClass:
        instance = MockClass.return_value
        yield instance


@pytest.fixture
def kpm_client_mock(kpm_issue_mock):
    with patch("app.ext.ahcp5.kpm_audi.kpm_client.KPMClient") as MockClass:
        instance = MockClass.return_value
        yield instance


@pytest.fixture
def jira_issue_mock():
    with patch("app.ext.ahcp5.jira_esr.jira_issue.JiraIssue") as MockClass:
        instance = MockClass.return_value
        yield instance


@pytest.fixture
def jira_client_mock(jira_issue_mock):
    with patch("app.ext.ahcp5.jira_esr.jira_client.JiraClient") as MockClass:
        instance = MockClass.return_value
        yield instance
