from app.core.jira.jira_map import JiraFieldsMapCore


def test_JiraFieldsMapCore():
    # Test with a valid JiraFieldsMapCore object
    fields = JiraFieldsMapCore(
        ticket_id="ABC-123",
        url="https://example.com",
        project="PROJECT",
        assignee="user@example.com",
        labels=["label1", "label2"],
        status="open",
        components=["component1", "component2"],
    )
    assert fields.ticket_id == "ABC-123"
    assert fields.url == "https://example.com"
    assert fields.project == "PROJECT"
    assert fields.assignee == "user@example.com"
    assert fields.labels == ["label1", "label2"]
    assert fields.status == "open"
    assert fields.components == ["component1", "component2"]
