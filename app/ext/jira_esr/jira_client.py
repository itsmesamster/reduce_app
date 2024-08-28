# project core
from app.core.jira.jira_client import JiraClientCore


# project extension
from app.ext.jira_esr.jira_issue import EsrLabsJiraIssue
from app.ext.jira_esr.jira_map import EsrLabsAhcp5JiraFieldMap


class ESRLabsJiraClient(JiraClientCore):
    """Wrapper around JiraClientCore client."""

    def __init__(
        self,
        server: str,
        email: str,
        token: str,
        field_map: EsrLabsAhcp5JiraFieldMap = None,
        project_name: str = "",
        project_key: str = "",
        issue_prefix: str = "",
        issue_type: str = "",
        reporters: list[str] = None,
        origin: list[str] = None,
    ):
        super().__init__(
            server=server,
            email=email,
            token=token,
            field_map=field_map,
            project_name=project_name,
            project_key=project_key,
            issue_prefix=issue_prefix,
            issue_type=issue_type,
            reporters=reporters,
            origin=origin,
        )
        self.jira_issue_type = EsrLabsJiraIssue
        self.field_map = field_map if field_map else EsrLabsAhcp5JiraFieldMap()
