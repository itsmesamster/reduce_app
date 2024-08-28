# standard
from math import ceil
from time import sleep, perf_counter

# 3rd party
import yaml

# project core
from app.core.custom_logger import logger
from app.core.jira.jira_utils import aggregated_tickets_link
from app.core.utils import (
    since_timestamp,
    clean_cache_dir,
    clean_reports_dir,
    performance_check,
    save_json_sync_report,
)
from app.core.processors.exceptions import SyncConditionNotMet
from app.core.core_config import APP_CACHE_DIR, APP_CACHE_HOLD_DAYS

# project extension
from app.ext.kpm_audi.kpm_client import KPMClient
from app.ext.kpm_audi.soap_responses.multiple_problem_data_response import (
    MultipleProblemDataResponse,
    ProblemReference,
)
from app.ext.kpm_audi.exceptions import KPMApiError

# project service
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import ESRLabsJiraClientForKpmSync
from app.service.hcp5.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync
from app.service.hcp5.kpm2jira.kpm2jira import SyncJiraFromKPM
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import esr_jira_client
from app.service.hcp5.kpm2jira.kpm_audi_client import kpm_client
from .config import (
    USE_KPM_SERVER,
    USE_JIRA_SERVER,
    KPM_INBOX,
    ENV,
    JIRA_SERVER_URL,
    JIRA_ID_FOR_SYNC_REPORTS,
)


