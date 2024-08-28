# standard
from datetime import datetime
from pathlib import Path
import os
from functools import lru_cache
from time import sleep

# external
from requests import Response, Session

# project core
from app.core.custom_logger import logger
from app.core.core_config import (
    APP_CACHE_DIR,
    ATTACHMENTS_VALIDATION_SIZE_TOLERANCE,
)
from app.core.utils import approximate_comparison, strip_date_prefix

# project extension
from app.ext.kpm_audi.exceptions import (
    KpmConnectError,
    KpmMissingConnectionError,
    KpmRequestError,
    KpmResponseError,
    KPMApiError,
)
from app.ext.kpm_audi.soap_requests import (
    DevelopmentProblemDataRequest,
    MultipleProblemDataRequest,
    ProcessStepListRequest,
    ProcessStepRequest,
    DocumentListRequest,
    DocumentRequest,
    AddSupplierResponseRequest,
    AddSupplierQuestionRequest,
)
from app.ext.kpm_audi.soap_responses import (
    DevelopmentProblemDataResponse,
    MultipleProblemDataResponse,
    ProcessStepListResponse,
    ProcessStepResponse,
    DocumentListResponse,
    DocumentReference,
    DocumentResponse,
    AddSupplierQuestionResponse,
    AddSupplierResponseResponse,
)


ALREADY_POSTED = "already_posted"


