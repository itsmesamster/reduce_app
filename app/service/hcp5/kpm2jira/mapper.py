import json

# proect core
from app.core.custom_logger import logger

# project extension
from app.ext.kpm_audi.soap_responses.development_problem_data_response import (
    DevelopmentProblemDataResponse,
)
from app.ext.jira_esr.jira_map import ClusterMap
from app.ext.jira_esr.jira_map import EsrLabsAhcp5JiraFieldMap as EsrFields

# project service
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import ESRLabsJiraClientForKpmSync
from app.service.hcp5.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync
from app.service.hcp5.kpm2jira.config import (
    JIRA_ACCOUNT_ID,
    JIRA_PROJECT_KEY,
    CONFIG_DIR,
    USE_JIRA_SERVER,
    ENV,
)


K2J_JSON_FIELD_MAP = f"{CONFIG_DIR}/k2j_field_map.json"
DEFAULT_DEV_CLUSTER = "Cluster 4.3"


class Mapper:
    def __init__(
        self,
        jira_client: ESRLabsJiraClientForKpmSync,
        field_map_file: str = K2J_JSON_FIELD_MAP,
        cluster_map_file: str = None,
    ):
        """
        Represents Mapper class.
        """
        self.path = field_map_file
        self.data: dict = {}
        self.logger = logger
        self.jira: ESRLabsJiraClientForKpmSync = jira_client
        if cluster_map_file:
            self.cluster_map: ClusterMap = ClusterMap(cluster_map_file)
        else:
            self.cluster_map: ClusterMap = ClusterMap()

        try:
            with open(self.path) as f:
                self.data = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load mapper file: {self.path}", e=e)

    # TODO: make the mapper more pythonic
    def _mapper_to_jira(self, kpm_ticket: DevelopmentProblemDataResponse):
        """
        Converts KPM ticket into Jira ticket.
        """
        kpm_id = kpm_ticket.kpm_id
        kpm_ticket: dict = kpm_ticket.development_problem_as_dict().get(
            "DevelopmentProblem"
        )
        jira_issue = EsrLabsJiraIssueForKpmSync()
        jira_issue_map: dict = self.data["jira_issue"]
        # self.logger.debug(f'Jira Issue Map:\n{jira_issue_map}')
        jira_priority_map: dict = self.data["priority"]
        jira_reproducibility_map: dict = self.data["reproducibility"]

        foremost_test_part: dict = kpm_ticket.get("ForemostTestPart", {})
        self.logger.debug(f"KPM {kpm_id} ForemostTestPart {foremost_test_part=}")
        software = foremost_test_part.get("Software")

        for k in jira_issue_map.keys():
            v: str = self.data["jira_issue"][k]
            if "?" not in v:
                if v == "##cluster_mapping_based_on_software_version##":
                    clusters = self.cluster_map.get_clusters(software)
                    if USE_JIRA_SERVER == ENV.DEV:
                        clusters = self.cluster_map.get_clusters(
                            software, DEFAULT_DEV_CLUSTER
                        )
                        self.logger.warning(
                            "DEV JIRA server: "
                            "Using DUMMY cluster as cluster mapping returned empty."
                        )
                    if not clusters:
                        self.logger.error(
                            f"Cluster not found for software version {software}"
                        )
                    set_clusters = []
                    for cluster in clusters:
                        set_clusters.append({"value": cluster})

                    # dummy value "-" hardcoded value if cluster mapped value
                    # not found for software version as
                    # cluster field is mandatory -> will not sync without
                    if not set_clusters:
                        set_clusters.append({"value": "-"})
                    # TODO: remove this after fixing the cluster mapping to be
                    # taken directly from jira (if possible)

                    jira_issue.set_field(k, set_clusters)
                elif jira_issue.set_field(k, v):
                    self.logger.debug(f"Added [{v}] to field [{k}]")  # , kpm_id=kpm_id)
            else:
                v = v.rstrip("?")
                kpm_ticket_v = kpm_ticket.get(v, "")
                if v in ["Description", "ProblemNumber", "Exclaimer"]:
                    jira_issue.set_field(k, kpm_ticket_v)
                elif v == "ShortText":
                    jira_issue.set_field(k, kpm_ticket_v)
                elif v == "Rating":
                    # self.logger.debug(f"Jira Priority Map:\n{jira_priority_map}")
                    name = jira_priority_map.get(str(kpm_ticket_v), "")
                    jira_issue.set_field(k, {"name": name})
                elif v == "Function":
                    jira_issue.set_field(k, [{"name": "Unknown"}])
                elif v == "Software":
                    # set "Affects Versions"
                    # field can't be set if the version doesn't exist in Jira
                    # "errors":{"versions":"Version name '0018-RC2' is not valid"}}
                    jira_available_versions = self.jira.available_versions(
                        JIRA_PROJECT_KEY
                    )
                    if software and software in jira_available_versions:
                        jira_issue.set_field(k, [{"name": software}])
                    else:
                        # field is mandatoy, so we set it to "-"
                        if "-" not in jira_available_versions:
                            self.logger.error(
                                f'Version "-" not found in the versions names '
                                f"list for Jira Project {JIRA_PROJECT_KEY}"
                            )
                        jira_issue.set_field(k, [{"name": "-"}])
                    self.logger.debug(f'{jira_issue.fields["versions"]=}')
                elif v == "Hardware":
                    # Set default for jira ticket field hardware to "-"
                    kpm_ticket_hardware = foremost_test_part.get("Hardware", "-")
                    jira_issue.set_field(k, kpm_ticket_hardware)
                elif v == "Reproducibility":
                    repeatable: str = kpm_ticket.get("Repeatable", {})
                    reproducibility: str = jira_reproducibility_map.get(
                        repeatable, "03 - Frequent"
                    )
                    jira_issue.set_field(k, {"value": reproducibility})
                elif v == "VerbundRelease":
                    if "VerbundRelease" not in kpm_ticket:
                        jira_issue.set_field(k, [{"value": "VR000"}])
                    else:
                        vr = ""
                        if kpm_ticket_v["Major"] != "00":
                            vr = f"VR{kpm_ticket_v['Major']}"
                        # TODO: remove next line .cluster_map.get_versions(software)
                        # available_vrs = self.cluster_map.get_versions(software)
                        available_vrs = self.jira.get_field_allowed_values(
                            EsrFields.audi_vr
                        )
                        if vr and vr not in available_vrs:
                            self.logger.error(
                                f"KPM {kpm_id} VerbundRelease {vr} not found in "
                                f"the versions names list for software {software}"
                            )
                            vr = "-"
                        if vr and vr in available_vrs and len(available_vrs) > 1:
                            self.logger.warning(
                                f"KPM {kpm_id} VerbundRelease {vr} was found in "
                                f"the versions names list for software {software}, "
                                f"but there are more available versions in the "
                                f"jira map: {available_vrs}"
                            )
                        # set Audi VR / customfield_12740 (ESR Jira)
                        # if Audi VR value in jira fields available options
                        #       -> set it, else "-"
                        vr = vr or "-"
                        jira_issue.set_field(k, [{"value": vr}])

                elif v == "PartNumber":
                    part_number = [
                        kpm_ticket["ForemostTestPart"]["PartNumber"]["PreNumber"],
                        kpm_ticket["ForemostTestPart"]["PartNumber"]["MiddleGroup"],
                        kpm_ticket["ForemostTestPart"]["PartNumber"]["EndNumber"],
                        kpm_ticket["ForemostTestPart"]["PartNumber"]["Index"],
                        kpm_ticket["ForemostTestPart"]["PartNumber"]["Charge"],
                        kpm_ticket["ForemostTestPart"]["PartNumber"][
                            "ChargeSerialNumber"
                        ],
                    ]

                    value = ""
                    for prop in part_number:
                        if prop:
                            value += prop

                    jira_issue.set_field(k, value)
                elif v == "AccountID":
                    jira_issue.set_field(k, {"accountId": JIRA_ACCOUNT_ID})
        return jira_issue

    def to_jira(
        self, kpm_ticket: DevelopmentProblemDataResponse
    ) -> EsrLabsJiraIssueForKpmSync:
        kpm_id = kpm_ticket.kpm_id
        self.logger.info(f"Converting KPM [{kpm_id}] to Jira ... ", kpm_id=kpm_id)

        jira_converted_ticket = self._mapper_to_jira(kpm_ticket)

        yml = jira_converted_ticket.get_all_fields_as_yaml()
        if jira_converted_ticket.output_ok():
            self.logger.debug(f"KPM TICKET {kpm_id} READY FOR JIRA: {yml}")
        else:
            self.logger.debug("TICKET READY FOR JIRA.", kpm_id=kpm_id)
        return jira_converted_ticket


# """
# KPM TICKET 9137474 READY FOR JIRA:
# assignee:
#   accountId: 63f87279c1f7acaf636ce8a9
# components:
# - name: Unknown
# customfield_10500: X23
# customfield_10501:
#   value: 03 - Frequent
# customfield_10503: '9137474'
# customfield_10900: Okunneck, Christian (N/P3-M31)
# customfield_12600:
# - value: Cluster 4.3
# customfield_12640:
#   value: Audi KPM
# customfield_12740:
# - value: VR21
# customfield_12748: 85F907468A
# description: "mit der UPS Pr\xFCftechnik (Siemens) ist es momentan nicht m\xF6glich
#  eine DoIP Verbindung zum HCP5 aufbauen. \nSomit ben\xF6tigen wir in der Produktion
#  immens mehr Zeit an den einzelnen Pr\xFCforten f\xFCr die IBN und auch einzelne
#  Steuerger\xE4te k\xF6nnen gar nicht bedatet werden."
# issuetype: Customer Issue
# priority:
#   name: Major
# project: AHCP5
# summary: "[K][ESR]DoIP Verbindungsaufbau HCP5nicht m\xF6glich"
# versions:
# - name: M414
# """
