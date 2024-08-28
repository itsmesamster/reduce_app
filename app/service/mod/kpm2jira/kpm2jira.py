# standard
from datetime import datetime, timedelta

# external
from jira import Issue
from jira.exceptions import JIRAError

# project core
from app.core.custom_logger import logger
from app.core.processors.exceptions import SyncConditionNotMet
from app.core.utils import clean_str, clean_str_list, timed_cache

# project extension
from app.ext.kpm_audi.kpm_client import KPMClient, ALREADY_POSTED
from app.ext.kpm_audi.soap_responses.development_problem_data_response import (
    DevelopmentProblemDataResponse,
)
from app.ext.kpm_audi.soap_responses.process_steps_response import (
    ProcessStepListResponse,
    ProcessStepResponse,
)
from app.ext.kpm_audi.exceptions import KpmResponseError

# project service
from app.service.mod.kpm2jira.jira_esr_client_k2j import ESRLabsJiraClientForKpmSync
from app.service.mod.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync
from app.service.mod.kpm2jira.mapper import Mapper
from app.service.mod.kpm2jira.config.jira2kpm_status_map import (
    JiraToKpmStatuses,
    KpmStatus,
)
from .config import (
    JIRA_ISSUE_PREFIX,
    K2J_KPM_SUPPLIER_CONTRACTOR_PATH,
    K2J_KPM_SUPPLIER_CONTRACTOR_IDS,
    K2J_KPM_CLOSED_STATUS_IDS,
    ORG_UNIT_KEY,
    ORG_UNIT_VAL,
    KPM_INBOX,
    PLANT_KEY,
    PLANT_VAL,
    INBOX_CHECKS,
    STATUSES_THAT_NEED_QUESTION_TO_OEM,
)


NO_KPM_ACCESS_JIRA_COMMENT = "No access in KPM"


class BaseSync:
    def __init__(
        self,
        jira_client: ESRLabsJiraClientForKpmSync,
        kpm_client: KPMClient,
        mapper: Mapper = None,
    ):
        self.logger = logger
        self.jira: ESRLabsJiraClientForKpmSync = jira_client
        self.kpm: KPMClient = kpm_client
        self.map: Mapper = mapper if mapper else Mapper(self.jira)


