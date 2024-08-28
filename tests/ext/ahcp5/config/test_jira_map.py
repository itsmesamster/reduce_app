import pytest
from app.ext.jira_esr.jira_map import EsrLabsAhcp5JiraFieldMap, ClusterMap


@pytest.fixture
def field_map():
    return EsrLabsAhcp5JiraFieldMap()


@pytest.fixture
def cluster_map():
    return ClusterMap()


def test_field_map_defaults(field_map):
    assert field_map.ticket_id == "key"
    assert field_map.url == "self"
    assert field_map.project == "project"
    assert field_map.assignee == "assignee"
    assert field_map.labels == "labels"
    assert field_map.status == "status"
    assert field_map.external_reference == "customfield_10503"
    assert field_map.audi_cluster == "customfield_12600"
    assert field_map.origin == "customfield_12640"


def test_field_map_extras(field_map):
    assert field_map.extras.feedback_to_oem == "customfield_12743"
    assert field_map.extras.feedback_from_oem == "customfield_12742"
    assert field_map.extras.question_to_oem == "customfield_12759"
    assert field_map.extras.answer_from_oem == "customfield_12760"
    assert field_map.extras.cause_of_reject == "customfield_12713"
