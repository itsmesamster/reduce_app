# standard
from dataclasses import dataclass
from copy import deepcopy

# project extension
from app.ext.jira_audi.jira_issue import VwAudiJiraIssue

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger


@dataclass
class Hcp5VwAudiJiraIssue(VwAudiJiraIssue):
    logger = logger

    def split_fix_version(self, fix_version: str) -> dict:
        """
        Split fix version into version and software version.

        e.g.:
            from  "0010 (VR28.1)" to {"software": "0010", "version": "VR28"}

            from  "B450 (VR31)" to {"software": "B450", "version": "VR31"}
        """
        software_and_version = fix_version.split(" (")
        if len(software_and_version) != 2:
            self.logger.warning(
                "Something is wrong with the fix versions "
                f"for VW Audi Jira [{self.jira_id}] . ",
                vw_id=self.jira_id,
            )
            return {}

        return {
            "software": software_and_version[0],
            "version": software_and_version[1].replace(")", "").split(".")[0],
        }

    def get_versions_or_software_versions(self, select: str = "version") -> list[str]:
        """
        Get versions or software versions from fix versions.

        e.g.:
            from  "0010 (VR28.1)" to ["VR28"] or ["0010"]

            from  "B450 (VR31)" to ["VR31"] or ["B450"]
        """
        if select not in ["version", "software"]:
            self.logger.error(
                'You can only select "version" or "software"', vw_id=self.jira_id
            )
            return []
        fix_versions = deepcopy(self.fix_versions)
        if not isinstance(fix_versions, list):
            fix_versions = [fix_versions]
        versions = []
        for fix_version in fix_versions:
            v = self.split_fix_version(fix_version).get(select)
            if v:
                versions.append(v)
        return sorted(list(set(versions)))

    @property
    def versions(self) -> list[str]:
        return self.get_versions_or_software_versions(select="version")

    @property
    def software_versions(self) -> list[str]:
        return self.get_versions_or_software_versions(select="software")

    def get_components_from_title(self) -> list[str]:
        """
        Get components from Jira issue title.

        e.g.: <HVK/HVLSF> Failed Integration Tests for HVK and HVLSF

        Components are: HVK, HVLSF
        """
        title = self.summary

        if not title:
            self.logger.warning(
                f"VW Audi Jira [{self.jira_id}] has no summary (title) "
                "to get components from. ",
                vw_id=self.jira_id,
            )
            return []

        if "<" not in title and ">" not in title:
            self.logger.warning(
                f"VW Audi Jira [{self.jira_id}] has no components in title. ",
                vw_id=self.jira_id,
            )
            return []

        components = title.split(">")[0].lstrip("<").split("/")

        self.logger.debug(
            f"Found components: {components} in title: {title}", vw_id=self.jira_id
        )

        return components

    # VW Cariad Integration Jira type
    @property
    def audi_cluster_and_vr(self) -> list[str]:
        return self.get_field("customfield_48514/value")

    @property
    def audi_cluster(self) -> str:
        clusters: list[str] = []
        audi_cluster_and_vr = self.audi_cluster_and_vr or []
        for clvr in audi_cluster_and_vr:
            clvr: list[str] = clvr.split(" ")
            if len(clvr) >= 2:
                if clvr[0] == "Cluster":
                    clusters.append(" ".join(clvr))
        return clusters

    @property
    def audi_vr(self) -> list[str]:
        vrs: list[str] = []
        audi_cluster_and_vr = self.audi_cluster_and_vr or []
        for clvr in audi_cluster_and_vr:
            clvr: list[str] = clvr.split(" ")
            if len(clvr) == 3 and clvr[0] == "Cluster":
                vrs.append(clvr[2])
            elif len(clvr) >= 3 and clvr[0] == "Cluster":
                vrs.extend([vr for vr in clvr[2:] if vr.startswith("VR")])
        return list(set(vrs))
