# standard
from dataclasses import dataclass, field

# external

# project core
from app.core.jira.jira_issue import JiraIssueCore

# project extension
from app.ext.jira_esr.jira_map import EsrLabsAhcp5JiraFieldMap


@dataclass
class EsrLabsJiraIssue(JiraIssueCore):
    """ESR Labs specific wrapper around a JiraIssueCore"""

    jira_map: EsrLabsAhcp5JiraFieldMap = field(
        default_factory=lambda: EsrLabsAhcp5JiraFieldMap()
    )

    @property
    def url(self) -> str:
        """Jira Issue URL."""
        return self.get(self.jira_map.url)

    @property
    def external_reference(self) -> str:
        """Textfield to reference external ticket id."""
        return self.get_field(self.jira_map.external_reference)

    @external_reference.setter
    def external_reference(self, new_val) -> str:
        """Textfield to set external ticket id reference."""
        return self.set_field(self.jira_map.external_reference, new_val)

    @property
    def origin(self) -> str:
        """Dropdown to select where the ticket is originally from."""
        return self.get_field(f"{self.jira_map.origin}/value")

    @property
    def audi_cluster(self) -> str:
        """Multi-value field to select the Audi Cluster/s."""
        return self.get_field(self.jira_map.audi_cluster)

    @audi_cluster.setter
    def audi_cluster(self, clusters: list[str], default: str = "-"):
        """Audi Cluster/s setter"""
        set_clusters = []
        for cluster in clusters:
            set_clusters.append({"value": cluster})
        if not set_clusters:
            set_clusters.append({"value": default})
        return self.set_field(self.jira_map.audi_cluster, set_clusters)

    @property
    def audi_vr(self) -> str:
        """Get Audi VR/s"""
        return self.get_field(self.jira_map.audi_cluster)

    @audi_vr.setter
    def audi_vr(self, vrs: list[str]):
        """Audi VR/s setter"""
        set_vrs = []
        for vr in vrs:
            set_vrs.append({"value": vr})
        if set_vrs:
            return self.set_field(self.jira_map.audi_vr, set_vrs)

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
                "logger failed to display value for "
                f"Jira Id {self.jira_id} , due to {e}"
            )
            self._output_ok_for_str_format = False
        return self._output_ok_for_str_format
