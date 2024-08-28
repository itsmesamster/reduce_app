# standard

# external
from jira import JIRA, Issue
from jira.exceptions import JIRAError
import yaml

# project core
from app.core.utils import connection_retry
from app.core.processors.exceptions import APIServerConnectionError
from app.core.jira.exceptions import (
    JiraApiError,
    MultipleJiraIssuesFound,
    JQLorAppConfigQueryError,
)

# project extension
from app.ext.jira_esr.jira_client import ESRLabsJiraClient
from app.ext.jira_esr.jira_map import EsrLabsAhcp5JiraFieldMap

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.jira_issue_esr4vw import EsrIssueForVwJiraSync
from app.service.hcp5.jira2jira.config import (
    J2J_ESR_USE_JIRA_SERVER,
    J2J_ESR_JIRA,
)


class ESRLabsJiraClientForVwJiraSync(ESRLabsJiraClient):
    """Wrapper around ESRLabsJiraClient client."""

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
        self.jira_issue_type = EsrIssueForVwJiraSync
        self.field_map = field_map if field_map else EsrLabsAhcp5JiraFieldMap()

    def add_ticket(self, jira_issue: EsrIssueForVwJiraSync) -> Issue | None:
        """Post a new Jira issue to Jira API server"""
        fields: dict = jira_issue.fields
        vw_id = jira_issue.external_reference
        self.logger.info(f"adding VW [{vw_id}] to JIRA ...", vw_id=vw_id)
        if not vw_id:
            self.logger.error(
                "VW/Audi/Cariad Jira ID missing. Won't process "
                "ticket without External Reference ... "
            )
            return
        if not fields:
            try:
                self.logger.error(
                    'EsrIssueForVwJiraSync is missing ".fields" to be used '
                    "for new Jira issue creation",
                    vw_id=vw_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "vw_id" and "esr_id" extras'
                )
                self.logger.error(
                    'EsrIssueForVwJiraSync is missing ".fields" to be used '
                    "for new Jira issue creation"
                )
            return
        try:
            # FIXME: loguru inconsistent format error:
            # ValueError: unmatched '{' in format spec
            self.logger.debug(
                f"Jira Issue {vw_id} .fields: \n{yaml.safe_dump(fields)}",
                vw_id=vw_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom format error when "
                f'adding "vw_id" and "esr_id" extras'
            )
            self.logger.debug(f"Jira Issue {vw_id} .fields: \n{yaml.safe_dump(fields)}")

        self.logger.debug(
            f"Issue Fields keys present (mapped from VW): {[k for k in fields.keys()]}"
        )

        # actual posting the new Jira issue to Jira API server
        jira_client: JIRA = self._session()
        jira_response: Issue = jira_client.create_issue(fields)
        if jira_response:
            self.logger.debug(f'Jira "create_issue" server response: {jira_response}')
            return jira_response
        else:
            self.logger.error(f"Failed to create Jira issue: {jira_issue}")

    def issues_relevant_data(self, issues: list):
        issues_new_list = []
        for issue in issues:
            issue: EsrIssueForVwJiraSync = issue
            issues_new_list.append(
                f"{issue.jira_id}: "
                f"Project [{issue.project}], "
                f"Type [{issue.issue_type}], "
                f"Origin [{issue.origin}], "
                f"Reporter [{issue.reporter}]. "
            )
        if len(issues_new_list) == 1:
            return issues_new_list[0]
        return issues_new_list

    def issue_by_ext_id(self, ext_id: str) -> EsrIssueForVwJiraSync | None:
        """Get Jira issue by External Reference ID"""
        if "HCP5- " not in ext_id and "HCP5-" in ext_id:
            ext_id = ext_id.replace("HCP5-", "HCP5- ")

        external_ref_jql = f'"External Reference" ~ "{ext_id}"'
        try:
            jql = f"{self.base_jql} AND {external_ref_jql}"

            single_issue: list = self.query(jql)  # should be a list of one item
            if len(single_issue) > 1:
                msg = (
                    f" ❌ ❌ Same External Reference for multiple Jira issues, "
                    f"based on the JQL: {jql} ❌ ❌ "
                )
                self.logger.error(msg)
                raise MultipleJiraIssuesFound(msg)
            elif not single_issue:
                msg = f"No issue found in Jira, based on the JQL: {jql}"
                self.logger.warning(msg, vw_id=ext_id.strip(" "))
                iss_by_ext_ref: list = self.query(external_ref_jql)
                if iss_by_ext_ref:
                    external_ref_issues = self.issues_relevant_data(iss_by_ext_ref)
                    msg = f"{external_ref_issues} ≠ JQL: " f"{jql.replace('\"', '')} "
                    self.logger.warning(msg, vw_id=ext_id.strip(" "))
                    raise JQLorAppConfigQueryError(msg)
                return
        except (JIRAError, JQLorAppConfigQueryError, MultipleJiraIssuesFound) as j_e:
            msg = f"Failed Jira query request: '{jql}' -> {j_e.status_code}: {j_e.text}"
            self.logger.error(msg)
            raise j_e
        return single_issue[0]

    def issue_by_ahcp5_id_jql(self, ahcp5_id: str) -> EsrIssueForVwJiraSync | None:
        jira_key_split = ahcp5_id.split("-")
        jira_key_prefix, jira_key_number = "", ""
        if len(jira_key_split) == 2:
            jira_key_prefix = jira_key_split[0]
            jira_key_number = int(jira_key_split[1])
        if jira_key_prefix == self.issue_prefix and isinstance(jira_key_number, int):
            jql = f'{self.base_jql} AND key = "{ahcp5_id}"'
            self.logger.debug(f"JQL: {jql}")
            single_issue = self.query(jql)
            if len(single_issue) > 1:
                msg = (
                    f"Same Jira Issue Key [{ahcp5_id}]for multiple Jira issues, "
                    f"based on the JQL: {jql}"
                )
                try:
                    self.logger.error(msg, esr_id=ahcp5_id)
                except (ValueError, KeyError, IndexError) as e:
                    self.logger.warning(
                        f"{e} - loguru lib inconsistent custom "
                        f'format error when adding "esr_id" extra'
                    )
                    self.logger.error(msg)
                # raise MultipleJiraIssuesFound(msg)
                return
            elif not single_issue:
                msg = f"No issue found in Jira, based on the JQL: {jql}"
                try:
                    self.logger.error(msg, esr_id=ahcp5_id)
                except (ValueError, KeyError, IndexError) as e:
                    self.logger.warning(
                        f"{e} - loguru lib inconsistent custom "
                        f'format error when adding "esr_id" extra'
                    )
                    self.logger.error(msg)
                # raise IssueNotFound(msg)
                return
            return single_issue[0]

    def get_esr_id_by_vw_id(self, vw_id: str) -> str:
        jira_issue: EsrIssueForVwJiraSync = self.issue_by_ext_id(vw_id)
        if jira_issue:
            return jira_issue.esr_id

    def get_vw_id_by_esr_id(self, esr_id: str) -> str:
        jira_issue: EsrIssueForVwJiraSync = self.issue(esr_id)
        if jira_issue:
            return jira_issue.vw_id

    def ticket_already_present(
        self, *, vw_id: str = "", esr_id: str = ""
    ) -> EsrIssueForVwJiraSync | None:
        # FIXME: improve 2 kwargs error logic
        if vw_id and esr_id:
            self.logger.error(
                "Please provide only one of the "
                f"2 possible arguments: {vw_id=} / {esr_id=} "
            )
            return
        try:
            self.logger.debug(
                "Checking if ticket already present in JIRA ... ",
                vw_id=vw_id,
                esr_id=esr_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom format "
                f'error when adding "vw_id" and "esr_id" extras'
            )
            self.logger.debug(
                f"Checking if ticket {vw_id=} {esr_id=} already present in JIRA ... "
            )
        if vw_id and (jira_issue := self.issue_by_ext_id(vw_id)):
            try:
                self.logger.warning(
                    f"VW Jira ID already in Jira: {jira_issue}",
                    vw_id=vw_id,
                    esr_id=esr_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "vw_id" and "esr_id" extras'
                )
                self.logger.warning(f"VW Jira ID already in Jira: {jira_issue}")
            return jira_issue
        if esr_id and (jira_issue := self.issue(esr_id)):
            try:
                self.logger.warning(
                    f"JIRA ID already exists in Jira: {jira_issue}",
                    vw_id=vw_id,
                    esr_id=esr_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "vw_id" and "esr_id" extras'
                )
                self.logger.warning(f"JIRA ID already exists in Jira: {jira_issue}")
            return jira_issue