class NewJiraFromKPM(BaseSync):
    """Logic and steps to create a new jira issue from an existing kpm issue.

    KPM -> Jira (most of the methods)

    Jira -> KPM (only for kpm.add_supplier_response)
    """

    def __init__(
        self,
        jira_client: ESRLabsJiraClientForKpmSync,
        kpm_client: KPMClient,
        mapper: Mapper = None,
    ):
        super().__init__(jira_client, kpm_client, mapper)

    def field_matches(
        self,
        kpm_ticket: DevelopmentProblemDataResponse,
        kpm_id: str,
        field_path: str,
        data_to_match: list[str] | str = "",
        msg: str = "",
    ) -> bool | None:
        """It checks the inner filed data of a dict by providing:
        ticket: kpm_ticket in the form of a dict
        filed_path: DevelopmentProblem/Supplier/Contractor/PersonalContractor/UserId
        data_to_match: in the form of a list of strings or single str

        return: True or None
        """
        ticket = kpm_ticket.development_problem_as_dict()
        if not isinstance(ticket, dict):
            self.logger.error("Please pass ticket as dict here.")
            return
        try:
            self.logger.debug(
                f"Splitting [{field_path}] inner dict path "
                f"to look for {data_to_match}",
                kpm_id=kpm_id,
            )
        except (ValueError, KeyError, IndexError):
            self.logger.debug(
                f"KPM ID {kpm_id} Splitting [{field_path}] inner dict path "
            )
        inner_keys_path = field_path.split("/")
        val = ticket
        for key in inner_keys_path:
            val = val.get(key, {})
        if val and (val in data_to_match):
            try:
                self.logger.debug(
                    f"{field_path}: {val} matches {data_to_match}", kpm_id=kpm_id
                )
            except (ValueError, KeyError, IndexError):
                self.logger.debug(f"{field_path}: {val} match.")
            return True
        if val and not data_to_match:
            self.logger.debug(f"{field_path} exists. Value {val}", kpm_id=kpm_id)
            return True
        if not val:
            val = ""
        try:
            self.logger.error(
                f"{field_path}: {val} not in {data_to_match}. {msg}", kpm_id=kpm_id
            )
        except Exception:
            self.logger.error(
                f"KPM ID {kpm_id} {field_path}: {val} not in {data_to_match}. {msg}"
            )

    @timed_cache
    def validate_plant_and_org_unit(self, kpm_id: str):
        """Check if KPM["OrganisationalUnit"] and KPM["Plant"] are in the list of
        allowed values."""
        self.logger.info("Checking OrganisationalUnit and Plant ", kpm_id=kpm_id)
        kpm_ticket = self.kpm.issue(kpm_id)
        if not kpm_ticket:
            self.logger.warning(
                f"Not a valid DevelopmentProblem for KPM ID {kpm_id}", kpm_id=kpm_id
            )
            return
        for path in INBOX_CHECKS:
            org_path = f"{path}/{ORG_UNIT_KEY}"
            plant_path = f"{path}/{PLANT_KEY}"
            if not self.field_matches(
                kpm_ticket, kpm_id, org_path, ORG_UNIT_VAL
            ) or not self.field_matches(kpm_ticket, kpm_id, plant_path, PLANT_VAL):
                self.logger.warning(
                    f"Different KPM INBOX than {KPM_INBOX}", kpm_id=kpm_id
                )
                return
        self.logger.info(
            f"All OrganisationalUnit and Plant values are matching {KPM_INBOX}",
            kpm_id=kpm_id,
        )
        return True

    def meets_conditions(self, kpm_ticket: DevelopmentProblemDataResponse, kpm_id: str):
        """Conditions for the ticket to be synced from KPM to JIRA"""
        # 1. if KPM["Supplier"]["Contractor"]["PersonalContractor"]["UserId"]
        #                not in ESR Labs user list e.g. ("D962178", "D16902F")
        #                       -> Ignore, not assigned to ESR
        if not self.field_matches(
            kpm_ticket,
            kpm_id,
            K2J_KPM_SUPPLIER_CONTRACTOR_PATH,
            K2J_KPM_SUPPLIER_CONTRACTOR_IDS,
        ):
            warning_msg = "KPM Supplier User missing or not an ESR Labs User"
            self.logger.warning(f"❌ {warning_msg}", kpm_id=kpm_id)
            raise SyncConditionNotMet(warning_msg)
        self.logger.info(
            "✅ SYNC CONDITION MET: KPM Supplier -> ESR Labs User", kpm_id=kpm_id
        )

        # 2. KPM["ProblemStatus"] in ("5", "6") -> Ignore, ticket already closed
        status = kpm_ticket.problem_status
        warning_msg = f"Ignoring, KPM ticket already closed [{status}]"
        if status in K2J_KPM_CLOSED_STATUS_IDS:
            self.logger.warning(f"❌ {warning_msg}", kpm_id=kpm_id)
            raise SyncConditionNotMet(warning_msg)
        self.logger.info(
            f"✅ SYNC CONDITION MET: KPM ProblemStatus ({status}) "
            f"not in {K2J_KPM_CLOSED_STATUS_IDS} "
            "-> Ticket not Closed",
            kpm_id=kpm_id,
        )

        # 3. Check unless KPM["SupplierStatus"] exists -> Ignore, must be set
        kpm_supplier_status = kpm_ticket.supplier_status
        warning_msg = "KPM SupplierStatus not set."
        if not kpm_supplier_status:
            self.logger.warning(f"❌ {warning_msg}", kpm_id=kpm_id)
            raise SyncConditionNotMet(warning_msg)
        self.logger.info(
            f"✅ SYNC CONDITION MET: KPM SupplierStatus ({kpm_supplier_status}) exists",
            kpm_id=kpm_id,
        )

        return True

    @timed_cache
    def add_issue(self, kpm_id: str) -> EsrLabsJiraIssueForKpmSync | None:  # to JIRA
        """Create new Jira issue from existing KPM ID...
        OR get existing Jira issue if already present."""
        self.logger.info(
            f"Create new Jira issue from KPM issue: {kpm_id} ... "
            f"OR get existing one if already present",
            kpm_id=kpm_id,
        )

        # 1. Check Jira for existing KPM ID (External Reference) in issue/ticket
        if jira_issue := self.jira.ticket_already_present(kpm_id=kpm_id):
            return jira_issue

        # 2. Fetch issue / ticket / development problem from KPM
        kpm_ticket = self.kpm.issue(kpm_id)
        if not kpm_ticket:
            self.logger.debug(
                f"Not a valid DevelopmentProblem for KPM ID {kpm_id}", kpm_id=kpm_id
            )
            return

        kpm_ticket.log_output_as_yaml()

        # 3. Conditions for KPM ticket to be synced from KPM to JIRA or not
        if not self.meets_conditions(kpm_ticket, kpm_id):
            return
        self.logger.info(
            f"KPM ID {kpm_id} meets all conditions to be added to JIRA ... ",
            kpm_id=kpm_id,
        )

        # 4. Convert KPM ticket to Jira ticket
        ticket_ready_for_jira = self.map.to_jira(kpm_ticket)

        # 5. Add newly created issue to JIRA
        try:
            jira_response = self.jira.add_ticket(ticket_ready_for_jira)
            if isinstance(jira_response, Issue):
                self.logger.debug(
                    f"Created new Jira issue with ID: {jira_response.key}"
                )
            else:
                self.logger.error("Failed to create new Jira issue", kpm_id=kpm_id)
                return
        except JIRAError as e:
            err_msg = f"Failed to create new Jira issue for KPM ID {kpm_id}: {e}"
            self.logger.error(err_msg)
            raise JIRAError(err_msg)

        if jira_issue := self.jira.issue_by_kpm_id(kpm_id):
            self.logger.info(
                f"Successfully created {jira_response} for KPM ID {kpm_id}",
                kpm_id=kpm_id,
                jira_id=jira_issue.jira_id,
            )
        else:
            err_msg = f"Failed to create new Jira issue for KPM ID {kpm_id}"
            self.logger.error(err_msg, kpm_id=kpm_id)
            raise JIRAError(err_msg)

        # KPM -> JIRA
        # 6. ADD supplier response (post JIRA ID to KPM)
        created_supl_resp = self.add_creation_supplier_response(
            kpm_id, jira_issue.jira_id
        )
        if not created_supl_resp:
            err_msg = "Failed to add supplier response"
            self.logger.error(err_msg, kpm_id=kpm_id)
            raise KpmResponseError(err_msg)

        return jira_issue

    # JIRA -> KPM
    def add_supplier_response(
        self, kpm_id: str, jira_id: str, status_number: str, msg: str
    ):
        msg = f"{datetime.now().strftime('%d.%m.%Y')}: {msg}"
        if self.validate_plant_and_org_unit(kpm_id):
            return self.kpm.post_supplier_response(kpm_id, jira_id, status_number, msg)

    # JIRA -> KPM
    def add_creation_supplier_response(self, kpm_id: str, jira_id: str):
        self.logger.info(
            "Will add supplier response to KPM after ticket creation in JIRA ... ",
            kpm_id=kpm_id,
            jira_id=jira_id,
        )
        new_status = JiraToKpmStatuses.OPEN
        status = new_status.status
        msg = new_status.comment
        if self.validate_plant_and_org_unit(kpm_id):
            return self.add_supplier_response(kpm_id, jira_id, status, msg)


