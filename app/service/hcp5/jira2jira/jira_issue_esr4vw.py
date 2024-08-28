# standard
from dataclasses import dataclass

# external

# project core

# project extension
from app.ext.jira_esr.jira_issue import EsrLabsJiraIssue

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger


@dataclass
class EsrIssueForVwJiraSync(EsrLabsJiraIssue):
    """AHCP5 Jira2Jira specific wrapper around a EsrLabsJiraIssue"""

    __devstack_id = ""
    logger = logger

    @property
    def esr_id(self) -> str:
        """ESR Labs Jira Issue ID"""
        return self.jira_id

    @property
    def vw_id(self) -> str:
        """VW Audi Devstack Jira Issue ID"""
        if self.__devstack_id:
            return self.__devstack_id
        if not self.external_reference:
            return ""
        self.__devstack_id = self.external_reference.replace(" ", "")
        return self.__devstack_id

    @property
    def answer_from_oem(self) -> str:
        """Answer from OEM"""
        return self.get_field(self.jira_map.extras.answer_from_oem)

    @answer_from_oem.setter
    def answer_from_oem(self, new_val) -> str:
        """Answer from OEM setter"""
        return self.set_field(self.jira_map.extras.answer_from_oem, new_val)

    def __repr__(self):
        return (
            f"VW: {self.vw_id}  ESR: {self.esr_id}  "
            f"ESR UI: {self.ui_url}  ESR API: {self.url}"
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
                vw_id=self.vw_id,
                esr_id=self.esr_id,
            )
            self._output_ok_for_str_format = True
        except (ValueError, KeyError, IndexError) as e:
            self.logger.warning(
                f"logger failed to display value for ESR Jira Id {self.esr_id} "
                f"| VW Jira Id {self.vw_id} , due to {e}"
            )
            self._output_ok_for_str_format = False
        return self._output_ok_for_str_format
