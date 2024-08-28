# standard
from math import ceil
from time import sleep, perf_counter

# 3rd party
import yaml

# project core
from app.core.utils import performance_check
from app.core.jira.jira_utils import aggregated_tickets_link

# project extension
from app.ext.jira_esr.jira_client import ESRLabsJiraClient
from app.ext.jira_audi.jira_client import VwAudiJiraClient

# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.jira_issue_vwaudi import Hcp5VwAudiJiraIssue
from app.service.hcp5.jira2jira.jira_issue_esr4vw import EsrIssueForVwJiraSync
from app.service.hcp5.jira2jira.jira2jira_vw2esr import SyncHCP5JiraEsrFromJiraVwAudi
from app.service.hcp5.jira2jira.sync_exceptions import JiraIssueTypeNotAcceptedForSync
from app.service.hcp5.jira2jira.jira_client_esr_j2j import j2j_esr_jira_client
from app.service.hcp5.jira2jira.jira_client_vwaudi import j2j_vw_jira_client
from app.service.hcp5.jira2jira.config import (
    J2J_ESR_JIRA,
    J2J_ESR_USE_JIRA_SERVER,
    J2J_VW_USE_JIRA_SERVER,
    MAPPER_BY_ISSUE_TYPE,
    VW_JQL,
)


VW_JIRA_ISSUE_TYPES_TO_SYNC = list(MAPPER_BY_ISSUE_TYPE.keys())


class HCP5JiraJiraMainSync:
    def __init__(self):
        self.logger = logger
        self.esr_jira: ESRLabsJiraClient = None
        self.vw_jira: VwAudiJiraClient = None

    def connect(self) -> bool:
        if not self.esr_jira:
            if esrc := j2j_esr_jira_client():
                self.esr_jira: ESRLabsJiraClient = esrc
            else:
                logger.error(
                    f"Failed to connect to ESR JIRA server {J2J_ESR_USE_JIRA_SERVER}"
                )
                return
        if not self.vw_jira:
            if vwc := j2j_vw_jira_client():
                self.vw_jira: VwAudiJiraClient = vwc
            else:
                logger.error(
                    f"Failed to connect to VW/Audi server {J2J_VW_USE_JIRA_SERVER}"
                )
                return
        return True

    @performance_check
    def sync_one(self, vw_id: str) -> EsrIssueForVwJiraSync | None:
        if not self.connect():
            self.logger.error(
                '"Sync One" Connection Error: Failed to connect to VW or ESR JIRA.'
            )
            return

        vw_jira_to_esr_jira = SyncHCP5JiraEsrFromJiraVwAudi(
            esr_jira_client=self.esr_jira, vw_jira_client=self.vw_jira
        )

        esr_ticket: EsrIssueForVwJiraSync = vw_jira_to_esr_jira.sync_one(vw_id)
        return esr_ticket

    @performance_check
    def sync(self, since: str = None):
        """
        Main sync function for synchronising CARIAD KPM to ESR LABS JIRA
        for multiple tickets: KPM to JIRA and JIRA to KPM sync.
        """
        start = perf_counter()
        sync_report = {"SYNCED": {}, "FAILED": {}, "TOTAL_FOUND": 0}
        all_synced_esr_ids = []
        try:
            if not self.connect():
                self.logger.error(
                    '"Sync One" Connection Error: Failed to connect to VW or ESR JIRA.'
                )
                return

            vw_tickets: dict[str : list[Hcp5VwAudiJiraIssue]] = {}

            vw_tickets["TASK"]: list[
                Hcp5VwAudiJiraIssue  # type: ignore
            ] = self.vw_jira.query(VW_JQL["TASK"])

            vw_tickets["INTEGRATION"]: list[
                Hcp5VwAudiJiraIssue  # type: ignore
            ] = self.vw_jira.query(VW_JQL["INTEGRATION"])

            sync_report["TOTAL_FOUND"] = len(
                [t for ts in vw_tickets.values() for t in ts]
            )

            self.logger.info(
                f"\n\nFound {sync_report['TOTAL_FOUND']} VW Jira issues to be synced: "
            )
            for ticket_type, vw_tickets_list in vw_tickets.items():
                print(f"{ticket_type}:")
                for vw_ticket in vw_tickets_list:
                    vw_ticket: Hcp5VwAudiJiraIssue = vw_ticket
                    print(f"\t\t{vw_ticket.info}")

            self.logger.info(
                "\n\n\nWill start to sync VW/Audi Jira issues "
                "to ESR Labs Jira in 5 seconds..."
            )
            sleep(2)
        except Exception as e:
            self.logger.error(f"Sync Cycle FAILED:\n{e}")

        for ticket_type, vw_tickets_list in vw_tickets.items():
            for vw_ticket in vw_tickets_list:
                try:
                    sleep(1)
                    if vw_ticket.issue_type not in VW_JIRA_ISSUE_TYPES_TO_SYNC:
                        msg = (
                            f'Type {vw_ticket.issue_type} not in the "To Sync" list'
                            f" {VW_JIRA_ISSUE_TYPES_TO_SYNC}"
                        )
                        self.logger.warning(
                            f"Skipping VW issue {vw_ticket.info} -> " f"{msg}"
                        )
                        raise JiraIssueTypeNotAcceptedForSync(msg)

                    self.logger.info(
                        "\n\n\n#################### Starting to sync VW Jira ID "
                        f"{vw_ticket.info} ####################\n\n\n"
                    )
                    ###### MAIN SYNC ENTRY POINT FOR SYNCING ONE ######
                    esr_ticket: EsrIssueForVwJiraSync = self.sync_one(vw_ticket.jira_id)

                    if esr_ticket:
                        self.logger.info(
                            "\n\n\n#################### Sync done for VW Jira ID "
                            f"{esr_ticket.info} ####################\n\n\n"
                        )
                    else:
                        self.logger.error(f"Failed to sync VW ticket: {vw_ticket.info}")
                        sync_report["FAILED"][vw_ticket.jira_id] = (
                            f"No ESR ticket returned from the sync - please check "
                            f"{self.__class__.__name__}.sync_one() code flow"
                        )
                        continue
                    if not sync_report["SYNCED"].get(ticket_type):
                        sync_report["SYNCED"][ticket_type] = {}
                    sync_report["SYNCED"][ticket_type][
                        vw_ticket.ui_url
                    ] = esr_ticket.ui_url
                    all_synced_esr_ids.append(esr_ticket.esr_id)

                except Exception as e:
                    if not sync_report["FAILED"].get(ticket_type):
                        sync_report["FAILED"][ticket_type] = {}
                    sync_report["FAILED"][ticket_type][vw_ticket.jira_id] = f"{e}"

        total_synced = len(all_synced_esr_ids)
        sync_report["TOTAL_SYNCED"] = total_synced
        sync_report["TOTAL_FAILED"] = sync_report["TOTAL_FOUND"] - total_synced

        duration = ceil(int(perf_counter() - start) / 60)
        sync_report["DURATION"] = f"{duration} minutes"

        self.logger.info(f"Sync report:\n{yaml.safe_dump(sync_report, width=200)}")

        all_jiras_link = aggregated_tickets_link(
            J2J_ESR_JIRA.server, all_synced_esr_ids
        )

        self.esr_jira.post_sync_report(
            J2J_ESR_JIRA.sync_reports_jira_id,
            sync_report,
            f"[All Synced tickets|{all_jiras_link}]",
        )
