# project core
from app.core.utils import connection_retry
from app.core.processors.exceptions import APIServerConnectionError
from app.core.jira.exceptions import JiraApiError

# project extension
from app.ext.jira_audi.jira_client import VwAudiJiraClient
from app.ext.jira_audi.jira_map import VwAudiHcp5JiraFieldMap

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.jira_issue_vwaudi import Hcp5VwAudiJiraIssue
from app.service.hcp5.jira2jira.config import (
    J2J_VW_USE_JIRA_SERVER,
    J2J_VWAUDI_JIRA,
)


class Hcp5VwAudiJiraClient(VwAudiJiraClient):
    """Audi HCP5 Cariad/Devstack Jira Client Wrapper around VwAudiJiraClient client."""

    def __init__(
        self,
        server: str,
        user: str,
        token: str,
        field_map: VwAudiHcp5JiraFieldMap = None,
        project_name: str = "",
        project_key: str = "",
        issue_prefix: str = "",
        issue_type: str = "",
        reporters: list[str] = None,
    ):
        super().__init__(
            server=server,
            user=user,
            token=token,
            field_map=field_map,
            project_name=project_name,
            project_key=project_key,
            issue_prefix=issue_prefix,
            issue_type=issue_type,
            reporters=reporters,
        )
        self.jira_issue_type = Hcp5VwAudiJiraIssue
        self.field_map = field_map if field_map else VwAudiHcp5JiraFieldMap()


@connection_retry(times=5)
def j2j_vw_jira_client(
    server: str = J2J_VWAUDI_JIRA.server,
    user: str = J2J_VWAUDI_JIRA.user,
    token: str = J2J_VWAUDI_JIRA.token,
    field_map: dict = None,
    project_name: str = J2J_VWAUDI_JIRA.PROJECT_NAME,
    project_key: str = J2J_VWAUDI_JIRA.PROJECT_KEY,
    issue_prefix: str = J2J_VWAUDI_JIRA.ISSUE_PREFIX,
    reporters: str = J2J_VWAUDI_JIRA.REPORTERS,
) -> Hcp5VwAudiJiraClient:
    """Interact with the Jira server."""
    if not field_map:
        field_map = VwAudiHcp5JiraFieldMap()
    try:
        jira = Hcp5VwAudiJiraClient(
            server=server,
            user=user,
            token=token,
            field_map=field_map,
            project_name=project_name,
            project_key=project_key,
            issue_prefix=issue_prefix,
            reporters=reporters,
        ).connect()
        if not jira:
            raise JiraApiError
        logger.info(
            f"👍👍👍 JIRA server {J2J_VW_USE_JIRA_SERVER} connection successful 👍👍👍"
        )  # noqa: E501
        return jira
    except (JiraApiError, Exception) as ex:
        logger.error(f"Failed to connect to JIRA server {user}@{server}: {ex}")
        raise APIServerConnectionError
