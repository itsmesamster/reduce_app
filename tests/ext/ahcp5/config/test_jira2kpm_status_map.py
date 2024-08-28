from app.service.hcp5.kpm2jira.config.jira2kpm_status_map import JiraToKpmStatuses


def test_get_status():
    jira_to_kpm_statuses = JiraToKpmStatuses()
    assert jira_to_kpm_statuses.get_status("OPEN") == jira_to_kpm_statuses.OPEN
    assert (
        jira_to_kpm_statuses.get_status("INFO_MISSING")
        == jira_to_kpm_statuses.INFO_MISSING
    )
    assert jira_to_kpm_statuses.get_status("REOPENED") == jira_to_kpm_statuses.REOPENED
    assert (
        jira_to_kpm_statuses.get_status("IN_ANALYSIS")
        == jira_to_kpm_statuses.IN_ANALYSIS
    )
    assert (
        jira_to_kpm_statuses.get_status("IN_REVIEW") == jira_to_kpm_statuses.IN_REVIEW
    )
    assert (
        jira_to_kpm_statuses.get_status("IN_PROGRESS")
        == jira_to_kpm_statuses.IN_PROGRESS
    )
    assert jira_to_kpm_statuses.get_status("REJECTED") == jira_to_kpm_statuses.REJECTED


def test_get_status_comment():
    jira_to_kpm_statuses = JiraToKpmStatuses()
    assert jira_to_kpm_statuses.get_status_comment("OPEN") == "Ins System Übernommen"
    assert (
        jira_to_kpm_statuses.get_status_comment("INFO_MISSING") == "Rückfrage gestellt"
    )
    assert (
        jira_to_kpm_statuses.get_status_comment("REOPENED") == "Ticket wiedereröffnet"
    )
    assert (
        jira_to_kpm_statuses.get_status_comment("IN_ANALYSIS")
        == "Mit der Analyse begonnen"
    )
    assert jira_to_kpm_statuses.get_status_comment("IN_REVIEW") == "Fix in Review"
    assert jira_to_kpm_statuses.get_status_comment("IN_PROGRESS") == "Fix in Umsetzung"
    assert jira_to_kpm_statuses.get_status_comment("REJECTED") == "Reject"


def test_get_status_number():
    jira_to_kpm_statuses = JiraToKpmStatuses()
    assert jira_to_kpm_statuses.get_status_number("OPEN") == 0
    assert jira_to_kpm_statuses.get_status_number("INFO_MISSING") == ""
    assert jira_to_kpm_statuses.get_status_number("REOPENED") == 0
    assert jira_to_kpm_statuses.get_status_number("IN_ANALYSIS") == 1
    assert jira_to_kpm_statuses.get_status_number("IN_REVIEW") == 1
    assert jira_to_kpm_statuses.get_status_number("IN_PROGRESS") == 1
    assert jira_to_kpm_statuses.get_status_number("REJECTED") == 4