class KPMJiraMainSync:
    def __init__(self):
        self.logger = logger
        self.kpm: KPMClient = None
        self.jira: ESRLabsJiraClientForKpmSync = None

    def connect(self) -> bool:
        if not self.kpm:
            if kc := kpm_client():
                self.kpm: KPMClient = kc
            else:
                logger.error(f"Failed to connect to KPM server {USE_KPM_SERVER}")
                return
        if not self.jira:
            if jc := esr_jira_client():
                self.jira: ESRLabsJiraClientForKpmSync = jc
            else:
                logger.error(f"Failed to connect to JIRA server {USE_JIRA_SERVER}")
                return
        return True

    @performance_check
    def sync_one(self, kpm_id: str):
        if not self.connect():
            self.logger.error(
                "Sync One Connection Error: Failed to connect to KPM or JIRA.",
                kpm_id=kpm_id,
            )
            return
        k2j = SyncJiraFromKPM(self.jira, self.kpm)

        # Check if user has access to KPM ticket
        if k2j.user_has_no_access_to_kpm_ticket(kpm_id):
            raise KPMApiError(f"User has no access to KPM ticket {kpm_id}")

        if not USE_KPM_SERVER == ENV.DEV:
            if not k2j.validate_plant_and_org_unit(kpm_id):
                raise SyncConditionNotMet(f"Different KPM INBOX than {KPM_INBOX}")
        jira_ticket: EsrLabsJiraIssueForKpmSync = k2j.sync_one(kpm_id)
        return jira_ticket

    @performance_check
    def sync(self, since: str = None):
        """
        Main sync function for synchronising CARIAD KPM to ESR LABS JIRA
        for multiple tickets: KPM to JIRA and JIRA to KPM sync.
        """
        start = perf_counter()

        if not since:
            since = since_timestamp()

        try:
            if not self.connect():
                self.logger.error(
                    "Sync Many Connection Error: Failed to connect to KPM or JIRA."
                )
                return

            clean_cache_dir(APP_CACHE_DIR, APP_CACHE_HOLD_DAYS)
            clean_reports_dir()

            response: MultipleProblemDataResponse = self.kpm.query(since)

            if not response:
                self.logger.error(f"Failed to get KPM issues since {since}")
                return

            kpm_issues: list[ProblemReference] = response.problem_references()
            kpm_issues.reverse()

            tickets_by_kpm_id = [ticket.problem_number for ticket in kpm_issues]

            hours_to_check = 4

            jira_tickets_found: list[
                EsrLabsJiraIssueForKpmSync
            ] = self.jira.get_tickets_with_changed_status(hours_to_check)
            question_to_oem_tickets: list[
                EsrLabsJiraIssueForKpmSync
            ] = self.jira.get_tickets_with_field_not_empty(
                "Question to OEM", hours_to_check
            )
            updated_tickets: list[
                EsrLabsJiraIssueForKpmSync
            ] = self.jira.get_tickets_updated(hours_to_check)

            jira_tickets_found.extend(question_to_oem_tickets)
            jira_tickets_found.extend(updated_tickets)

            for jira_ticket in jira_tickets_found:
                kpm_id = jira_ticket.kpm_id
                if kpm_id.isnumeric() and kpm_id not in tickets_by_kpm_id:
                    tickets_by_kpm_id.append(kpm_id)

        except KPMApiError as kpm_error:
            self.logger.error(
                "Failed to request KPM issues -> "
                f"{kpm_error.__class__.__name__} {kpm_error}"
            )
            return

        self.logger.info(
            f"\n\n\nFound {len(kpm_issues)} KPM issues changed "
            f"since: {since} for {USE_KPM_SERVER} KPM inbox:\n"
        )
        self.logger.info("-------------------------------------------------------")

        for ticket in kpm_issues:
            self.logger.info(ticket.summary)
        self.logger.info("---------------------------------------------------------\n")

        self.logger.info(
            f"\n\n\nFound {len(jira_tickets_found)} JIRA issues "
            f"with ticket status or 'Question to OEM' changed "
            f"in the last {hours_to_check} hours:\n"
        )
        self.logger.info("-------------------------------------------------------")

        for ticket in jira_tickets_found:
            self.logger.info(str(ticket).split("  API: ")[0])
        self.logger.info("---------------------------------------------------------\n")

        self.logger.debug(f"Using KPM {USE_KPM_SERVER} server: {self.kpm}")
        self.logger.debug(f"Using JIRA {USE_JIRA_SERVER} server: {self.jira}")
        self.logger.info(
            f"Will start to sync {len(tickets_by_kpm_id)} tickets KPM to JIRA "
            "(and back) in 5 seconds..."
        )
        sleep(4)

        sync_report = {"SYNCED": {}, "FAILED": {}}
        all_synced_esr_ids = []

        # TODO: aggregate sync cycle results and send email report with webpage link
        # TODO: attachments downloaded & uploaded
        # TODO: how many attachments MB / minute
        for kpm_id in tickets_by_kpm_id:
            try:
                sleep(1)

                self.logger.info(
                    "\n\n\n#################### "
                    f"Starting to sync KPM {kpm_id} "
                    "####################\n\n\n"
                )

                ########### Sync one KPM to JIRA (and back) ##############
                jira_ticket: EsrLabsJiraIssueForKpmSync = self.sync_one(kpm_id)

                if not jira_ticket:
                    err_msg = f"Failed to sync KPM {kpm_id} to JIRA."
                    self.logger.error(err_msg)
                    sync_report["FAILED"][kpm_id] = err_msg
                    continue

                sync_report["SYNCED"][kpm_id] = jira_ticket.ui_url
                self.logger.info(
                    "\n\n\n#################### "
                    f"Sync done for {jira_ticket} | KPM {kpm_id} "
                    "####################\n\n\n"
                )
                all_synced_esr_ids.append(jira_ticket.jira_id)

            except Exception as e:
                self.logger.error(f"Failed to sync issue with KPM ID [{kpm_id}] -> {e}")
                fail_reason_msg = f"{e.__class__.__name__} -> {e}"
                if the_len := len(fail_reason_msg) > 500:
                    fail_reason_msg = (
                        f"{fail_reason_msg[:500]} "
                        f"... [sliced to 500 chars of {the_len}] ..."
                    )
                sync_report["FAILED"][kpm_id] = fail_reason_msg

        sync_report["TOTAL_SYNCED"] = len(sync_report["SYNCED"])
        sync_report["TOTAL_FAILED"] = len(sync_report["FAILED"])
        sync_report["TOTAL_FOUND"] = len(tickets_by_kpm_id)
        sync_report["NOT_PROCESSED"] = list(
            set(tickets_by_kpm_id)
            - set(sync_report["SYNCED"].keys())
            - set(sync_report["FAILED"])
        )
        duration = ceil(int(perf_counter() - start) / 60)
        sync_report["DURATION"] = f"{duration} minutes"

        yaml_sync_report = f"Sync report:\n{yaml.safe_dump(sync_report, width=200)}"
        self.logger.info(yaml_sync_report)

        if USE_JIRA_SERVER == ENV.DEV:
            report_filename = f"{USE_JIRA_SERVER}_in_{duration}_mins"
        else:
            report_filename = f"in_{duration}_mins"
        save_json_sync_report(sync_report, report_filename)

        all_jiras_link = aggregated_tickets_link(JIRA_SERVER_URL, all_synced_esr_ids)

        try:
            self.jira.post_sync_report(
                JIRA_ID_FOR_SYNC_REPORTS,
                sync_report,
                f"[All Synced tickets|{all_jiras_link}]",
            )
        except Exception as e:
            self.logger.error(
                "Failed to Post Sync Report to Jira server: "
                f"{e.__class__.__name__} -> {e}"
            )

        # TODO: move sync report logic to separate method
