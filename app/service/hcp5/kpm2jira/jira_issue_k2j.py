# standard
from dataclasses import dataclass

# external
from jira import Issue, JIRA
from jira.exceptions import JIRAError

# project core
from app.core.jira.exceptions import JiraApiError

# project extension
from app.ext.jira_esr.jira_issue import EsrLabsJiraIssue

# project service


@dataclass
class EsrLabsJiraIssueForKpmSync(EsrLabsJiraIssue):
    """Kpm2Jira specific wrapper around a EsrLabsJiraIssue"""

    __kpm_id = ""

    @property
    def kpm_id(self) -> str:
        """Textfield to reference external KPM fields."""
        if self.__kpm_id:
            return self.__kpm_id
        self.__kpm_id = self.external_reference
        return self.__kpm_id

    @property
    def cause_of_reject(self) -> str:
        """Cause of reject"""
        cause = self.get_field(self.jira_map.extras.cause_of_reject)
        if isinstance(cause, dict):
            return cause.get("value", "")

    @property
    def question_to_oem(self) -> str:
        """Question to OEM"""
        return self.get_field(self.jira_map.extras.question_to_oem)

    @question_to_oem.setter
    def question_to_oem(self, new_val) -> str:
        """Question to OEM setter"""
        return self.set_field(self.jira_map.extras.question_to_oem, new_val)

    @property
    def feedback_to_oem(self) -> str:
        """Feedback to OEM"""
        return self.get_field(self.jira_map.extras.feedback_to_oem)

    @feedback_to_oem.setter
    def feedback_to_oem(self, new_val) -> str:
        """Feedback to OEM setter"""
        return self.set_field(self.jira_map.extras.feedback_to_oem, new_val)

    @property
    def feedback_from_oem(self) -> str:
        """Feedback from OEM"""
        return self.get_field(self.jira_map.extras.feedback_from_oem)

    @feedback_from_oem.setter
    def feedback_from_oem(self, new_val) -> str:
        """Feedback from OEM setter"""
        return self.set_field(self.jira_map.extras.feedback_from_oem, new_val)

    @property
    def answer_from_oem(self) -> str:
        """Answer from OEM"""
        return self.get_field(self.jira_map.extras.answer_from_oem)

    @answer_from_oem.setter
    def answer_from_oem(self, new_val) -> str:
        """Answer from OEM setter"""
        return self.set_field(self.jira_map.extras.answer_from_oem, new_val)

    @property
    def last_answer_from_oem(self) -> str:
        """Last Answer from OEM"""
        answer_from_oem: str = self.answer_from_oem
        if not answer_from_oem:
            return ""
        all_answers_from_oem: str = answer_from_oem.split("\n\n 📆 \t ")
        if len(all_answers_from_oem) <= 1:
            return self.answer_from_oem
        return f" 📆 \t {all_answers_from_oem[-1]}"

    def __repr__(self):
        return (
            f"KPM: {self.kpm_id}  JIRA: {self.jira_id}  "
            f"UI: {self.ui_url}  API: {self.url}"
        )

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
                kpm_id=self.kpm_id,
                jira_id=self.jira_id,
            )
            self._output_ok_for_str_format = True
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display value for Jira Id {self.jira_id} "
                f"| KPM ID {self.kpm_id} , due to {e}"
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
                    kpm_id=self.kpm_id,
                    jira_id=self.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.error(
                    f"logger failed to display value for updating [{jira_ui_field_name}]"  # noqa: E501
                    f" for Jira Id {self.jira_id} | KPM ID {self.kpm_id} , due to {e}"
                )
            update_fields_dict[custom_field_name] = field_value
        if not update_fields_dict:
            try:
                self.logger.info(
                    "No custom fields to update to jira server. ",
                    kpm_id=self.kpm_id,
                    jira_id=self.jira_id,
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.warning(
                    f"logger failed to display value for "
                    f"Jira Id {self.jira_id} | KPM ID {self.kpm_id} , due to {e}"
                )
            return
        try:
            self.logger.info(
                f"sending bulk fields update to server: {update_fields_dict} "
                f"for kpm_id {self.kpm_id} | jira_id {self.jira_id}"
            )
            server_issue.update(fields=update_fields_dict, jira=jira_client)
            self.logger.info(
                f"Successfully updated custom fields {fields_to_update} to jira server",
                kpm_id=self.kpm_id,
                jira_id=self.jira_id,
            )
        except (JiraApiError, JIRAError) as e:
            self.logger.error(
                f"Failed to update fields to jira server due to Jira error: {e} ",
            )
            # kpm_id=self.kpm_id, jira_id=self.jira_id)
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display bulk fields update dict due to {e}",
                kpm_id=self.kpm_id,
                jira_id=self.jira_id,
            )
        except Exception:
            self.logger.error(
                "Failed to update fields to jira server. ",
                kpm_id=self.kpm_id,
                jira_id=self.jira_id,
            )