class SyncJiraFromKPM(NewJiraFromKPM):
    """Logic and steps to sync a existing jira issue from an existing kpm issue.

    KPM -> Jira (most of the methods)

    Jira -> KPM (only for kpm.post_supplier_question (question to oem) + status changed)
    """

    def __init__(
        self,
        jira_client: ESRLabsJiraClientForKpmSync,
        kpm_client: KPMClient,
        mapper: Mapper = None,
    ):
        super().__init__(jira_client, kpm_client, mapper)

    def jira_substeps_len(self, step: str) -> int:
        """Return the length of the process substep in Jira."""
        if not step:
            return 0
        # make SPLIT_BY consistent with process_steps_response.for_jira_ui method
        SPLIT_BY = "\n\n 📆 \t "
        return len(step.strip("\n\n").split(SPLIT_BY))

    # KPM -> Jira
    # Handle "Feedback to OEM":
    # TODO: merge with _add_feedback_from_oem and _add_answer_from_oem
    def _add_feedback_to_oem(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync,
        process_step_list: ProcessStepListResponse,
    ):
        # select all process steps where
        # step['ProcessStepTypeDescription'] == "Lieferantenaussage"
        ALLOWED_LIMIT = 32767  # characters
        self.logger.info("Checking [Feedback to OEM] ... ", kpm_id=jira_issue.kpm_id)
        jira_substep_len = self.jira_substeps_len(jira_issue.feedback_to_oem)
        if jira_substep_len == len(process_step_list.feedback_to_oem_step_list):
            self.logger.info(
                "Jira [Feedback to OEM] same as in KPM (same number "
                "of process steps / comments). Nothing to do.",
                kpm_id=jira_issue.kpm_id,
                jira_id=jira_issue.jira_id,
            )
            return

        # set feedback to oem to jira issue
        all_feedback_to_oem: str = ""
        feedback_steps_to_post = 0
        kpm_feedback_steps_len = len(process_step_list.feedback_to_oem_step_list)

        for i, process_step in enumerate(process_step_list.feedback_to_oem_step_list):
            step_response_details: ProcessStepResponse = self.kpm.process_step(
                process_step.problem_number, process_step.step_id
            )
            if not step_response_details:
                self.logger.error(
                    f"Failed to get process step {process_step.step_id} ",
                    kpm_id=process_step.problem_number,
                )
                continue

            kpm_step_for_jira_ui = step_response_details.for_jira_ui
            if i == 0 and jira_issue.feedback_to_oem:
                jira_feedback_first_chars = jira_issue.feedback_to_oem.split("\n\n")[0]
                kpm_step_first_chars = kpm_step_for_jira_ui.split("\n\n")[0]

                if jira_feedback_first_chars == kpm_step_first_chars:
                    self.logger.info(
                        "Jira [Feedback to OEM] same as in KPM (same first "
                        "step / comment). Nothing to do.",
                        kpm_id=jira_issue.kpm_id,
                        jira_id=jira_issue.jira_id,
                    )
                    return
                else:
                    self.logger.info(
                        "Jira [Feedback to OEM] different than in KPM. Will update.",
                        kpm_id=jira_issue.kpm_id,
                        jira_id=jira_issue.jira_id,
                    )

            if len(all_feedback_to_oem) + len(kpm_step_for_jira_ui) < ALLOWED_LIMIT:
                all_feedback_to_oem += kpm_step_for_jira_ui
                feedback_steps_to_post += 1
            else:
                self.logger.warning(
                    f"KPM ID {jira_issue.kpm_id} Feedback to OEM too long. "
                    f"Will limit comments to {feedback_steps_to_post} "
                    f"out of KPM's {kpm_feedback_steps_len} steps - "
                    f"to be lower than {ALLOWED_LIMIT} characters."
                )
                break

        jira_issue.feedback_to_oem = all_feedback_to_oem
        # Jira: Post/Append the "Lieferantenaussage" text
        # to "Feedback to OEM" (always append all answers)

        return "feedback_to_oem"

    # KPM -> Jira
    # Handle "Feedback from OEM":
    # TODO: merge with _add_feedback_to_oem and _add_answer_from_oem
    def _add_feedback_from_oem(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync,
        process_step_list: ProcessStepListResponse,
    ):
        # select all process steps where
        # step['ProcessStepTypeDescription'] == "Analyse abgeschlossen"
        # select all "Feedback from OEM" entries from Jira split by
        # [{step["ProcessStepID"]}][{step["Creator"]["Email"]}] ->
        # [2022-09-23-10.32.05.3kk10477][user.name@cariad.technology]
        # If Jira len == KPM len: nothing to do.
        jira_substep_len = self.jira_substeps_len(jira_issue.feedback_from_oem)
        if jira_substep_len == len(process_step_list.feedback_from_oem_step_list):
            self.logger.info(
                "Jira [Feedback from OEM] same as in KPM. Nothing to do.",
                kpm_id=jira_issue.kpm_id,
                jira_id=jira_issue.jira_id,
            )
            return
        # set feedback from oem to jira issue
        all_feedback_from_oem: str = ""
        for process_step in process_step_list.feedback_from_oem_step_list:
            step_response_details: ProcessStepResponse = self.kpm.process_step(
                process_step.problem_number, process_step.step_id
            )
            if not step_response_details:
                self.logger.error(
                    f"Failed to get process step {process_step.step_id} ",
                    kpm_id=process_step.problem_number,
                )
                continue
            all_feedback_from_oem += step_response_details.for_jira_ui
        jira_issue.feedback_from_oem = all_feedback_from_oem

        # Jira: Post/Append the "Analyse abgeschlossen" in form of
        # "\n[ProcessStepId][Email]\n{Text}" to "Feedback from OEM"
        # (always append all answers)
        return "feedback_from_oem"

    # KPM -> Jira
    # Handle "Answer from OEM":
    # TODO: merge with _add_feedback_from_oem and _add_feedback_to_oem
    def _add_answer_from_oem(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync,
        process_step_list: ProcessStepListResponse,
    ):
        # select all process steps where
        # step['ProcessStepTypeDescription'] == "Antwort"
        # (Get length of Jira issue "Answer from OEM".
        # If Jira len == KPM len: nothing to do.)
        # Concat steps creation date and text in reverse order
        jira_substep_len = self.jira_substeps_len(jira_issue.answer_from_oem)
        if jira_substep_len == len(process_step_list.answers_from_oem_step_list):
            self.logger.info(
                "Jira [Answer from OEM] same as in KPM. Nothing to do.",
                kpm_id=jira_issue.kpm_id,
                jira_id=jira_issue.jira_id,
            )
            return
        # set answer from oem to jira issue
        all_answers_from_oem: str = ""
        reverse_answers_from_oem = reversed(
            process_step_list.answers_from_oem_step_list
        )
        for process_step in reverse_answers_from_oem:
            step_response_details: ProcessStepResponse = self.kpm.process_step(
                process_step.problem_number, process_step.step_id
            )
            if not step_response_details:
                self.logger.error(
                    f"Failed to get process step {process_step.step_id} ",
                    kpm_id=process_step.problem_number,
                )
                continue
            all_answers_from_oem += step_response_details.for_jira_ui
        jira_issue.answer_from_oem = all_answers_from_oem
        # Jira: Post the concat list to "Answer from OEM" (Always append all answers)
        return "answer_from_oem"

    def get_attachments_from_jira(self, jira_issue: EsrLabsJiraIssueForKpmSync):
        """Jira: Get attachment list from Jira issue/ticket"""
        attachments_list = self.jira.get_attachments_list(jira_issue)
        attachments = []
        for attachment in attachments_list:
            if not attachment.raw:
                continue
            if filename := attachment.raw.get("filename"):
                attachments.append(str(filename))
        self.logger.debug(f"{jira_issue} Attachments:\n{attachments}")
        return attachments

    def post_attachment_to_jira(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync,
        kpm_doc_name: str,
        kpm_doc_data: bytes | str,
    ):
        # Jira: Post attachment to Jira issue
        attachment_response = self.jira.add_attachment(
            jira_issue, kpm_doc_name, kpm_doc_data
        )
        self.logger.debug(f"{jira_issue}\n{attachment_response=}")
        return attachment_response

    # KPM -> Jira
    # KPM: Fetch document list
    def sync_attachments(self, jira_issue: EsrLabsJiraIssueForKpmSync):
        # Iterate attachments
        # kpm-attachments = list(attachment["Name"]}.{att["Suffix"]})
        kpm_documents = self.kpm.get_document_list(jira_issue.kpm_id)
        if not kpm_documents:
            self.logger.info(f"No documents found for KPM ticket {jira_issue.kpm_id}.")
            return
        existing_jira_attachments = self.get_attachments_from_jira(jira_issue)
        existing_jira_attachments = clean_str_list(existing_jira_attachments)
        # download all documents
        for doc_ref in kpm_documents:
            kpm_doc_full_name = clean_str(f"{doc_ref.name}.{doc_ref.suffix}")
            if kpm_doc_full_name in existing_jira_attachments:
                try:
                    self.logger.info(
                        f"Attachment {kpm_doc_full_name} already present. "
                        "Ignoring it ...",
                        kpm_id=jira_issue.kpm_id,
                        jira_id=jira_issue.jira_id,
                    )
                except (ValueError, KeyError, IndexError):
                    att_name = kpm_doc_full_name.strip("{").strip("}")
                    self.logger.info(
                        f"Attachment {att_name} already present. Ignoring it ..."
                    )
                continue

            # KPM: Download Document
            kpm_doc = self.kpm.get_document(
                jira_issue.kpm_id,
                doc_ref.id,
                doc_ref.name,
                doc_ref.suffix,
                doc_ref.size,
            )
            # self.logger.debug(f'{kpm_doc=}')

            # Jira: Post attachment
            if kpm_doc:
                jira_doc_post_success = self.post_attachment_to_jira(
                    jira_issue, kpm_doc_full_name, kpm_doc
                )
            else:
                self.logger.error(
                    f"KPM document download failed: {kpm_doc_full_name} "
                    f"[size: {doc_ref.size}] to {jira_issue}"
                )
                continue
            if jira_doc_post_success:
                self.logger.debug(
                    f"Jira attachment post successfull: {kpm_doc_full_name} "
                    f"[size: {doc_ref.size}] to {jira_issue}"
                )
            else:
                self.logger.error(
                    f"Jira attachment post failed: {kpm_doc_full_name} "
                    f"[size: {doc_ref.size}]  to {jira_issue}"
                )

    # KPM -> Jira
    def sync_ticket_extras_kpm2jira(self, jira_issue: EsrLabsJiraIssueForKpmSync):
        """Method of adding extra fields to an existing Jira issue

        jira_id: Already existing (in the Jira server)
        ticket ID 'AHCP5-...' (jira issue key)

        kpm_ticket: the actual KPM ticket data, not only id
        """
        process_steps: ProcessStepListResponse = self.kpm.process_step_list(
            jira_issue.kpm_id
        )

        # self.logger.debug(f'process step list: {process_steps.as_list}',
        #                   kpm_id=jira_issue.kpm_id, jira_id=jira_issue.jira_id)

        if not process_steps.as_list:
            try:
                self.logger.warning(
                    f"No process steps found: {process_steps}. "
                    'Ignoring "extra/custom fields sync".',
                    kpm_id=jira_issue.kpm_id,
                    jira_id=jira_issue.jira_id,
                )
            except Exception:
                self.logger.warning(
                    f"No process steps found: {process_steps}. "
                    'Ignoring "extra/custom fields sync".'
                )
            return True

        update = []

        if field := self._add_feedback_to_oem(jira_issue, process_steps):
            update.append(field)
        if field := self._add_feedback_from_oem(jira_issue, process_steps):
            update.append(field)
        if field := self._add_answer_from_oem(jira_issue, process_steps):
            update.append(field)

        jira_issue.update_server_custom_fields(self.jira._client, update)

    @timed_cache
    def add_issue(self, kpm_id: str) -> EsrLabsJiraIssueForKpmSync | None:
        """CREATE new Jira issue from KPM id (if doesn't exist)
        OR get existing Jira issue from KPM id (if exists)"""

        jira_issue: EsrLabsJiraIssueForKpmSync = super().add_issue(kpm_id)

        if jira_issue:
            if not (
                jira_issue.jira_id and jira_issue.jira_id.startswith(JIRA_ISSUE_PREFIX)
            ):
                self.logger.error(
                    f"Jira issue creation failed. Jira response {jira_issue}",
                    kpm_id=kpm_id,
                )
                return
        return jira_issue

    # JIRA -> KPM
    # 10. Handle "Question to OEM":
    def add_question_to_oem(
        self, jira_issue: EsrLabsJiraIssueForKpmSync
    ) -> bool | None:
        # Question to OEM -> KPM step['ProcessStepTypeDescription'] == "Rückfrage"
        jira_question_to_oem = jira_issue.question_to_oem
        if not jira_question_to_oem:
            return

        if jira_issue.status == JiraToKpmStatuses.REJECTED:
            jira_question_to_oem = (
                f"Rejected -> [{jira_issue.cause_of_reject}]: {jira_question_to_oem}"
            )

        self.logger.info(
            'Jira "Question to OEM" found. Will try to post to KPM ... ',
            jira_id=jira_issue.jira_id,
            kpm_id=jira_issue.kpm_id,
        )

        if not self.validate_plant_and_org_unit(jira_issue.kpm_id):
            return

        if post_ok := self.kpm.post_supplier_question(
            jira_issue.kpm_id, jira_question_to_oem
        ):
            # delete question from Jira issue object and post changes to Jira server
            self.logger.info(
                'Jira "Question to OEM" posted to KPM. Will delete from Jira ... ',
                jira_id=jira_issue.jira_id,
                kpm_id=jira_issue.kpm_id,
            )

            jira_issue.question_to_oem = ""
            jira_issue.update_server_custom_fields(
                self.jira._client, ["question_to_oem"]
            )
            if not post_ok:
                return
            if post_ok == ALREADY_POSTED:
                self.logger.warning(
                    'Jira "Question to OEM" already posted to KPM. Ignoring ... ',
                    jira_id=jira_issue.jira_id,
                    kpm_id=jira_issue.kpm_id,
                )
                return post_ok
            # add comment that question was posted to KPM successfully
            comment_to_add = "✅ *Question to OEM* successfully posted to KPM:\n"
            self.jira.add_comment(jira_issue, f"{comment_to_add}{jira_question_to_oem}")
            return post_ok

    def sync_status_and_extras_jira2kpm(
        self, jira_issue: EsrLabsJiraIssueForKpmSync, kpm_id: str = None
    ):
        if not kpm_id:
            kpm_id = jira_issue.kpm_id
        if not jira_issue.kpm_id or jira_issue.kpm_id != kpm_id:
            self.logger.error(
                "KPM ID mismatch or missing from JIRA: "
                f"{kpm_id=} != {jira_issue.kpm_id=}"
            )
            return
        self.sync_status_and_question_to_oem_jira2kpm(jira_issue)

    def user_has_no_access_to_kpm_ticket(self, kpm_id: str):
        """Check if user has access to KPM ticket"""
        if not self.kpm:
            self.logger.error("KPM client not initialized")
            return True

        if self.kpm.user_has_no_access_to_ticket(kpm_id):
            self.logger.warning(
                "User has no access to KPM ticket. "
                "Will try post comment to Jira, if missing ... ",
                kpm_id=kpm_id,
            )
            # is there a Jira comment in the ticket already? -> if yes, do nothing
            jira_issue: EsrLabsJiraIssueForKpmSync = self.jira.issue_by_kpm_id(kpm_id)
            if not jira_issue:
                self.logger.warning(
                    "Jira issue not found for KPM ID. "
                    "This could be a KPM ticket that was not assigned to ESR Labs",
                    kpm_id=kpm_id,
                )
                return True
            jira_issue_comments = self.jira.get_all_comments_for_issue_since(
                jira_issue
            ) or [("", "")]
            for comment_date, comment_text in jira_issue_comments:
                if NO_KPM_ACCESS_JIRA_COMMENT in comment_text:
                    self.logger.info(
                        "User has no access to KPM ticket. "
                        f'Jira "{NO_KPM_ACCESS_JIRA_COMMENT}" comment already present '
                        f"(from {comment_date}). Nothing to do ... ",
                        kpm_id=kpm_id,
                        jira_id=jira_issue.jira_id,
                    )
                    return True

            # if not, post comment to Jira
            self.jira.add_comment(jira_issue, NO_KPM_ACCESS_JIRA_COMMENT)

            return True

    # KPM -> JIRA
    # JIRA -> KPM
    def sync_one(self, kpm_id: str):
        """Sync KPM -> JIRA entrypoint:

        1. CREATE new Jira issue from KPM id (if doesn't exist)

        2. ADD/UPDATE custom fields

        3. ADD/UPDATE attachments
        """
        # 1. CREATE/GET new Jira issue based on KPM id
        jira_issue: EsrLabsJiraIssueForKpmSync = self.add_issue(
            kpm_id
        )  # add or get existing
        if not jira_issue:
            return

        # 2. ADD/UPDATE JIRA custom fields (KPM -> JIRA)
        self.sync_ticket_extras_kpm2jira(jira_issue)

        # 3. ADD/UPDATE JIRA custom fields + status (JIRA -> KPM)
        self.sync_status_and_extras_jira2kpm(jira_issue)

        # 4. ADD/UPDATE attachments
        self.sync_attachments(jira_issue)

        return jira_issue

    ######################### JIRA -> KPM status change ##########################

    def check_jira_status_change(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync | str,
        current_status: tuple[str] = None,
        status_not_in: tuple[str] = None,
    ) -> bool | None:
        kpm_id = ""
        if isinstance(jira_issue, EsrLabsJiraIssueForKpmSync):
            jira_id, kpm_id = jira_issue.jira_id, jira_issue.kpm_id
        elif isinstance(jira_issue, str):
            jira_id, kpm_id = jira_issue, ""
        else:
            self.logger.error(f"Invalid jira issue: {jira_issue}")
            return
        if self.jira.get_tickets_with_changed_status(
            since=0,
            current_status=current_status,
            status_not_in=status_not_in,
            jira_ids=jira_id,
        ):
            self.logger.info(
                "Jira issue has a status change in JIRA. ",
                jira_id=jira_id,
                kpm_id=kpm_id,
            )
            return True
        self.logger.info("No status change. ", jira_id=jira_id, kpm_id=kpm_id)

    # JIRA -> KPM
    def post_kpm_status(
        self, kpm_id: str, jira_id: str, status: KpmStatus, reason: str = ""
    ):
        """Update KPM status"""
        if not self.validate_plant_and_org_unit(kpm_id):
            return

        kpm_ticket = self.kpm.issue(kpm_id)
        # problem status or supplier status ???
        kpm_status = kpm_ticket.supplier_status

        status_number = status.status
        if not status_number:
            status_number = kpm_status

        msg = status.comment
        j2kstat = JiraToKpmStatuses()

        if status in [j2kstat.INFO_MISSING, j2kstat.REJECTED] and reason:
            msg += reason

        if self.add_supplier_response(kpm_id, jira_id, status_number, msg):
            return True

    # JIRA -> KPM
    def update_kpm_status(self, jira_issue: EsrLabsJiraIssueForKpmSync) -> bool | None:
        jira_id = jira_issue.jira_id
        kpm_id = jira_issue.kpm_id
        jira_status = jira_issue.status
        jkstat = JiraToKpmStatuses()
        mapped_status: KpmStatus = jkstat.get_status(jira_status)
        if not mapped_status:
            self.logger.error(
                f"No mapped status for Jira status {jira_status}",
                jira_id=jira_id,
                kpm_id=kpm_id,
            )
            return
        self.logger.info(
            f'Will update KPM status to "{mapped_status.comment}" '
            f"[{mapped_status.status}] ... ",
            jira_id=jira_issue.jira_id,
            kpm_id=jira_issue.kpm_id,
        )
        try:
            reason = ""
            j2kstat = JiraToKpmStatuses()
            if mapped_status in [j2kstat.INFO_MISSING, j2kstat.REJECTED]:
                cause = jira_issue.cause_of_reject
                question = jira_issue.question_to_oem
                if cause:
                    reason = f" [{cause}]"
                if question:
                    reason += f":\n{question}"
            return self.post_kpm_status(kpm_id, jira_id, mapped_status, reason)

        except ValueError as e:
            self.logger.warning(
                f"There was a logging exception when updating KPM status to "
                f'"{mapped_status.comment}" [{mapped_status.status}] . ValueError: {e}'
            )

        except Exception as e:
            self.logger.error(
                f'Failed to update KPM status to "{mapped_status.comment}" '
                f"[{mapped_status.status}] ... {e}",
                jira_id=jira_id,
                kpm_id=kpm_id,
            )

    # JIRA -> JIRA status change
    def change_jira_status(
        self,
        jira_issue: EsrLabsJiraIssueForKpmSync,
        to_status: str,
        lookback_days: int = 7,
    ) -> bool:
        msg = f"Trying to change status to {to_status}"
        self.logger.debug(msg, jird_id=jira_issue.jira_id, kpm_id=jira_issue.kpm_id)

        comment = f"✅ Succesfully changed status to *{to_status}*"

        if to_status == "In Analysis":
            last_week_dates = []
            now = datetime.now()
            for x in range(lookback_days):
                date = now - timedelta(days=x)
                date = date.isoformat().split("T")[0].replace("-", "/")
                last_week_dates.append(date)
            last_answer_from_oem: str = jira_issue.last_answer_from_oem or ""
            last_answer_date = last_answer_from_oem.split(":")[0]
            if not any(date in last_answer_date for date in last_week_dates):
                self.logger.warning(
                    f"{msg} "
                    f"-> {now} not in Answer from OEM -> "
                    f"{last_answer_date or 'missing'} ",
                    jird_id=jira_issue.jira_id,
                    kpm_id=jira_issue.kpm_id,
                )
                return
            self.logger.info(f"Answer from OEM not older than {lookback_days} days.")

            comment += f" -> *Answer from OEM* received:\n\n{last_answer_from_oem}"
            all_comments: str = self.jira.get_all_comments_merged_as_str(jira_issue)
            if comment in all_comments:
                self.logger.warning(
                    f"Failed to change status to {to_status} -->> "
                    f"Auto comment already present in issue comments.",
                    jird_id=jira_issue.jira_id,
                    kpm_id=jira_issue.kpm_id,
                )
                return

        updated_jira_issue: EsrLabsJiraIssueForKpmSync = self.jira.update_status(
            jira_issue.jira_id, to_status, comment
        )
        if not updated_jira_issue:
            self.logger.error(
                f"Failed to change status to {to_status}",
                jird_id=jira_issue.jira_id,
                kpm_id=jira_issue.kpm_id,
            )
            return
        self.logger.info(msg, jird_id=jira_issue.jira_id, kpm_id=jira_issue.kpm_id)
        self.jira.add_comment(updated_jira_issue, comment)
        return updated_jira_issue

    # JIRA -> KPM
    def sync_status_and_question_to_oem_jira2kpm(
        self, ticket: EsrLabsJiraIssueForKpmSync | str
    ):
        """Sync JIRA -> KPM status for all Jira issues
        if status was changed in JIRA
            ticket: EsrLabsJiraIssueForKpmSync | jira_id | kpm_id"""
        # Jira: Check if issue in Jira has a status change
        # KPM: Set status
        if isinstance(ticket, str):
            if ticket.startswith(JIRA_ISSUE_PREFIX):
                jira_issue = self.jira.issue(ticket)
            else:
                jira_issue = self.jira.issue_by_kpm_id(ticket)
        else:
            jira_issue = ticket

        # Jira status change from "Info Missing" -> "In Analysis"
        if jira_issue.status == "Info Missing":
            self.change_jira_status(jira_issue, "In Analysis")

        if self.check_jira_status_change(
            jira_issue, current_status=STATUSES_THAT_NEED_QUESTION_TO_OEM
        ):
            if jira_issue.question_to_oem:
                msg = (
                    "Jira issue has status recently changed to "
                    f'{jira_issue.status}, and has the "Question to OEM" populated.'
                    "Will post new status to KPM."
                )
                self.logger.info(
                    msg, jira_id=jira_issue.jira_id, kpm_id=jira_issue.kpm_id
                )
                return self.add_question_to_oem(jira_issue) and self.update_kpm_status(
                    jira_issue
                )
            msg = (
                "Jira issue has status recently changed to "
                f'{jira_issue.status}, but has the "Question to OEM" empty. '
                "Will not post new status to KPM."
            )
            self.logger.warning(
                msg, jira_id=jira_issue.jira_id, kpm_id=jira_issue.kpm_id
            )

        elif self.check_jira_status_change(
            jira_issue, status_not_in=STATUSES_THAT_NEED_QUESTION_TO_OEM
        ):
            return self.update_kpm_status(jira_issue)

        if jira_issue.status not in STATUSES_THAT_NEED_QUESTION_TO_OEM:
            return self.add_question_to_oem(jira_issue)