class KPMClient:
    """SOAP client to consume the KPM web service."""

    def __init__(
        self,
        server_url: str,
        user_id: str,
        cert_path: str,
        inbox: str,
        post_back_to_kpm: bool = False,
    ) -> None:
        """Initialize the KPM client.

        server  (str):  The full URL of the server to connect to.
        user    (str):  The User ID to be used for the TLS authentication.
        cert    (str):  The path to the TLS certificate to be used.
        inbox   (str):  The inbox to be used for the requests.
        """
        self.server = server_url
        self.user = user_id
        self.cert = cert_path
        self.inbox = inbox
        self.post_back_to_kpm = post_back_to_kpm

        self.logger = logger
        self.session = None

    def connect(self) -> "KPMClient":
        """Connect to a KPM server"""
        if None in (self.server, self.user, self.cert):
            raise KpmConnectError(
                f"Please provide server {self.server}, "
                f"user {self.user} and tls certificate {self.cert}."
            )
        self.logger.info(f"Connecting KPM client to {self.user}@{self.server} ... ")
        session = Session()
        session.cert = self.cert
        session.headers.update({"Content-Type": "text/xml; charset=utf-8"})
        self.session = session
        return self

    def __repr__(self):
        self_name = f"{self.__class__.__name__} at {hex(id(self))}"
        if self.session and self.server and self.user:
            return f"{self.user}@{self.server} ({self_name})"
        return self_name

    def issue(self, kpm_id: str) -> DevelopmentProblemDataResponse:
        """Request Development Problem Data for given KPM ID."""
        data = DevelopmentProblemDataRequest(kpm_id, self.user).to_string()
        self.logger.info(f"Request KPM issue: {kpm_id}.", kpm_id=kpm_id)
        # from app.core.utils import xml_to_yaml
        # print(xml_to_yaml(data))
        response = self._post(data=data)
        result = DevelopmentProblemDataResponse(response, kpm_id)
        if result.is_valid():
            return result

    def query(self, since: str) -> MultipleProblemDataResponse:
        """Request multiple Development Problem Data for provided params."""
        inbox = self.inbox
        data = MultipleProblemDataRequest(self.user, since, inbox).to_string()
        self.logger.info(f"Query KPM issues since {since} for project: {inbox}.")
        result = self._post(data=data)
        try:
            response = MultipleProblemDataResponse(result)
            issues = response.problem_references()
            self.logger.debug(
                f"Found {len(issues)} KPM issues for {inbox} since {since}"
            )
            if response.is_valid():
                return response
            return response
        except Exception as ex:
            raise KpmResponseError(ex) from ex

    def _session(self):
        """Get a connection to the KPM client or raise `KpmMissingConnectionError`."""
        if self.session:
            return self.session
        else:
            self.logger.error("KPM client not connected. Please connect first.")
            raise KpmMissingConnectionError

    def _post(self, data) -> Response:
        """Send a POST request with the given data and return the response
        or raise a KpmRequestError."""
        try:
            result = self._session().post(
                self.server, data=data.encode(encoding="utf-8")
            )
            return result
        except Exception as ex:
            self.logger.error(f"Failed to post request: {ex}")
            raise KpmRequestError(ex) from ex

    def process_step_list(self, kpm_id: str) -> ProcessStepListResponse:
        """Request Process Step List for given KPM ID."""
        data = ProcessStepListRequest(kpm_id=kpm_id, user_id=self.user).to_string()
        # self.logger.debug(f"Request process step list for KPM issue {kpm_id} {data=}")
        try:
            result = self._post(data=data)
            process_step_list = ProcessStepListResponse(result)
            if process_step_list.is_valid():
                return process_step_list
        except Exception as ex:
            self.logger.error(f"Exception: {ex}")

    @lru_cache(maxsize=30)
    def process_step(self, kpm_id: str, step_id: str) -> ProcessStepResponse | None:
        """Request Process Step for given KPM ID and STEP ID."""
        data = ProcessStepRequest(kpm_id, self.user, step_id).to_string()
        self.logger.info(f"Requesting process step -> ID: {step_id} ", kpm_id=kpm_id)
        # self.logger.debug(f"Requesting process step -> ID: {step_id} {data=}",
        #                       kpm_id=kpm_id)
        try:
            result = self._post(data=data)
            response = ProcessStepResponse(result)
            descr = response.step.step_type_desc
            stype = response.step.step_type
            self.logger.debug(
                f"Process step [{kpm_id}][{stype}][{descr}][{step_id}]"
                f"response:\n{response.for_jira_ui}"
            )
            if response.is_valid():
                return response
        except Exception as ex:
            self.logger.error(f"Exception: {ex}")

    def get_document_list(self, kpm_id: str) -> list[DocumentReference]:
        """Request document list for given KPM ID"""
        data = DocumentListRequest(kpm_id, self.user).to_string()
        self.logger.info("Requesting document list from KPM.", kpm_id=kpm_id)
        # self.logger.debug(f"Requesting document list from KPM {data=}", kpm_id=kpm_id)
        try:
            result = self._post(data=data)
            # self.logger.debug(f'DocumentListRequest {result.text=}')
            response = DocumentListResponse(result)
            if response.is_valid():
                document_list = response.as_list
                self.logger.debug(f"DocumentListResponse:\n{document_list}")
                return document_list
        except Exception as ex:
            self.logger.error(f"Exception: {ex}")

    def validate_attachment_size(self, attachment_path: str, size: int) -> bool | None:
        """Validate attachment size"""
        tolerance = ATTACHMENTS_VALIDATION_SIZE_TOLERANCE  # in bytes
        kpm_id = attachment_path.split("/")[-4].lstrip("kpmid_")
        downloaded_size = os.stat(attachment_path).st_size
        should_be_size = int(size)
        if downloaded_size == should_be_size:
            return True
        if -tolerance <= downloaded_size - should_be_size <= tolerance:
            return True
        self.logger.error(
            f"Attachment size mismatch: {downloaded_size=} vs. "
            f"{should_be_size=} for {attachment_path}",
            kpm_id=kpm_id,
        )

    def get_document(
        self, kpm_id: str, doc_id: str, doc_name: str, suffix: str, size: str
    ):
        """Request document (attachment) for given KPM ID and DOC ID.

        This method will download to the local cache
        the attachment or attachment parts (without merging)
        """

        data = DocumentRequest(kpm_id, self.user, doc_id).to_string()
        self.logger.info(
            f"Requesting document (attachment) -> ID: {doc_id} ", kpm_id=kpm_id
        )
        self.logger.debug(f"{kpm_id=}, {doc_id=}, {doc_name=}, {suffix=}, {size=}")
        try:
            result: Response = self._post(data=data)
            now = datetime.now().date().strftime("%Y-%m-%d")
            file_name = f"{doc_name}.{suffix}"
            file_path = f"{now}/kpmid_{kpm_id}/stepid_{doc_id}/size_{size}"
            dir_path = f"{APP_CACHE_DIR}/{file_path}"
            full_path = f"{dir_path}/{file_name}"
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            if Path(full_path).is_file():
                self.logger.warning(f"KPM file {file_path}/{file_name} already exists.")
                with open(full_path, "rb") as f:
                    try:
                        self.validate_attachment_size(full_path, size)
                        attachment = f.read()
                        return attachment
                    except Exception as ex:
                        self.logger.error(
                            f"Failed to read file {file_path}/{file_name} : {ex}"
                        )
            response = DocumentResponse(result)
            if not response.is_valid():
                return
            attachment = response.attachment
            if not attachment:
                return
            with open(full_path, "wb") as f:
                f.write(attachment)
            self.validate_attachment_size(full_path, size)
            return attachment
        except Exception as ex:
            self.logger.error(
                f"Get XML SOAP MTOM/XOP Attachment Exception "
                f"for {kpm_id=} {doc_id=} {doc_name=} {suffix=} {size=} : {ex}"
            )

    def get_last_step_of_type(self, kpm_id: str, step_type_desc: str):
        """get last from feedback list / last of type description

        e.g. : Lieferantenaussage, Rückfrage"""
        process_steps = self.process_step_list(kpm_id)
        if not process_steps:
            return
        try:
            for step in process_steps.as_list:
                if step.step_type_desc == step_type_desc:
                    detailed_step: ProcessStepResponse = self.process_step(
                        step.problem_number, step.step_id
                    )
                    # self.logger.debug(f'Last "{step_type_desc}" for
                    # KPM ID {kpm_id}:\n{detailed_step.yaml}')
                    return detailed_step
        except (KPMApiError, Exception) as e:
            try:
                self.logger.error(
                    f"Failed to get last {step_type_desc}: {e}", kpm_id=kpm_id
                )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.error(
                    f"Failed to get last {step_type_desc} for kpm id {kpm_id}: {e}"
                )

    def get_last_supplier_response(self, kpm_id: str):
        self.logger.info("Will get last supplier response ... ", kpm_id=kpm_id)
        return self.get_last_step_of_type(kpm_id, "Lieferantenaussage")

    def get_last_supplier_question(self, kpm_id: str):
        self.logger.info("Will get last supplier question ... ", kpm_id=kpm_id)
        return self.get_last_step_of_type(kpm_id, "Rückfrage")

    def post_supplier_response(
        self, kpm_id: str, ticket_id: str, status: str, text: str
    ) -> bool | str | None:
        """ticket_id: external reference | jira id | issue id | problem id etc

        return:
            True if successful

            None if failed to post

            'already_posted' if text already present in last "Lieferantenaussage"
        """
        self.logger.info("Will add new supplier response ... ", kpm_id=kpm_id)
        # get last Liefereantenaussage from feedback list
        current_supplier_response: ProcessStepResponse = (
            self.get_last_supplier_response(kpm_id)
        )

        text = text.strip()

        # compare with existing one
        if current_supplier_response:
            self.logger.debug(
                f"Last supplier response:\n{current_supplier_response.for_jira_ui}"
            )
            # if different, post new one
            if text and approximate_comparison(
                text, current_supplier_response.for_jira_ui
            ):
                self.logger.warning(
                    f"No new supplier response to post: [{strip_date_prefix(text)}] "
                    f'already in last "Lieferantenaussage" ',
                    kpm_id=kpm_id,
                )
                return ALREADY_POSTED
        else:
            self.logger.debug("No supplier response found.", kpm_id=kpm_id)
        data: str = AddSupplierResponseRequest(
            kpm_id, self.user, ticket_id, status, text
        ).to_string()
        if not self.post_back_to_kpm:
            self.logger.warning(
                f"POST BACK TO KPM is set to FALSE. "
                f"Just showing the AddSupplierResponseRequest data:\n{data}"
            )
            return
        log_msg = f"{ticket_id=} {status=} {text=}"

        response = self._post(data=data)
        result = AddSupplierResponseResponse(response)

        err_msg = f"❌ ❌ New supplier response POST to KPM -> FAILED for: {log_msg} ❌ ❌"  # noqa: E501
        if not result.is_valid():
            self.logger.error(err_msg, kpm_id=kpm_id)
            return

        # this sleep allows KPM to process the request
        # from AddSupplierResponseRequest to Process Step List
        # in order to be able to get this/our supplier response
        # as last "Lieferantenaussage"
        sleep(1)

        # check if new response was posted successfully to KPM /
        # compare with what should have been posted
        updated_supplier_response: ProcessStepResponse = (
            self.get_last_supplier_response(kpm_id)
        )

        if updated_supplier_response and approximate_comparison(
            text, updated_supplier_response.for_jira_ui
        ):
            self.logger.info(
                f" ✅ ✅ New supplier response added successfully for: {log_msg} ✅ ✅",
                kpm_id=kpm_id,
            )
            return True

        self.logger.debug(f"{updated_supplier_response=}")
        self.logger.debug(f"{text=}")
        if updated_supplier_response:
            self.logger.debug(f"{updated_supplier_response.for_jira_ui=}")

        self.logger.error(err_msg, kpm_id=kpm_id)

    def post_supplier_question(self, kpm_id: str, question: str) -> bool | str | None:
        """
        Add Supplier Question / Question to OEM as a new KPM "Rückfrage" process step
        ticket_id: external reference | jira id | issue id | problem id etc

        return:
            True if successful

            None if failed to post

            'already_posted' if question already present in last "Rückfrage"
        """
        self.logger.info(
            'Will add new Supplier Question / Question to OEM -> to "Rückfrage" ... ',
            kpm_id=kpm_id,
        )

        question = question.strip()

        # check if question was already posted to KPM / compare it with existing one
        current_supplier_question: ProcessStepResponse = (
            self.get_last_supplier_question(kpm_id)
        )
        if current_supplier_question:
            self.logger.debug(
                f"Last supplier question:\n{current_supplier_question.for_jira_ui}"
            )
            # if different, post new one
            if question and approximate_comparison(
                question, current_supplier_question.for_jira_ui
            ):
                self.logger.warning(
                    f"No new supplier question to post: [{question}] "
                    f'already in last "Rückfrage" ',
                    kpm_id=kpm_id,
                )
                return ALREADY_POSTED
        else:
            self.logger.debug("No supplier question found.", kpm_id=kpm_id)

        data: str = AddSupplierQuestionRequest(kpm_id, self.user, question).to_string()
        if not self.post_back_to_kpm:
            self.logger.warning(
                f"POST BACK TO KPM is set to FALSE. "
                f"Just showing the AddSupplierQuestionRequest data:\n{data}"
            )
            return
        response = self._post(data=data)
        result = AddSupplierQuestionResponse(response)

        err_msg = (
            '❌ ❌ New supplier question aka "Question to OEM" '
            "POST to KPM -> FAILED ❌ ❌"
        )
        if not result.is_valid():
            self.logger.error(err_msg, kpm_id=kpm_id)
            return

        # this sleep allows KPM to process the request
        # from AddSupplierQuestionRequest to Process Step List
        # in order to be able to find it in the Process Step List
        sleep(1)

        # check if new question was posted successfully to KPM /
        # compare with what should have been posted
        updated_supplier_question: ProcessStepResponse = (
            self.get_last_supplier_question(kpm_id)
        )

        if updated_supplier_question and approximate_comparison(
            question, updated_supplier_question.for_jira_ui
        ):
            self.logger.info(
                ' ✅ ✅ New supplier question aka "Question to OEM" '
                "added successfully ✅ ✅ ",
                kpm_id=kpm_id,
            )
            return True

        self.logger.debug(f"{updated_supplier_question=}")
        self.logger.debug(f"{question=}")
        if updated_supplier_question:
            self.logger.debug(f"{updated_supplier_question.for_jira_ui=}")

        self.logger.error(err_msg, kpm_id=kpm_id)

    def get_current_status(self, kpm_id: str):
        """get current status for KPM issue
        available statuses: problem | supplier | engineering | coordinator
        """
        kpm_ticket: DevelopmentProblemDataResponse = self.issue(kpm_id)
        if not kpm_ticket:
            self.logger.warning(f"Failed to get current status for KPM issue: {kpm_id}")
            return
        return {
            "problem": kpm_ticket.problem_status,  # ProblemStatus
            "engineering": kpm_ticket.engineering_status,  # EngineeringStatus
            "supplier": kpm_ticket.supplier_status,  # SupplierStatus
            "inner": {
                # Supplier / Status
                "supplier_inner": kpm_ticket.supplier_inner_status,
                # ProblemSolver / Status
                "problem_solver": kpm_ticket.problem_solver_status,
                # Coordinator / Status
                "coordinator": kpm_ticket.coordinator_status,
                # SpecialistCoordinator / Status
                "specialist_coord": kpm_ticket.specialist_coord_status,
            },
        }

    def user_has_no_access_to_ticket(self, kpm_id: str | int):
        """check if user has no access to ticket"""
        kpm_id: str = str(kpm_id)

        data = DevelopmentProblemDataRequest(kpm_id, self.user).to_string()
        self.logger.info("Checking if user has access to KPM ticket", kpm_id=kpm_id)
        response = self._post(data=data)
        kpm_ticket = DevelopmentProblemDataResponse(response, kpm_id)
        if kpm_ticket.has_no_access():
            return True