@connection_retry(times=5)
def j2j_esr_jira_client(
    server: str = J2J_ESR_JIRA.server,
    email: str = J2J_ESR_JIRA.email,
    token: str = J2J_ESR_JIRA.token,
    field_map: dict = None,
    project_name: str = J2J_ESR_JIRA.PROJECT_NAME,
    project_key: str = J2J_ESR_JIRA.PROJECT_KEY,
    issue_prefix: str = J2J_ESR_JIRA.ISSUE_PREFIX,
    issue_type: str = J2J_ESR_JIRA.ISSUE_TYPE,
    reporters: str = J2J_ESR_JIRA.REPORTERS,
    origin: str = J2J_ESR_JIRA.ORIGIN,
) -> ESRLabsJiraClientForVwJiraSync:
    """Interact with the Jira server."""
    if not field_map:
        field_map = EsrLabsAhcp5JiraFieldMap()
    try:
        jira = ESRLabsJiraClientForVwJiraSync(
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
        ).connect()
        if not jira:
            raise JiraApiError
        logger.info(
            f"👍👍👍 JIRA server {J2J_ESR_USE_JIRA_SERVER} connection successful 👍👍👍"
        )  # noqa: E501
        return jira
    except (JiraApiError, Exception) as ex:
        logger.error(f"Failed to connect to JIRA server {email}@{server}: {ex}")
        raise APIServerConnectionError
