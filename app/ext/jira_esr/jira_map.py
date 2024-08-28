# standard
from functools import cache
from dataclasses import dataclass, asdict

# 3rd party
import yaml

# project core
from app.core.custom_logger import logger
from app.core.jira.jira_map import JiraFieldsMapCore, ExtraFieldsMapCore

# project extension
from app.ext.jira_esr.config import DEFAULT_ESR_JIRA_CLUSTER_MAP_YML


@dataclass(frozen=True)
class EsrLabsAhcp5JiraFieldMap(JiraFieldsMapCore):
    """Jira fields mapping from UI representation to Jira internal representation."""

    # JIRA JQL custom field use e.g.:
    #       CORRECT:    cf[10503] ~ 9045195
    #                   "External Reference" ~ 9045195 (KPM ID)
    #       WRONG:      customfield_10503 = "9045195"

    external_reference: str = "customfield_10503"  # this is the KPM problem ID
    audi_cluster: str = "customfield_12600"
    origin: str = "customfield_12640"
    audi_vr: str = "customfield_12740"
    teams: str = "customfield_12733"

    @dataclass(frozen=True)
    class EsrLabsAhcp5ExtraFieldsMap(ExtraFieldsMapCore):
        """Jira custom fields mapping from UI representation
        to Jira internal representation."""

        feedback_to_oem: str = "customfield_12743"
        feedback_from_oem: str = "customfield_12742"
        question_to_oem: str = "customfield_12759"
        answer_from_oem: str = "customfield_12760"
        cause_of_reject: str = "customfield_12713"

    @property
    def extras(self) -> EsrLabsAhcp5ExtraFieldsMap:
        return self.EsrLabsAhcp5ExtraFieldsMap()

    def __repr__(self) -> str:
        dc = asdict(self)
        dc["extras"] = asdict(self.extras)
        return str(dc)


# @cache
class ClusterMap:
    def __init__(self, cluster_map_path: str = None) -> None:
        self.logger = logger
        self.cluster_map_path = cluster_map_path or DEFAULT_ESR_JIRA_CLUSTER_MAP_YML
        self.__map: dict = None

    def _load_map(self) -> dict:
        if self.cluster_map_path.split(".")[-1] not in ["yaml", "yml"]:
            self.logger.error(
                f"Cluster map file must be yaml file: {self.cluster_map_path}"
            )
            return {}
        try:
            with open(self.cluster_map_path) as f:
                load: dict = yaml.safe_load(f)
                if not load:
                    self.logger.error(
                        f"Cluster map file is empty: {self.cluster_map_path}"
                    )
                else:
                    self.logger.debug(
                        f"Cluster map file loaded -> {self.cluster_map_path} : "
                        f"\n{yaml.safe_dump(load)}"
                    )
                return load
        except Exception as e:
            self.logger.error(
                f"Failed to load cluster map file: {self.cluster_map_path} : {e}"
            )

    @property
    def map_dict(self) -> dict:
        if not self.__map:
            self.__map = self._load_map()
        return self.__map

    @cache
    def get_clvr(self, software_or_version: str) -> dict:
        """Get cluster and Version from software name."""
        if software_or_version is None:
            return {}
        clusters_ver = []
        pre = False  # is pre-release software ?
        if len(software_or_version) == 4 and software_or_version[2] == "E":
            pre = True
            pre_sv = software_or_version[:2]

        def loop(map_dl: dict | list = self.map_dict, path=""):
            if isinstance(map_dl, dict):
                for k, v in map_dl.items():
                    if p := loop(v, f"{path}/{k}"):
                        return p
                    elif k == software_or_version:
                        clusters_ver.append(path.lstrip("/"))
            elif isinstance(map_dl, list):
                sv = software_or_version
                if not pre and sv in map_dl:
                    clusters_ver.append(path.lstrip("/"))
                if pre and pre_sv in [x[:2] for x in map_dl]:
                    clusters_ver.append(path.lstrip("/"))

        loop()

        if not clusters_ver:
            self.logger.error(
                f"Failed to find cluster (and version) for {software_or_version}"
            )
            return {}

        cluster_and_version = {"cluster": [], "version": []}
        for clvr in clusters_ver:
            clvr = clvr.split("/")
            if len(clvr) == 2:
                cluster_and_version["cluster"].append(clvr[0])
                cluster_and_version["version"].append(clvr[1])
            elif len(clvr) == 1:
                cluster_and_version["version"].append(clvr[0])

        return cluster_and_version

    def get_clusters(self, software_or_version: str, default: str = "-") -> list[str]:
        self.logger.debug("getting cluster name " f"for version: {software_or_version}")
        return self.get_clvr(software_or_version).get("cluster", [default])

    def get_versions(self, software: str) -> list[str]:
        versions = self.get_clvr(software).get("version", [])
        return versions

    def get_audi_clusters(
        self,
        software_versions: list[str],
        fix_versions: list[str],
        default_audi_cluster: str = "-",
        esr_jira_id: str = "",
        other_ticket_id: str = "",
    ) -> list[str]:
        software_and_or_versions = software_versions + fix_versions
        clusters: list[str] = []

        self.logger.debug(
            f"Software and/or versions: {software_and_or_versions}",
            jira_id=esr_jira_id,
            kpm_id=other_ticket_id,
        )

        if not software_and_or_versions:
            return [default_audi_cluster]

        for sftw_or_ver in software_and_or_versions:
            if cluster_name := self.get_clusters(sftw_or_ver):
                clusters.extend(cluster_name)

        if not clusters:
            return [default_audi_cluster]

        clusters = set(clusters)
        if len(clusters) > 1 and "-" in clusters:
            clusters.remove("-")

        return sorted(list(clusters))
