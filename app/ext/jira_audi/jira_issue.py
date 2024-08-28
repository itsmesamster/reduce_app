# standard
from dataclasses import dataclass, field

# external
from jira import Issue, JIRA
from jira.exceptions import JIRAError

# project core
from app.core.jira.jira_issue import JiraIssueCore
from app.core.jira.exceptions import JiraApiError

# project extension
from app.ext.jira_audi.jira_map import VwAudiHcp5JiraFieldMap


@dataclass
class VwAudiJiraIssue(JiraIssueCore):
    """Project specific wrapper around a JiraIssueCore"""

    jira_map: VwAudiHcp5JiraFieldMap = field(
        default_factory=lambda: VwAudiHcp5JiraFieldMap()
    )

    @property
    def url(self) -> str:
        """Jira Issue URL."""
        return self.get(self.jira_map.url)

    def __repr__(self):
        return f"JIRA: {self.jira_id}  UI: {self.ui_url}  API: {self.url}"

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
                f"logger failed to display value for Jira Id {self.jira_id} "
                f"due to {e}"
            )
            self._output_ok_for_str_format = False
        return self._output_ok_for_str_format

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
                    f" for Jira Id {self.jira_id} , due to {e}"
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
                    f"Jira Id {self.jira_id} , due to {e}"
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
