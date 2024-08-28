from app.service.hcp5.jira2jira.config import J2J_ESR_JIRA


MAPPER_BY_ISSUE_TYPE = {
    # TASK
    "Task": {
        "hardcoded": {
            # OK:
            "project": J2J_ESR_JIRA.PROJECT_KEY,  # Project
            "parent": {"key": J2J_ESR_JIRA.PARENT_EPIC},  # Parent
            "customfield_12640": {"value": J2J_ESR_JIRA.ORIGIN},  # Origin
            "customfield_12613": [{"value": "VD"}],  # Audi Domain
            "labels": ["Technical_Clearing"],
            "assignee": {"accountId": J2J_ESR_JIRA.user_id},
        },
        "from_vwjira": {
            # OK:
            "issuetype": "issuetype/name",
            "summary": "summary",
            "description": "description",
            "priority": "priority/name",
        },
        "from_vwjira_property": {
            "customfield_10902": "ui_url",  # External Reference Link
        },
    },
    # INTEGRATION
    "Integration": {
        "hardcoded": {
            # OK:
            "project": J2J_ESR_JIRA.PROJECT_KEY,  # Project
            "customfield_12640": {"value": J2J_ESR_JIRA.ORIGIN},  # Origin
            "customfield_12613": [{"value": "VD"}],  # Audi Domain
            "assignee": {"accountId": J2J_ESR_JIRA.user_id},
        },
        "from_vwjira": {
            # OK:
            "issuetype": "issuetype/name",
            "summary": "summary",
            "description": "description",
            "priority": "priority/name",
        },
        "from_vwjira_property": {
            "customfield_10902": "ui_url",  # External Reference Link
        },
    },
}
