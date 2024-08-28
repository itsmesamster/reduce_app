# standard

# project extension
from app.ext.jira_esr.jira_map import (
    ClusterMap,
    EsrLabsAhcp5JiraFieldMap as EsrFields,
)

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.jira_issue_vwaudi import Hcp5VwAudiJiraIssue
from app.service.hcp5.jira2jira.jira_client_esr_j2j import (
    ESRLabsJiraClientForVwJiraSync,
)
from app.service.hcp5.jira2jira.jira_issue_esr4vw import EsrIssueForVwJiraSync
from app.service.hcp5.jira2jira.sync_exceptions import JiraIssueTypeNotAcceptedForSync
from app.service.hcp5.jira2jira.config import (
    J2J_ESR_JIRA,
    MAPPER_BY_ISSUE_TYPE,
    INTEGRATION_LABELS,
)


class EsrJira2VwAudiJiraTransformer:
    def __init__(
        self,
        esr_jira_client: ESRLabsJiraClientForVwJiraSync,
        map: dict = None,
        cluster_map_yml_path: str = None,
    ):
        """
        Represents Mapper class.
        """
        self.esr: ESRLabsJiraClientForVwJiraSync = esr_jira_client
        self.map: dict = map or MAPPER_BY_ISSUE_TYPE
        self.cluster_map: ClusterMap = ClusterMap()
        if cluster_map_yml_path:
            self.cluster_map: ClusterMap = ClusterMap(cluster_map_yml_path)
        self.logger = logger

    def get_audi_clusters(
        self,
        vw_ticket: Hcp5VwAudiJiraIssue,
        default_audi_cluster: str = J2J_ESR_JIRA.default_audi_cluster,
    ) -> list[str]:
        return self.cluster_map.get_audi_clusters(
            vw_ticket.software_versions,
            vw_ticket.versions,
            default_audi_cluster,
            other_ticket_id=vw_ticket.jira_id,
        )

    def get_audi_vr(
        self,
        vw_ticket: Hcp5VwAudiJiraIssue,
        default_audi_cluster: str = J2J_ESR_JIRA.default_audi_cluster,
    ) -> list[str]:
        return self.cluster_map.get_clvr(
            vw_ticket.software_versions,
            vw_ticket.versions,
            default_audi_cluster,
            other_ticket_id=vw_ticket.jira_id,
        )

    def filter_esr_field_values_to_set(
        self,
        field_key: str,
        values: list[str] | str,
        vw_id: str = "",
        default_value: str = "-",
        issue_type: str = None,
        field_name: str = None,
    ) -> list[str]:
        """Filter values by accepted values for field_name.
        If "values" is not a list, it is converted to a list.
        If the values list contains an option that is
        not accepted in Jira, it is removed from the list.

        Returns a list of accepted values."""
        if not isinstance(values, list):
            values = [values]
        accepted_values = self.esr.get_field_allowed_values(
            field_key,
            field_name,
            issue_type_name=issue_type,
        )
        field = field_name or " "
        if field_key:
            field += field_key
        self.logger.debug(f"accepted values for {field}: {accepted_values}")
        values_to_set = [val for val in values if val in accepted_values]
        not_accepted_values = list(set(values) - set(values_to_set))
        if not_accepted_values:
            self.logger.debug(
                f"not accepted values for {field}: " f"{not_accepted_values}",
                vw_id=vw_id,
            )
        if not values_to_set:
            if not default_value:
                values_to_set = []
            elif default_value in accepted_values:
                values_to_set = [default_value]
            else:
                values_to_set = [accepted_values[0]]
                self.logger.warning(
                    f"not accepted values for {field} and "
                    'the default value "-" not accepted in ESR Jira. '
                    f"setting {accepted_values[0]} as default.",
                    vw_id=vw_id,
                )
        self.logger.debug(f"Values to set {len(values_to_set)} {values_to_set}")
        return values_to_set

    def to_esr_jira(self, vw_ticket: Hcp5VwAudiJiraIssue) -> EsrIssueForVwJiraSync:
        vw_id: str = vw_ticket.jira_id

        issue_type = vw_ticket.issue_type
        if not issue_type:
            self.logger.error(
                f"VW Audi Jira [{vw_id}] has no issue type. ", vw_id=vw_id
            )
            return

        if issue_type not in self.map.keys():
            msg = f"Ignoring unsupported issue type for sync -> {issue_type}"
            self.logger.warning(msg, vw_id=vw_id)
            raise JiraIssueTypeNotAcceptedForSync(msg)

        mapper: dict = self.map.get(issue_type)
        if not mapper:
            self.logger.warning(
                f"VW Audi Jira [{vw_id}] is an unsupported issue type {issue_type}. "
                f"Supported issue types are: {self.map.keys()}",
                vw_id=vw_id,
            )
            return

        self.logger.info(
            f"Converting VW Audi Jira [{vw_id}] to ESR Jira ... ", vw_id=vw_id
        )

        new_esr_issue = EsrIssueForVwJiraSync()

        hardcoded_map: dict = mapper["hardcoded"]
        for esr_field, hard_value in hardcoded_map.items():
            new_esr_issue.set_field(esr_field, hard_value)

        jira_issue_map: dict = mapper["from_vwjira"]
        for esr_field, vw_field in jira_issue_map.items():
            value = vw_ticket.get_field(vw_field)
            if "/" in vw_field:
                subkey = vw_field.split("/")[-1]
                value = {subkey: value}
            new_esr_issue.set_field(esr_field, value)

        from_vwjira_property_map: dict = mapper["from_vwjira_property"]
        for esr_field, vw_field in from_vwjira_property_map.items():
            value = getattr(vw_ticket, vw_field)
            new_esr_issue.set_field(esr_field, value)

        # external reference
        external_ref = vw_ticket.jira_id.replace("HCP5-", "HCP5- ")
        new_esr_issue.external_reference = external_ref

        # components
        new_esr_issue.components = self.get_components_to_set(vw_ticket, new_esr_issue)

        # audi cluster (Task)
        if issue_type == "Task":
            audi_clusters: list[str] = self.get_audi_clusters(vw_ticket)
            if audi_cluster_to_set := self.filter_esr_field_values_to_set(
                field_key=EsrFields.audi_cluster,
                values=audi_clusters,
                vw_id=vw_id,
                issue_type=issue_type,
            ):
                new_esr_issue.audi_cluster = audi_cluster_to_set

        # (Integration) fix version + audi cluster + audi vr
        if issue_type == "Integration":
            # fix version (Integration)
            if accepted_fix_versions := self.filter_esr_field_values_to_set(
                field_key="fixVersions",
                values=vw_ticket.fix_versions,
                vw_id=vw_id,
                default_value="",
                issue_type=issue_type,
            ):
                new_esr_issue.fix_versions = accepted_fix_versions

            # audi Cluster (Integration)
            if audi_cluster_to_set := self.filter_esr_field_values_to_set(
                EsrFields.audi_cluster,
                vw_ticket.audi_cluster,
                vw_id=vw_id,
                issue_type=issue_type,
            ):
                self.logger.debug(f"{audi_cluster_to_set=}")
                new_esr_issue.audi_cluster = audi_cluster_to_set

            # audi VR (Integration)
            if audi_vr_to_set := self.filter_esr_field_values_to_set(
                field_key=EsrFields.audi_vr,
                values=vw_ticket.audi_vr,
                vw_id=vw_id,
                issue_type=issue_type,
            ):
                self.logger.debug(f"{audi_vr_to_set=}")
                new_esr_issue.audi_vr = audi_vr_to_set

            if vw_ticket.labels:
                labels = []
                for label in vw_ticket.labels:
                    if label in INTEGRATION_LABELS:
                        labels.append(label)
                if labels:
                    new_esr_issue.labels = labels

        yml = new_esr_issue.get_all_fields_as_yaml()
        if new_esr_issue.output_ok():
            self.logger.debug(
                f"Devstack Cariad VW Audi Jira ticket {vw_id} "
                f"is READY for ESR Jira:\n{yml}"
            )
        else:
            self.logger.debug("TICKET READY FOR JIRA.", vw_id=vw_id)

        return new_esr_issue

    def get_components_to_set(
        self, vw_ticket: Hcp5VwAudiJiraIssue, esr_issue: EsrIssueForVwJiraSync
    ) -> list[str]:
        components = []
        issue_type = vw_ticket.issue_type

        if issue_type == "Task":
            components: list[str] = vw_ticket.get_components_from_title()

        elif issue_type == "Integration":
            components: list[str] = self.convert_components(vw_ticket.components)
        else:
            return []

        components_to_set = self.filter_esr_field_values_to_set(
            EsrFields.components,
            components,
            vw_ticket.jira_id,
            J2J_ESR_JIRA.DEFAULT_COMPONENT,
            issue_type=issue_type,
        )
        components_not_found = [c for c in components if c not in components_to_set]
        if components_not_found:
            self.logger.debug(
                "Components not found "
                f"{len(components_not_found)} {components_not_found}"
            )
        return components_to_set

    def convert_components(self, vw_components: list[str]) -> list[str]:
        esr_components: list[str] = []
        if isinstance(vw_components, str):
            vw_components = [vw_components]

        self.logger.debug(f"Components found {len(vw_components)} {vw_components}")
        for component in vw_components:
            match component:
                case "NF ORU_Con":
                    esr_components.extend(
                        ["Functional Safety", "Online Update", "ORU Control A"]
                    )
                case "NF ZZI":
                    esr_components.append("Diagnostics VD")
                case "NF ORUOM":
                    esr_components.append("ORU OBD")
                case "NF GDC-BA":
                    esr_components.append("SWC Platform")
                case "NF TM_BASE" | "NF TM_OBD":
                    esr_components.append("TM")
                case _:
                    esr_components.append(component.removeprefix("NF "))

        self.logger.debug(
            "Components converted " f"{len(esr_components)} {esr_components}"
        )

        if not esr_components:
            esr_components = [J2J_ESR_JIRA.DEFAULT_COMPONENT]

        return esr_components
