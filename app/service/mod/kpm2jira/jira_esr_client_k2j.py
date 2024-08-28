# standard

# external
from jira import JIRA, Issue
from jira.exceptions import JIRAError
import yaml

# project core
from app.core.utils import connection_retry, logger
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
from app.service.mod.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync
from app.service.mod.kpm2jira.config import (
    JIRA_ISSUE_PREFIX,
    JIRA_PROJECT,
    JIRA_REPORTERS,
    JIRA_ORIGIN,
    JIRA_PROJECT_KEY,
    JIRA_ISSUE_TYPE,
    USE_JIRA_SERVER,
    JIRA_SERVER_URL,
    JIRA_EMAIL,
    JIRA_TOKEN,
)


class ESRLabsJiraClientForKpmSync(ESRLabsJiraClient):
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
        self.jira_issue_type = EsrLabsJiraIssueForKpmSync
        self.field_map = field_map if field_map else EsrLabsAhcp5JiraFieldMap()

    def add_ticket(self, jira_issue: EsrLabsJiraIssueForKpmSync) -> Issue | None:
        """Post a new Jira issue to Jira API server"""
        fields: dict = jira_issue.fields
        jira_id, kpm_id = jira_issue.jira_id, jira_issue.kpm_id
        self.logger.info(f"adding KPM [{kpm_id}] to JIRA ...", kpm_id=kpm_id)
        if not kpm_id:
            self.logger.error(
                "KPM ID missing. Won't process ticket without External Reference ... "
            )
            return
        if not fields:
            try:
                self.logger.error(
                    'EsrLabsJiraIssueForKpmSync is missing ".fields" to be used '
                    "for new Jira issue creation",
                    kpm_id=kpm_id,
                    jira_id=jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "kpm_id" and "jira_id" extras'
                )
                self.logger.error(
                    'EsrLabsJiraIssueForKpmSync is missing ".fields" to be used '
                    "for new Jira issue creation"
                )
            return
        try:
            # FIXME: loguru inconsistent format error:
            # ValueError: unmatched '{' in format spec
            self.logger.debug(
                f"Jira Issue {jira_id} .fields: \n{yaml.safe_dump(fields)}",
                kpm_id=kpm_id,
                jira_id=jira_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom format error when "
                f'adding "kpm_id" and "jira_id" extras'
            )
            self.logger.debug(
                f"Jira Issue {jira_id} .fields: \n{yaml.safe_dump(fields)}"
            )

        self.logger.debug(
            f"Issue Fields keys present (mapped from KPM): {[k for k in fields.keys()]}"
        )

        # actual posting the new Jira issue to Jira API server
        jira_client: JIRA = self._session()
        jira_response: Issue = jira_client.create_issue(fields)
        if jira_response:
            self.logger.debug(
                f'Jira "create_issue" server response: {jira_response}', kpm_id=kpm_id
            )
            return jira_response
        else:
            self.logger.error(
                f"Failed to create Jira issue: {jira_issue}", kpm_id=kpm_id
            )

    def issues_relevant_data(self, issues: list):
        issues_new_list = []
        for issue in issues:
            issue: EsrLabsJiraIssueForKpmSync = issue
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

    def issue_by_kpm_id(self, kpm_id: str) -> EsrLabsJiraIssueForKpmSync | None:
        try:
            if not kpm_id.isdigit():
                return

            external_ref_jql = f'"External Reference" ~ {kpm_id}'
            jql = f"{self.base_jql} AND {external_ref_jql}"

            single_issue: list = self.query(jql)  # should be a list of one item
            if len(single_issue) > 1:
                msg = (
                    f" ❌ ❌ Same External Reference for multiple Jira issues, "
                    f"based on the JQL: {jql} ❌ ❌ "
                )
                self.logger.error(msg, kpm_id=kpm_id)
                raise MultipleJiraIssuesFound(msg)

            elif not single_issue:
                msg = f"No issue found in Jira, based on the JQL: {jql}"
                self.logger.warning(msg, kpm_id=kpm_id)
                iss_by_ext_ref: list = self.query(
                    f'PROJECT = "{self.project_key}" ' f"AND {external_ref_jql}"
                )
                if iss_by_ext_ref:
                    external_ref_issues = self.issues_relevant_data(iss_by_ext_ref)
                    msg = f"{external_ref_issues} ≠ JQL: " f"{jql.replace('\"', '')} "
                    self.logger.warning(msg, kpm_id=kpm_id)
                    raise JQLorAppConfigQueryError(msg)
                return
        except JIRAError as e:
            msg = f"Failed Jira query request: '{jql}' -> {e.status_code}: {e.text}"
            self.logger.error(msg)
            return
        return single_issue[0]

    def issue_by_ahcp5_id_jql(self, ahcp5_id: str) -> EsrLabsJiraIssueForKpmSync | None:
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
                    self.logger.error(msg, jira_id=ahcp5_id)
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
                    self.logger.error(msg, jira_id=ahcp5_id)
                except (ValueError, KeyError, IndexError) as e:
                    self.logger.warning(
                        f"{e} - loguru lib inconsistent custom "
                        f'format error when adding "jira_id" extra'
                    )
                    self.logger.error(msg)
                # raise IssueNotFound(msg)
                return
            return single_issue[0]

    def get_jira_id_by_kpm_id(self, kpm_id: str) -> str:
        jira_issue: EsrLabsJiraIssueForKpmSync = self.issue_by_kpm_id(kpm_id)
        if jira_issue:
            return jira_issue.jira_id

    def get_kpm_id_by_jira_id(self, jira_id: str) -> str:
        jira_issue: EsrLabsJiraIssueForKpmSync = self.issue(jira_id)
        if jira_issue:
            return jira_issue.kpm_id

    def ticket_already_present(
        self, *, kpm_id: str = "", jira_id: str = ""
    ) -> EsrLabsJiraIssueForKpmSync | None:
        # FIXME: improve 2 kwargs error logic
        if kpm_id and jira_id:
            self.logger.error(
                "Please provide only one of the "
                f"2 possible arguments: {kpm_id=} / {jira_id=} "
            )
            return
        try:
            self.logger.debug(
                "Checking if ticket already present in JIRA ... ",
                kpm_id=kpm_id,
                jira_id=jira_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom format "
                f'error when adding "kpm_id" and "jira_id" extras'
            )
            self.logger.debug(
                f"Checking if ticket {kpm_id=} {jira_id=} already present in JIRA ... "
            )
        if kpm_id and (jira_issue := self.issue_by_kpm_id(kpm_id)):
            try:
                self.logger.warning(
                    f"KPM ID already in Jira: {jira_issue}",
                    kpm_id=kpm_id,
                    jira_id=jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "kpm_id" and "jira_id" extras'
                )
                self.logger.warning(f"KPM ID already in Jira: {jira_issue}")
            return jira_issue
        if jira_id and (jira_issue := self.issue(jira_id)):
            try:
                self.logger.warning(
                    f"JIRA ID already exists in Jira: {jira_issue}",
                    kpm_id=kpm_id,
                    jira_id=jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "kpm_id" and "jira_id" extras'
                )
                self.logger.warning(f"JIRA ID already exists in Jira: {jira_issue}")
            return jira_issue


@connection_retry(times=5)
def esr_jira_client(
    server: str = JIRA_SERVER_URL,
    email: str = JIRA_EMAIL,
    token: str = JIRA_TOKEN,
    field_map: dict = None,
    project_name: str = JIRA_PROJECT,
    project_key: str = JIRA_PROJECT_KEY,
    issue_prefix: str = JIRA_ISSUE_PREFIX,
    issue_type: str = JIRA_ISSUE_TYPE,
    reporters: str = JIRA_REPORTERS,
    origin: str = JIRA_ORIGIN,
) -> ESRLabsJiraClientForKpmSync:
    """Interact with the Jira server."""
    if not field_map:
        field_map = EsrLabsAhcp5JiraFieldMap()
    try:
        jira = ESRLabsJiraClientForKpmSync(
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
            f"👍👍👍 JIRA server {USE_JIRA_SERVER} connection successful 👍👍👍"
        )  # noqa: E501
        return jira
    except (JiraApiError, Exception) as ex:
        logger.error(f"Failed to connect to JIRA server {email}@{server}: {ex}")
        raise APIServerConnectionError
