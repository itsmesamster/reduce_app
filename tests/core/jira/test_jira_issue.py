# standard
import pytest

# project core
from app.core.jira.jira_issue import JiraIssueCore
from app.core.jira.jira_map import JiraFieldsMapCore


MOCKED_JIRA_SERVER = "https://www.mocked-jira-domain.com"


@pytest.fixture
def jira_issue_core():
    jira_map = JiraFieldsMapCore()
    jira_server = MOCKED_JIRA_SERVER
    key = "TEST-1"
    raw_issue = {
        "id": "10000",
        "key": key,
        "self": f"{jira_server}/browse/{key}",
        "fields": {
            "issuetype": {"name": "Bug"},
            "project": {"key": "TEST"},
            "reporter": {"displayName": "John Doe"},
            "status": {"name": "In Progress"},
            "summary": "Test Issue",
            "description": "Test Description",
            "fixVersions": [{"name": "Version 1.0"}],
            "components": [{"name": "Component A"}],
            "attachment": [
                {
                    "filename": "test.txt",
                    "id": "12345",
                    "created": "2022-01-01T12:00:00",
                    "mimeTypee": "text/plain",
                    "size": 100,
                }
            ],
        },
    }
    return JiraIssueCore(raw_issue, jira_map)


def test_jira_issue_core_url(jira_issue_core):
    assert jira_issue_core.url == f"{MOCKED_JIRA_SERVER}/browse/TEST-1"


def test_jira_issue_core_id(jira_issue_core):
    assert jira_issue_core._id == "10000"


def test_jira_issue_core_issue_type(jira_issue_core):
    assert jira_issue_core.issue_type == "Bug"


def test_jira_issue_core_project(jira_issue_core):
    assert jira_issue_core.project == "TEST"


def test_jira_issue_core_reporter(jira_issue_core):
    assert jira_issue_core.reporter == "John Doe"


def test_jira_issue_core_status(jira_issue_core):
    assert jira_issue_core.status == "In Progress"


def test_jira_issue_core_summary(jira_issue_core):
    assert jira_issue_core.summary == "Test Issue"


def test_jira_issue_core_description(jira_issue_core):
    assert jira_issue_core.description == "Test Description"


def test_jira_issue_core_fix_versions(jira_issue_core):
    assert jira_issue_core.fix_versions == ["Version 1.0"]


def test_jira_issue_core_components(jira_issue_core):
    assert jira_issue_core.components == ["Component A"]


def test_jira_issue_core_attachments(jira_issue_core):
    attachments = jira_issue_core.attachments
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "test.txt"
    assert attachments[0]["id"] == "12345"
    assert attachments[0]["created"] == "2022-01-01T12:00:00"
    assert attachments[0]["mimeTypee"] == "text/plain"
    assert attachments[0]["size"] == 100
    assert attachments[0]["vol"] == "100 B"


def test_jira_issue_core_output_ok(jira_issue_core):
    assert jira_issue_core.output_ok()


@pytest.mark.parametrize(
    "field_name,new_value,expected_value",
    [
        ("summary", "New Summary", "New Summary"),
        ("description", "New Description", "New Description"),
    ],
)
def test_jira_issue_core_set_summary_and_description(
    jira_issue_core, field_name, new_value, expected_value
):
    setattr(jira_issue_core, field_name, new_value)
    assert getattr(jira_issue_core, field_name) == expected_value


@pytest.mark.parametrize(
    "field_name,new_value,expected_value",
    [
        ("components", ["Component C"], ["Component C"]),
    ],
)
def test_jira_issue_core_set_components_list(
    jira_issue_core, field_name, new_value, expected_value
):
    setattr(jira_issue_core, field_name, new_value)
    assert jira_issue_core.components == expected_value


@pytest.mark.parametrize(
    "field_name,new_value,expected_value",
    [
        ("components", "Component D", ["Component D"]),
    ],
)
def test_jira_issue_core_set_components_str(
    jira_issue_core, field_name, new_value, expected_value
):
    setattr(jira_issue_core, field_name, new_value)
    assert jira_issue_core.components == expected_value


@pytest.mark.parametrize(
    "field_name,new_value,expected_value",
    [
        ("components", ["Component E"], ["Component E"]),
    ],
)
def test_jira_issue_core_set_components_str_list(
    jira_issue_core, field_name, new_value, expected_value
):
    setattr(jira_issue_core, field_name, new_value)
    assert jira_issue_core.components == expected_value
