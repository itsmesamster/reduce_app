# standard
from copy import deepcopy
from io import BytesIO
from datetime import datetime, timedelta
from requests.exceptions import ChunkedEncodingError as DownloadFailed

# external
from jira import JIRA, Comment, Issue, User
from jira.resources import Attachment, Version
from jira.exceptions import JIRAError
import yaml

# project core
from app.core.custom_logger import logger
from app.core.jira.jira_issue import JiraIssue, JiraIssueCore
from app.core.processors.exceptions import APIServerConnectionError
from app.core.utils import (
    connection_retry,
    performance_check,
    timed_cache,
    names_are_equal,
    build_auto_comment,
)
from app.core.jira.jira_map import JiraFieldsMapCore
from app.core.jira.jira_utils import process_jira_error_msg
from app.core.jira.exceptions import (
    JiraApiError,
    JiraConnectError,
    JiraMissingConnectionError,
    JiraRequestError,
)


class JiraClientCore:
    """Wrapper around jira.JIRA client to interact with the Jira server."""

    def __init__(
        self,
        server: str,
        email: str,
        token: str,
        field_map: JiraFieldsMapCore = None,
        project_name: str = "",
        project_key: str = "",
        issue_prefix: str = "",
        issue_type: str = "",
        reporters: list[str] = None,
        origin: list[str] = None,
    ):
        self.jira_issue_type = JiraIssueCore
        self.logger = logger
        self.__server = server
        self.__email = email
        self.__token = token
        self.field_map = field_map if field_map else JiraFieldsMapCore()
        self._client = None
        self.__base_jql = ""
        self.__available_versions: dict = {}
        self.project_name = project_name
        self.project_key = project_key
        self.issue_prefix = issue_prefix
        self.issue_type = issue_type
        self.reporters = reporters if reporters else []
        self.origin = origin if origin else []

    def connect(self) -> "JiraClientCore":
        """Connect and authenticate to a Jira server."""
        if not all([self.__server, self.__email, self.__token]):
            token_ok = "ok" if self.__token else "missing"
            raise JiraConnectError(
                f"Please provide server [{self.__server}], "
                f"email address [{self.__email}] "
                f"and token [{token_ok}]."
            )
        try:
            self.logger.info(
                f"Connecting Jira client to {self.__email}@{self.__server} ... "
            )
            self._client = JIRA(
                server=self.__server, basic_auth=(self.__email, self.__token)
            )
            return self
        except JIRAError as j_e:
            error_message = f"{j_e.status_code}: {j_e.text}"
            self.logger.error(
                f"Failed to connect to Jira server: {self.__email}@{self.__server}. "
                # f"-> {error_message}"
            )
            raise JiraConnectError(error_message) from j_e

    def _session(self) -> JIRA:
        """Get a connected JIRA client or raise `JiraMissingConnectionError`."""
        if self._client:
            return self._client
        else:
            self.logger.error("Jira client not connected. Please connect first.")
            raise JiraMissingConnectionError

    def __repr__(self):
        self_name = f"{self.__class__.__name__} at {hex(id(self))}"
        if self._session() and self.__server and self.__email:
            return f"{self.__email}@{self.__server} ({self_name})"
        return self_name

    @property
    def base_jql(self):
        if not self.__base_jql:
            base_jql = ""
            if self.project_name:
                base_jql += f'AND PROJECT = "{self.project_name}" '
            if self.issue_type:
                base_jql += f"AND issuetype in {self.issue_type} "
            if self.reporters:
                base_jql += f"AND reporter in {self.reporters} "
            if self.origin:
                base_jql += f'AND "Origin" in ("{self.origin}") '
            self.__base_jql = base_jql.strip("AND").strip()
        return self.__base_jql

    def issue(self, jira_id: str) -> JiraIssue | None:
        """Get an issue Resource from the server."""
        try:
            self.logger.info(f"Request Jira issue: {jira_id} from {self.__server}.")
            issue = self._session().issue(jira_id)
            return self.jira_issue_type(issue.raw)
        except JIRAError as j_e:
            error_message = f"{j_e.status_code}: {j_e.text}"
            self.logger.error(
                f"Failed to request Jira issue: {jira_id} -> {error_message}"
            )
            raise JiraRequestError(error_message) from j_e

    def _run_query(self, jql, start_at) -> tuple[list[JiraIssue], int]:
        try:
            self.logger.debug(
                f"Request Jira issues starting from issue index: {start_at}."
            )
            result = self._client.search_issues(
                jql_str=jql, json_result=True, startAt=start_at
            )
            issues = result.get("issues", [])
            issues_count = len(issues)
            self.logger.debug(f"Found {issues_count} issues.")
            return (issues, issues_count)
        except JIRAError as j_e:
            error_message = f"{j_e.status_code}: {j_e.text}"
            error_message = process_jira_error_msg(error_message)
            self.logger.error(
                f"Failed to request Jira query: '{jql}' -> {error_message}"
            )
            raise JiraRequestError(error_message) from j_e

    def query(self, jql: str) -> list[JiraIssue]:
        """Get all|max issues for the provided query."""
        start_at = 0
        all_issues = []
        self.logger.info(f"Query Jira issues: '{jql}'.")
        while True:
            issues, issues_count = self._run_query(jql, start_at)
            all_issues.extend([self.jira_issue_type(issue) for issue in issues])
            if issues_count >= 0 and issues_count < 50:
                self.logger.debug(
                    f"Found {len(all_issues)} Jira issues for query "
                    f"in Jira server: {self.__server} . JQL:"
                    f"\n{jql}"
                )
                return all_issues
            if issues_count == 50:
                start_at += 50
            else:
                error_message = (
                    f"Invalid length of returned issues: {issues_count}. "
                    "Must be between 0 and 50."
                )
                self.logger.error(error_message)
                raise JiraRequestError(error_message)

    @timed_cache
    def cached_query(self, jql: str) -> list[JiraIssue]:
        """JQL query that will keep the results in cache for an hour"""
        return self.query(jql)

    def beautify_allowed_values(self, allowed_vals: list[dict]) -> list[dict]:
        allowed: list[dict] = []
        for av in allowed_vals:
            value = av.get("value")
            name = av.get("name")
            if value and name:
                self.logger.warning(f"!!! Allowed values has both value and name: {av}")
            new_dict = {"value": value or name or ""}
            if description := av.get("description", ""):
                new_dict["description"] = description
            allowed.append(new_dict)
        return allowed

    @performance_check
    def get_meta_for_project_fields(
        self,
        project_key: str = None,
        issue_type_name: str = None,
        expand: str = "projects.issuetypes.fields",
        data: tuple = ("name", "required", "allowedValues"),
    ) -> dict:
        """
        List the required fields for creating a new issue in Jira API
        """
        if not project_key:
            project_key = self.project_key
        # /rest/api/latest/issue/createmeta
        # ?projectKeys=AHCP5&issuetypeNames=Task&expand=projects.issuetypes.fields
        jira_client: JIRA = self._session()
        meta = jira_client.createmeta(
            project_key,
            issuetypeNames=issue_type_name,
            expand=expand,
        )
        if not meta:
            self.logger.error(f"No meta found for Jira Project {project_key}")
            return

        projects_list = meta.get("projects", [])
        if not projects_list:
            self.logger.error(f"No projects found for Jira Project {project_key}")
            return
        elif len(projects_list) > 1:
            self.logger.error(f"More than one project found for Project {project_key}")
            return

        project: dict = projects_list[0]
        issue_types_list = project.get("issuetypes", [])
        if not issue_types_list:
            self.logger.error(f"No issue types found for Project {project_key}")
            return
        if issue_type_name:
            issue_types = [
                it for it in issue_types_list if it.get("name", "") == issue_type_name
            ]
            issue_type = issue_types[0]
        else:
            issue_type: dict = issue_types_list[0]
            issue_name = issue_type.get("name", "")
            self.logger.warning(
                "No issue type name selected to check fields metadata. "
                "More than one issue type found. Using the first one -> "
                f"{issue_name} for Project {project_key}. "
                "--> INFO: All issue types should have same allowed "
                "values/options for same field name, so this is fine."
            )

        fields: dict = {}
        for field_key, value_dict in issue_type.get("fields", {}).items():
            if not isinstance(value_dict, dict):
                continue
            field_details: dict = deepcopy(value_dict)

            for k in value_dict.keys():
                if k not in data:
                    field_details.pop(k)

            if "allowedValues" in field_details.keys():
                allow_vals: list[dict] = field_details.pop("allowedValues")
                field_details["values_allowed"] = self.beautify_allowed_values(
                    allow_vals
                )

            fields[field_key] = field_details
        return fields

    @timed_cache
    def get_field_metadata(
        self, field_key: str = None, field_name: str = None, issue_type_name: str = None
    ) -> dict:
        """
        Get Jira Fields Metadata from Jira Server.
        """
        if not field_name and not field_key:
            self.logger.error(
                "Either field_name or field_key must be provided, or both."
            )
        fields_meta = self.get_meta_for_project_fields(
            project_key=self.project_key, issue_type_name=issue_type_name
        )
        if not fields_meta:
            self.logger.error("Failed to get fields metadata.")
            return {}
        metadata: dict = {}
        if field_key:
            metadata = fields_meta.get(field_key, {})
            if not metadata:
                self.logger.error(f"Field with key '{field_key}' not found.")
                return {}
            if field_name and (metadata.get("name") != field_name):
                self.logger.error(
                    f"Field with key '{field_key}' has name "
                    f"'{metadata.get('name')}' but not '{field_name}'."
                )
                return {}
            return metadata
        if field_name and not field_key:
            for k, v in fields_meta.items():
                if v.get("name") == field_name:
                    metadata = v
                    return metadata
            self.logger.error(f"Field with name '{field_name}' not found.")
            return {}

    @timed_cache
    def get_field_allowed_values(
        self,
        field_key: str = None,
        field_name: str = None,
        issue_type_name: str = None,
    ) -> dict:
        """Get allowed values for a field.
        If there are none, that means the field is not a
        select / multiselect list and any value is allowed.
        """
        metadata = self.get_field_metadata(field_key, field_name, issue_type_name)
        if metadata:
            if values_allowed := metadata.get("values_allowed"):
                return [v.get("value") for v in values_allowed]
        return []

    @timed_cache
    def get_field_metadata_as_yaml(
        self,
        field_key: str = None,
        field_name: str = None,
        issue_type_name: str = None,
    ) -> str:
        """
        Get Jira Cluster Versions Map from Jira Server.
        """
        metadata = self.get_field_metadata(field_key, field_name, issue_type_name)
        if not metadata:
            self.logger.error(
                "Failed to get fields metadata for "
                f"{field_key or ''} {field_name or ''}"
            )
            return ""
        return yaml.safe_dump(metadata)

    @timed_cache
    def _get_available_release_versions(self, project_key: str):
        """
        List the available release versions for the project
        """
        jira_client: JIRA = self._session()
        jira_versions: list = jira_client.project_versions(project_key)
        versions = []
        for jira_ver in jira_versions:
            if isinstance(jira_ver, Version):
                versions.append(jira_ver.name)
        self.logger.info(
            f"Found {len(versions)} software versions "
            f"for Jira Project {project_key}"
        )
        if not versions:
            self.logger.error(
                f"No release versions found for Jira Project {project_key}"
            )
        return versions

    def available_versions(self, project_key: str = None):
        if not project_key:
            project_key = self.project_key
        if not self.__available_versions.get(project_key):
            self.__available_versions[
                project_key
            ] = self._get_available_release_versions(project_key)
        return self.__available_versions.get(project_key, [])

    def add_ticket(self, jira_issue: JiraIssueCore) -> Issue | None:
        """Post a new Jira issue to Jira API server"""
        fields: dict = jira_issue.fields
        jira_id = jira_issue.jira_id
        if not fields:
            try:
                self.logger.error(
                    'JiraIssueCore is missing ".fields" to be used '
                    "for new Jira issue creation",
                    jira_id=jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "jira_id" extras'
                )
                self.logger.error(
                    'JiraIssueCore is missing ".fields" to be used '
                    "for new Jira issue creation"
                )
            return
        try:
            # FIXME: loguru inconsistent format error:
            # ValueError: unmatched '{' in format spec
            self.logger.debug(
                f"Jira Issue {jira_id} .fields: \n{yaml.safe_dump(fields)}",
                jira_id=jira_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom format error when "
                f'"jira_id" extra'
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
            self.logger.debug(f'Jira "create_issue" server response: {jira_response}')
            return jira_response
        else:
            self.logger.error(f"Failed to create Jira issue: {jira_issue}")

    @timed_cache
    def get_user_data(self, user_id: str) -> User:
        try:
            jira_client: JIRA = self._session()
            return jira_client.user(user_id)
        except JIRAError as e:
            self.logger.error(f"{user_id} -> {e.text}")
            return ""

    @timed_cache
    def get_user_by_name(self, display_name: str) -> User | None:
        try:
            jira_client: JIRA = self._session()
            users: list[User] = jira_client.search_users(query=display_name)
            if not users:
                self.logger.warning(f'No user found for user name "{display_name}"')
                return None

            users_ok: list[User] = []
            for user in users:
                user: User = user
                found_name = user.raw.get("displayName", "")
                if names_are_equal(display_name, found_name):
                    users_ok.append(user)
            if len(users_ok) > 1:
                self.logger.error(
                    "More than one user found for user "
                    f'"{display_name}". Users: {users}'
                )
            if users and not users_ok:
                self.logger.warning(
                    "No user found with an exact name match for user "
                    f'"{display_name}". Users: {users}'
                )
            if len(users_ok) == 1:
                return users[0]
        except JIRAError as e:
            self.logger.error(f"{display_name} -> {e.text}")

    def get_labels(self, jira_id: str) -> list[str]:
        """Get all labels for a Jira issue"""
        jira_client: JIRA = self._session()
        return jira_client.issue(jira_id).fields.labels

    def add_label(self, jira_id: str, label: str, remove_existing=False) -> bool:
        """Post a new label to Jira API server"""
        self.logger.debug(f"Adding label {label} to Jira issue {jira_id}")
        jira_client: JIRA = self._session()
        labels = self.get_labels(jira_id)
        if remove_existing:
            jira_client.issue(jira_id).update(fields={"labels": [label]})
        elif label not in labels:
            labels.append(label)
            jira_client.issue(jira_id).update(fields={"labels": labels})
        new_labels = self.get_labels(jira_id)
        if label in new_labels:
            self.logger.debug(
                f"Successfully added label {label} to Jira issue {jira_id}"
            )
            return True
        self.logger.error(f"Failed to add label {label} to Jira issue {jira_id}")

    @timed_cache
    def get_cached_attachments_list(self, jira_id: str) -> list[Attachment]:
        jira_issue: JiraIssueCore = self.issue(jira_id)
        jira_client: JIRA = self._session()
        return jira_client.issue(jira_issue._id).fields.attachment

    def get_attachments_list(self, jira_issue: JiraIssueCore) -> list[Attachment]:
        jira_client: JIRA = self._session()
        return jira_client.issue(jira_issue._id).fields.attachment

    def download_attachment(
        self, jira_issue: JiraIssueCore, attachment_id: str, retry_time: int = 0
    ) -> Attachment | None:
        """Download an attachment from Jira API server"""
        try:
            jira_client: JIRA = self._session()
            attachment_response: Attachment = jira_client.attachment(attachment_id)
        except DownloadFailed as e:
            self.logger.error(
                f"Download Failed (ChunkedEncodingError) : {e}",
                jira_id=jira_issue.jira_id,
            )
            if retry_time < 3:
                retry_time += 1
                self.logger.debug(
                    f"Retrying Attachment ({attachment_id}) "
                    f"Download after Failure (retry {retry_time})",
                    jira_id=jira_issue.jira_id,
                )
                return self.download_attachment(jira_issue, attachment_id, retry_time)

        if isinstance(attachment_response, Attachment):
            try:
                self.logger.info(
                    f"Attachment downloaded from Jira: {jira_issue.info}. "
                    f"Attachment response: {attachment_response}",
                    jira_id=jira_issue.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "jira_id" extra'
                )
                self.logger.info(
                    f"Attachment downloaded from Jira: {jira_issue.info}. "
                    f"Attachment response: {attachment_response}"
                )
            return attachment_response.get()

    def add_attachment(
        self, jira_issue: JiraIssueCore, doc_name: str, doc_data: bytes | str
    ) -> Attachment | None:
        """Post a new attachment to Jira API server"""
        if not jira_issue._id:
            try:
                self.logger.error(
                    f"Can't add attachment to Jira "
                    f"without Jira Issue ID {jira_issue._id=}",
                    jira_id=jira_issue.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"{e} - loguru lib inconsistent custom "
                    f'format error when adding "jira_id" extra'
                )
                self.logger.error(
                    f"Can't add attachment to Jira "
                    f"without Jira Issue ID {jira_issue._id=}"
                )
        jira_client: JIRA = self._session()
        if isinstance(doc_data, bytes):
            attachment = BytesIO(doc_data)
        elif isinstance(doc_data, str):
            attachment = doc_data
        attach_response: Attachment = jira_client.add_attachment(
            issue=jira_issue._id,
            attachment=attachment,
            filename=doc_name,
        )
        try:
            self.logger.info(
                f"Attachment added to Jira: {jira_issue}. "
                f"Attachment response: {attach_response}",
                jira_id=jira_issue.jira_id,
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"{e} - loguru lib inconsistent custom "
                f'format error when adding "jira_id" extra'
            )
            self.logger.info(
                f"Attachment added to Jira: {jira_issue}. "
                f"Attachment response: {attach_response}"
            )
        return attach_response

    def get_all_comments(self, jira_issue: JiraIssueCore) -> list[str]:
        jira_client: JIRA = self._session()
        existing_comments: list[Comment] = jira_client.comments(issue=jira_issue._id)
        return existing_comments

    def get_all_comments_merged_as_str(self, jira_issue: JiraIssueCore) -> str:
        comments_list: list[str] = self.get_all_comments(jira_issue)
        comments_text = []
        for esr_comment in comments_list:
            esr_comment: Comment = esr_comment
            esr_text = esr_comment.raw.get("body", "")
            comments_text.append(esr_text)

        all_comments_merged: str = " ### ".join(comments_text)
        return all_comments_merged

    def get_all_comments_for_issue_after_date(
        self,
        jira_issue: JiraIssueCore,
        after_date: str,
        return_type: type = Comment,
    ):
        """after_date format: "%Y-%m-%d" or YYYY-MM-DD"""

        since = datetime.now() - datetime.strptime(after_date, "%Y-%m-%d")
        since_days: int = since.days

        return self.get_all_comments_for_issue_since(
            jira_issue, since_days, return_type
        )

    def get_all_comments_for_issue_since(
        self,
        jira_issue: JiraIssueCore,
        since_days: int = 15,
        return_type: type = tuple,
    ) -> list[tuple[str, str]]:
        jira_client: JIRA = self._session()
        existing_comments: list[Comment] = jira_client.comments(issue=jira_issue._id)
        comments_list = []

        if not existing_comments:
            return comments_list

        for comment_id in existing_comments:
            comment: Comment = jira_client.comment(
                issue=jira_issue._id, comment=comment_id
            )
            if not comment:
                continue

            comment_text: str = comment.raw.get("body")  # only text of comment
            comment_date: str = comment.raw.get("updated")

            if comment_date:
                comment_date = comment_date.split("T")[0]

            if datetime.strptime(comment_date, "%Y-%m-%d") > datetime.now() - timedelta(
                days=since_days
            ):
                if return_type is tuple:
                    to_add = (comment_date, comment_text)
                elif return_type is Comment:
                    to_add = comment

                comments_list.append(to_add)

        if comments_list:
            self.logger.debug(
                f"Found {len(comments_list)} comments for Jira issue {jira_issue.info}",
                jira_id=jira_issue.jira_id,
                vw_id=jira_issue.jira_id,
            )
        return comments_list

    def is_equal_to_last_comment(
        self, jira_issue: JiraIssueCore, new_comment: str
    ) -> bool | None:
        jira_client: JIRA = self._session()
        existing_comments: list[Comment] = jira_client.comments(issue=jira_issue._id)
        if not existing_comments:
            return
        comment_id: str = existing_comments[-1]
        comment: Comment = jira_client.comment(issue=jira_issue._id, comment=comment_id)
        if not comment:
            return
        last_comment_from_jira: str = comment.raw.get("body")  # only text of comment
        if new_comment == last_comment_from_jira:
            self.logger.warning("Same comment already present in Jira")
            return True
        return

    def add_comment(
        self,
        jira_issue: JiraIssueCore,
        comment: str,
        source: str = "",
    ) -> bool | None:
        """Add a comment to a Jira issue"""
        comment = build_auto_comment(comment, source)
        if not jira_issue._id:
            self.logger.error(
                "Can't add comment to Jira without Jira Issue ID",
                jira_id=jira_issue.jira_id,
            )
            return
        try:
            if self.is_equal_to_last_comment(jira_issue, comment):
                return True
            jira_client: JIRA = self._session()
            response: Comment = jira_client.add_comment(
                issue=jira_issue._id, body=comment
            )
            if response:
                self.logger.info(
                    f"Added comment to Jira: {comment}", jira_id=jira_issue.jira_id
                )
                return True
        except (ValueError, KeyError, IndexError):
            self.logger.info(f"Comment added to Jira: {jira_issue}")
            return True
        except (JIRAError, Exception) as e:
            self.logger.error(f"Failed to add comment to Jira: {e}")

    @timed_cache
    def get_tickets_with_changed_status(
        self,
        since: int = 36,
        timeframe: str = "h",  # d = days, h = hours, m = minutes
        new_status: str = "",
        old_status: str = "",
        current_status: tuple[str] = None,
        status_not_in: tuple[str] = None,
        jira_ids: str | tuple[str] = None,
    ) -> list[JiraIssue]:
        """this method uses a timed cache to avoid querying Jira too often

        timeframe: str -> d = days, h = hours, m = minutes

        if since == 0 -> jql "AND status changed " (without after)"""

        if timeframe not in ("d", "h", "m"):
            self.logger.error(f"Invalid timeframe: {timeframe}")
            return []
        if timeframe == "d":
            pass
        elif timeframe == "h":
            pass
        elif timeframe == "m":
            pass

        if isinstance(current_status, str):
            current_status = str(tuple([current_status])).replace(",)", ")")

        if isinstance(status_not_in, str):
            status_not_in = str(tuple([status_not_in])).replace(",)", ")")

        # changed status JQL:
        jql = (
            f"{self.base_jql} "
            f'AND status changed AFTER "-{since}{timeframe}" '
            f'FROM "{old_status}" '
            f'TO "{new_status}" '
            f"AND status in {current_status} "
            f"AND status not in {status_not_in} "
        )

        if jira_ids:
            if isinstance(jira_ids, str):
                jira_ids = tuple([jira_ids])
            jira_ids = str(jira_ids).replace(",)", ")")
            jql += f"AND issuekey in {jira_ids} "

        if since == 0:
            jql = jql.replace(
                f'AND status changed AFTER "-{since}{timeframe}"', "AND status changed"
            )

        if not new_status:
            jql = jql.replace(f'TO "{new_status}" ', "")

        if not old_status:
            jql = jql.replace(f'FROM "{old_status}" ', "")

        if not current_status:
            jql = jql.replace(f"AND status in {current_status} ", "")

        if not status_not_in:
            jql = jql.replace(f"AND status not in {status_not_in} ", "")

        try:
            return self.cached_query(jql)
        except Exception as e:
            self.logger.error(
                f"Failed to get the tickets based on JQL query {jql} : {e}"
            )
            return []

    def get_tickets_updated(
        self,
        since: int = 36,
        timeframe: str = "h",  # d = days, h = hours, m = minutes
    ) -> list[JiraIssue]:
        """timeframe: str -> d = days, h = hours, m = minutes"""
        if timeframe not in ("d", "h", "m"):
            self.logger.error(f"Invalid timeframe: {timeframe}")
            return []

        self.logger.info(f"Query Jira issues updated in the past {since}{timeframe}.")
        jql = f"{self.base_jql} AND updated >= -{since}{timeframe} "

        try:
            if jira_issues := self.query(jql):
                return jira_issues
            else:
                return []
        except Exception as e:
            self.logger.error(
                f"Failed to get the tickets based on JQL query {jql} : {e}"
            )
            return []

    def get_tickets_with_field_not_empty(
        self,
        field: list[str],
        since: int = 4,
        timeframe: str = "h",  # d = days, h = hours, m = minutes
    ) -> list[JiraIssue]:
        """timeframe: str -> d = days, h = hours, m = minutes"""
        self.logger.info(
            f"Query Jira issues where the field {field} were "
            f"updated in the past {since} {timeframe}."
        )

        jql = (
            f"{self.base_jql}"
            f'AND "{field}" is not EMPTY '
            f"AND updated >= -{since}{timeframe} "
        )

        try:
            if jira_issues := self.query(jql):
                return jira_issues
            else:
                return []
        except Exception as e:
            self.logger.error(
                f"Failed to get the tickets based on JQL query {jql} : {e}"
            )
            return []

    def update_field(self, jira_id: str, field_name: str, field_value: str) -> bool:
        """Post a new field value for Jira issue ID to Jira API server"""
        self.logger.debug(f"Adding new {field_name} to Jira issue {jira_id}")
        jql = f'project = {self.project_key} AND key = "{jira_id}"'
        jira_issue_list: list = self.query(jql)
        if not jira_issue_list:
            self.logger.warning(
                f'Jira ticket "{jira_id}" not found in project ' f"{self.project_key}"
            )
        jira_issue: JiraIssueCore = jira_issue_list[0]
        _id = jira_issue._id
        jira_client: JIRA = self._session()
        jira_client.issue(_id).update(fields={field_name: field_value})
        if field_value in jira_client.issue(_id).get_field(field_name):
            self.logger.info(
                f"Posted succesfully new {field_name} to Jira {jira_issue.ui_url}",
                jira_id=jira_id,
            )
            return True
        self.logger.error(
            f"Failed to post new {field_name} (len {len(field_value)})"
            f" to Jira ticket {jira_id}",
            jira_id=jira_id,
        )

    def update_description(self, jira_id: str, description: str) -> bool:
        """Post a new description to Jira API server"""
        return self.update_field(jira_id, "description", description)

    def update_status(self, jira_id: str, new_status: str, comment: str) -> bool:
        self.logger.debug(f"Adding new status to Jira issue {jira_id}")
        jql = f'project = {self.project_key} AND key = "{jira_id}"'
        jira_issue_list: list = self.query(jql)
        if not jira_issue_list:
            self.logger.warning(
                f'Jira ticket "{jira_id}" not found in project {self.project_key}'
            )
        jira_issue: JiraIssueCore = jira_issue_list[0]
        _id = jira_issue._id
        jira_client: JIRA = self._session()
        issue = jira_client.issue(_id)

        transitions = jira_client.transitions(issue)
        transition_id = None
        for transition in transitions:
            if transition["to"]["name"] == new_status:
                transition_id = transition["id"]
                break

        if transition_id is None:
            self.logger.error(
                f"Failed to update status to {new_status} "
                f"to Jira {jira_issue.ui_url}",
                jira_id=jira_id,
            )
            return

        jira_client.transition_issue(issue, transition_id, comment=comment)
        self.logger.info(
            f"Posted succesfully new status {new_status} "
            f"to Jira {jira_issue.ui_url}",
            jira_id=jira_id,
        )
        return self.issue(jira_id)

    def post_sync_report(
        self, jira_id: str, sync_report: dict, extra: str = None, max_len: int = 32_767
    ):
        time = f'LAST SYNC: *{str(datetime.now()).rsplit(":", 1)[0]}*\n\n'
        yaml_sync_report: str = yaml.safe_dump(sync_report, indent=4) or ""
        yaml_sync_report = time + (
            yaml_sync_report.replace("\n", "\n\n")
            .replace("\n    ", "* ")
            .replace("'", "")
        )
        if extra:
            yaml_sync_report += f"\n\n{extra}"

        if len(yaml_sync_report) > max_len:
            yaml_sync_report = f"{yaml_sync_report[:max_len - 20]} ... [trimmed] ..."

        if self.update_description(jira_id, yaml_sync_report):
            self.logger.info(
                "Sync report posted succesfully to Jira " f"ticket {jira_id}",
                jira_id=jira_id,
            )
            return True
        self.logger.error(
            "Failed to post sync report to Jira " f"ticket {jira_id}", jira_id=jira_id
        )


@connection_retry(times=5)
def jira_client_core(server: str, user: str, token: str) -> JiraClientCore:
    """Interact with the Jira server."""
    try:
        jira = JiraClientCore(server, user, token).connect()
        if not jira:
            raise JiraApiError
        logger.info(
            f"👍👍👍 JIRA server {user}@{server} connection successful 👍👍👍"
        )  # noqa: E501
        return jira
    except (JiraApiError, Exception) as ex:
        logger.error(f"Failed to connect to JIRA server {user}@{server}: {ex}")
        raise APIServerConnectionError
