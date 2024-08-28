# standard


# project core
from app.core.jira.jira_client import JiraClientCore

# project extension - jira_audi
from app.ext.jira_audi.jira_issue import VwAudiJiraIssue
from app.ext.jira_audi.jira_map import VwAudiHcp5JiraFieldMap


class VwAudiJiraClient(JiraClientCore):
    """VW/AUDI/CARIAD Devstack Jira Client Wrapper around JiraClientCore client."""

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
            email=user,
            token=token,
            field_map=field_map,
            project_name=project_name,
            project_key=project_key,
            issue_prefix=issue_prefix,
            issue_type=issue_type,
            reporters=reporters,
        )
        self.jira_issue_type = VwAudiJiraIssue
        self.field_map = field_map if field_map else VwAudiHcp5JiraFieldMap()

    def issue_by_hcp5_id_jql(self, hcp5_id: str) -> VwAudiJiraIssue | None:
        jira_key_split = hcp5_id.split("-")
        jira_key_prefix, jira_key_number = "", ""
        if len(jira_key_split) == 2:
            jira_key_prefix = jira_key_split[0]
            jira_key_number = int(jira_key_split[1])
        if jira_key_prefix == self.issue_prefix and isinstance(jira_key_number, int):
            jql = f'{self.base_jql} AND key = "{hcp5_id}"'
            self.logger.debug(f"JQL: {jql}")
            single_issue = self.query(jql)
            if len(single_issue) > 1:
                msg = (
                    f"Same Jira Issue Key [{hcp5_id}]for multiple Jira issues, "
                    f"based on the JQL: {jql}"
                )
                try:
                    self.logger.error(msg, jira_id=hcp5_id)
                except (ValueError, KeyError, IndexError) as e:
                    self.logger.warning(
                        f"{e} - loguru lib inconsistent custom "
                        f'format error when adding "jira_id" extra'
                    )
                    self.logger.error(msg)
                # raise MultipleJiraIssuesFound(msg)
                return
            elif not single_issue:
                msg = f"No issue found in Jira, based on the JQL: {jql}"
                try:
                    self.logger.error(msg, jira_id=hcp5_id)
                except (ValueError, KeyError, IndexError) as e:
                    self.logger.warning(
                        f"{e} - loguru lib inconsistent custom "
                        f'format error when adding "jira_id" extra'
                    )
                    self.logger.error(msg)
                # raise IssueNotFound(msg)
                return
            return single_issue[0]
