# standard
from abc import ABC
from dataclasses import dataclass, asdict, field
import json

# external
import yaml
from jira import Issue, JIRA
from jira.exceptions import JIRAError

# project core
from app.core.custom_logger import logger
from app.core.utils import convert_size
from app.core.jira.jira_map import JiraFieldsMapCore
from app.core.jira.exceptions import JiraApiError


class JiraIssue(ABC):
    pass


@dataclass
class JiraIssueCore(JiraIssue):
    """Wrapper around a Jira raw issue for convenience access."""

    raw: dict = field(default_factory=lambda: {})
    jira_map: JiraFieldsMapCore = field(default_factory=lambda: JiraFieldsMapCore())
    fields = None
    __jira_id = ""
    __id = ""
    logger = logger
    _output_ok_for_str_format = None

    @property
    def url(self) -> str:
        """Jira Issue URL."""
        return self.get(self.jira_map.url)

    @property
    def _id(self) -> str:
        """Issue ID

        issue.fields.id  [e.g. id: '144331']
        """
        if not self.__id:
            self.__id = self.get("id")
        return self.__id

    @property
    def issue_type(self) -> str:
        """Issue Type
        issue.fields.issuetype.name  [e.g. issuetype: 'Bug']
        """
        return self.get_field("issuetype/name")

    @issue_type.setter
    def issue_type(self, value):
        return self.set_field("issuetype/name", value)

    @property
    def project(self) -> str:
        return self.get_field("project/key")

    @property
    def reporter(self) -> str:
        return self.get_field("reporter/displayName")

    @property
    def jira_id(self) -> str:
        """Jira Issue ID

        issue.fields.key [e.g. key: AHCP5-24159]
        """
        if self.__jira_id:
            return self.__jira_id
        self.__jira_id = self.get(self.jira_map.ticket_id)
        return self.__jira_id

    @property
    def status(self) -> str:
        """Issue workflow status."""
        status_dict = self.get_field(self.jira_map.status)
        if isinstance(status_dict, dict):
            return status_dict.get("name")

    def get(self, field_name: str):
        """Read a field name from the root of the raw issue"""
        return self.raw.get(field_name)

    def get_multiple_values_field(self, values: list, keys: list[str]) -> list[str]:
        keys.pop(0)
        if not keys:
            return values
        for key in keys:
            for i, value in enumerate(values):
                if isinstance(value, dict):
                    values[i] = value.get(key, "")
        return values

    def get_field(self, field_name: str) -> str | list[str]:
        """Read a field name from the raw[fields] hash"""
        if self.fields is None:
            self.fields = self.get("fields")
        value = self.fields
        keys = field_name.split("/")
        for i, key in enumerate(keys):
            if value:
                value = value.get(key, "")
                if not isinstance(value, (dict, list)):
                    return value
            if isinstance(value, list):
                return self.get_multiple_values_field(value, keys[i:])
        return value

    def set_field(self, field_name: str, value: str | list | dict) -> str | list | dict:
        """Set a field name from the raw[fields] hash"""
        if self.fields is None:
            if self.get("fields"):
                self.fields = self.get("fields")
            else:
                self.fields = {}
        self.fields[field_name] = value
        return self.get_field(field_name)

    def get_all_fields(self) -> dict:
        if self.fields is None:
            self.fields = self.get("fields")
        return self.fields

    def get_all_fields_as_yaml(self):
        return yaml.safe_dump(self.get_all_fields())

    @property
    def ui_url(self):
        server: str = str(self.url).split("/rest/api/")[0]
        browse_ticket_ui: str = f"{server}/browse/{self.jira_id}"
        return browse_ticket_ui

    def short_info(self):
        return self.jira_id, self.ui_url, self.url

    @property
    def info(self):
        return f"JIRA: {self.jira_id}  " f"UI: {self.ui_url}  " f"API: {self.url}"

    def __repr__(self):
        return f"JIRA: {self.jira_id}  UI: {self.ui_url}  API: {self.url}"

    def __str__(self):
        return self.__repr__()

    def raw_json_from_api(self):
        return json.dumps(self.raw, indent=4)

    def as_dict(self):
        return asdict(self)

    def as_json(self):
        return json.dumps(self.as_dict(), indent=4)

    def as_yaml(self):
        return yaml.safe_dump(self.as_dict())

    @property
    def yaml(self):
        return self.as_yaml()

    def output_ok(self) -> bool:
        # fields values (description field usually) contain code that might
        # cause str format KeyError when added to logs
        # e.g. src:DiagServiceEvents.hpp|lin:211|p_output:
        # {"domainRepairInstructionId":1,"errorCode":50462751, ...
        if self._output_ok_for_str_format is not None:
            return self._output_ok_for_str_format
        try:
            jira_yml = self.get_all_fields_as_yaml()
            self.logger.debug(
                f"Checking JiraIssue for sync: \n{jira_yml}",
                jira_id=self.jira_id,
            )
            self._output_ok_for_str_format = True
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display value for Jira Id {self.jira_id}, "
                f"due to {e}"
            )
            self._output_ok_for_str_format = False
        return self._output_ok_for_str_format

    def update_fields(self, jira_client: JIRA, fields_and_new_values: dict):
        server_issue: Issue = jira_client.issue(self._id)
        update_fields_dict = {}
        for field_name, new_field_value in fields_and_new_values.items():
            server_issue_field_value = server_issue.get_field(field_name)
            if new_field_value != server_issue_field_value:
                update_fields_dict[field_name] = new_field_value
            if self.get_field(field_name) != server_issue_field_value:
                self.set_field(field_name, new_field_value)

        try:
            self.logger.info(
                f"sending bulk fields update to server: {update_fields_dict} "
                f"for jira_id {self.jira_id}"
            )

            server_issue.update(fields=update_fields_dict, jira=jira_client)

            self.logger.info(
                f"Successfully updated custom fields {update_fields_dict.keys()} "
                "to jira server",
                jira_id=self.jira_id,
            )
        except (JiraApiError, JIRAError) as e:
            self.logger.error(
                f"Failed to update fields to jira server due to Jira error: {e} ",
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display bulk fields update dict due to {e}",
                jira_id=self.jira_id,
            )
        except Exception:
            self.logger.error(
                "Failed to update fields to jira server. ",
                jira_id=self.jira_id,
            )

    def update_server_custom_fields(self, jira_client: JIRA, fields_to_update: list):
        """Update all changed field values to jira server

        e.g.:

                from jira import JIRA

                jc = JIRA(server=server, basic_auth=(email, token))

                jira_issue.update_server_fields(jc)
        """
        server_issue: Issue = jira_client.issue(self._id)
        update_fields_dict = {}
        for (
            jira_ui_field_name,
            custom_field_name,
        ) in self.jira_map.extras.__dict__.items():
            if jira_ui_field_name not in fields_to_update:
                continue
            field_value = self.get_field(custom_field_name)
            try:
                self.logger.debug(
                    f"updating [{jira_ui_field_name}] to\n{field_value}",
                    jira_id=self.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.error(
                    f"logger failed to display value for updating [{jira_ui_field_name}]"  # noqa: E501
                    f" for Jira Id {self.jira_id}, due to {e}"
                )
            update_fields_dict[custom_field_name] = field_value
        if not update_fields_dict:
            try:
                self.logger.info(
                    "No custom fields to update to jira server. ",
                    jira_id=self.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"logger failed to display value for "
                    f"Jira Id {self.jira_id}, due to {e}"
                )
            return
        try:
            self.logger.info(
                f"sending bulk fields update to server: {update_fields_dict} "
                f"for jira_id {self.jira_id}"
            )
            server_issue.update(fields=update_fields_dict, jira=jira_client)
            self.logger.info(
                f"Successfully updated custom fields {fields_to_update} to jira server",
                jira_id=self.jira_id,
            )
        except (JiraApiError, JIRAError) as e:
            self.logger.error(
                f"Failed to update fields to jira server due to Jira error: {e} ",
            )
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display bulk fields update dict due to {e}",
                jira_id=self.jira_id,
            )
        except Exception:
            self.logger.error(
                "Failed to update fields to jira server. ",
                jira_id=self.jira_id,
            )

    @property
    def summary(self):
        return self.get_field("summary")

    @summary.setter
    def summary(self, value):
        return self.set_field("summary", value)

    @property
    def description(self):
        return self.get_field("description")

    @description.setter
    def description(self, value):
        return self.set_field("description", value)

    @property
    def labels(self) -> list[str]:
        return self.get_field("labels")

    @labels.setter
    def labels(self, value: str | list[str]):
        if isinstance(value, str):
            value = [value]
        return self.set_field("labels", value)

    @property
    def fix_versions(self) -> list[str]:
        """It will return a list of fix versions names as
        written in Jira issue fixVersions -> name fields

        It can also be something like:
            "B050 (VR30)"
        """
        return self.get_field("fixVersions/name")

    @fix_versions.setter
    def fix_versions(self, value: str | list) -> list[str]:
        if isinstance(value, str):
            value = [value]
        version_list = [{"name": version} for version in value]
        return self.set_field("fixVersions", version_list)

    @property
    def components(self) -> list[str]:
        """It will return a list of components names as
        written in Jira issue components -> name fields
        """
        return self.get_field("components/name")

    @components.setter
    def components(self, value: str | list) -> list[str]:
        if isinstance(value, str):
            value = [value]
        component_list = [{"name": component} for component in value]
        return self.set_field(JiraFieldsMapCore.components, component_list)

    @property
    def attachments(self, attachment_details: list = None) -> list[dict]:
        """Get a list of attachments with details from Jira ticket."""
        if not attachment_details:
            attachment_details = ["filename", "id", "created", "mimeTypee", "size"]

        ticket_attachments = self.get_field("attachment") or []

        attachment_list, total_size = [], 0
        for attachment in ticket_attachments:
            new_dict = {}
            for k in attachment_details:
                if k not in attachment.keys():
                    continue
                if k == "created" and isinstance(attachment[k], str):
                    new_dict["created"] = attachment[k].split(".")[0]
                    continue
                new_dict[k] = attachment[k]

            size = new_dict.get("size", 0)
            if size:
                total_size += size
                new_dict["vol"] = " ".join(map(str, convert_size(size)))

            attachment_list.append(new_dict)

        total_size, unit = convert_size(total_size)

        self.logger.info(
            f"[{self.__class__.__name__} {self.jira_id}] "
            f"Found {len(attachment_list)} "
            f"attachments of total size {total_size} {unit}",
            jira_id=self.jira_id,
        )
        self.logger.debug(
            f"[{self.__class__.__name__} {self.jira_id}] "
            f"Attachments:\n{yaml.safe_dump(attachment_list)}",
            jira_id=self.jira_id,
        )
        return attachment_list
