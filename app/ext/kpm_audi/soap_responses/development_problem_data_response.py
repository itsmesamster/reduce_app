from json import loads, dumps
from dataclasses import dataclass

import xml.etree.ElementTree as ET
import xmltodict
import yaml

from .base_response import BaseResponse


@dataclass
class Address:
    AddressTimestamp: str
    ContactPerson: str
    Description: str
    Group: str
    OrganisationalUnit: str
    Plant: str


@dataclass
class PersonalContractor:
    Email: str
    Phone: str
    UserId: str
    UserName: str


@dataclass
class Contractor:
    Address: Address
    PersonalContractor: PersonalContractor


@dataclass
class Coordinator:
    Contractor: Contractor
    OrderType: str
    Status: str


@dataclass
class Creator:
    Address: Address
    PersonalContractor: PersonalContractor


@dataclass
class ForemostGroupProject:
    Brand: str
    Extension: str
    LaunchPriority: str
    Project: str
    Reporting: str


@dataclass
class PartNumber:
    Charge: str
    ChargeSerialNumber: str
    EndNumber: str
    Index: str
    MiddleGroup: str
    PreNumber: str


@dataclass
class ForemostTestPart:
    EEDeviceType: str
    Hardware: str
    PartName: str
    PartNumber: PartNumber
    SeFt: str
    Software: str


@dataclass
class Kefa:
    DefectObjectId: str
    DefectTypeId: str
    Type: str


@dataclass
class Origin:
    MainProcess: str
    Phase: str
    PhaseAddition: str
    SubProcess: str


@dataclass
class ProblemSolver:
    Contractor: Contractor
    DueDate: str
    OrderType: str
    Status: str


@dataclass
class SollVerbundRelease:
    Extend: str
    Major: str
    Minor: str


@dataclass
class SpecialistCoordinator:
    Contractor: Contractor
    DueDate: str
    OrderType: str
    Status: str


@dataclass
class Supplier:
    Contractor: Contractor
    DueDate: str
    OrderType: str
    Status: str


@dataclass
class VerbundRelease:
    Extend: str
    Major: str
    Minor: str


@dataclass
class DevelopmentProblem:
    ActiveRole: str
    AuthorityToClose: str
    AuthorityToOutgoingCheck: str
    Coordinator: Coordinator
    Country: str
    Creator: Creator
    Description: str
    EProject: str
    EngineeringStatus: str
    Exclaimer: str
    ExternalProblemNumber: str
    ForemostGroupProject: ForemostGroupProject
    ForemostTestPart: ForemostTestPart
    Frequency: str
    Function: str
    Kefa: Kefa
    Keyword: str
    LastChangeTimestamp: str
    LaunchPriority: str
    ModuleRelevant: str
    Origin: Origin
    ProblemDate: str
    ProblemNumber: str
    ProblemSolver: ProblemSolver
    ProblemStatus: str
    Rating: str
    Repeatable: str
    Section: str
    ShortText: str
    SollVerbundRelease: SollVerbundRelease
    SpecialistCoordinator: SpecialistCoordinator
    StartOfProductionDate: str
    Supplier: Supplier
    SupplierStatus: str
    TCB: str
    TrafficLight: str
    VBV: str
    VerbundRelease: VerbundRelease
    Visibility: str
    Workflow: str


@dataclass
class DevelopmentProblemDataResponse(BaseResponse):
    def __init__(self, response, kpm_id="") -> None:
        super().__init__(response, kpm_id)
        self._output_ok_for_str_format = None

    def summary(self):
        return (
            f"KPM ID: {self.problem_number} - Jira ID: {self.external_problem_number}"
        )

    def get_development_data_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDevelopmentProblemDataResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_development_data_response_internal(self):
        match = "GetDevelopmentProblemDataResponseInternal"
        element = self.get_development_data_response()
        return self._find(element, match)

    def log_other_fault_type(self):
        resp_msg = self.response_message

        def look(elem):
            return self._find(resp_msg, elem)

        msg = {
            elem: look(elem).text
            for elem in ["MessageId", "MessageType", "MessageText"]
            if look(elem)
        }
        return msg

    def development_problem_as_dict(self) -> dict:
        if self.development_problem:
            dev_problem = ET.tostring(self.development_problem)
            return loads(dumps(xmltodict.parse(dev_problem)))

    def development_problem_as_yaml(self) -> str:
        d = self.development_problem_as_dict()
        if d:
            return yaml.safe_dump(d)

    @property
    def response_message(self):
        match = "ResponseMessage"
        element = self.get_development_data_response_internal()
        return self._find(element, match)

    @property
    def development_problem(self):
        match = "DevelopmentProblem"
        element = self.get_development_data_response_internal()
        dev_probl = self._find(element, match)
        if dev_probl:
            return dev_probl
        self.logger.debug(self.log_other_fault_type())

    @property
    def problem_number(self):
        match = "ProblemNumber"
        element = self.development_problem
        if element:
            xml_val = self._find(element, match).text
            if xml_val:
                self.kpmid = xml_val
                return xml_val
        return ""

    @property
    def kpm_id_from_response(self):
        if self.problem_number:
            return self.problem_number
        return self.kpm_id

    @property
    def external_problem_number(self):
        match = "ExternalProblemNumber"
        element = self.development_problem
        if element:
            return self._find(element, match).text
        return ""

    @property
    def supplier_status(self):
        match = "SupplierStatus"
        element = self.development_problem
        if element:
            return self._find(element, match).text
        return ""

    @property
    def problem_status(self):
        match = "ProblemStatus"
        element = self.development_problem
        if element:
            return self._find(element, match).text
        return ""

    @property
    def engineering_status(self):
        match = "EngineeringStatus"
        element = self.development_problem
        if element:
            return self._find(element, match).text
        return ""

    def _get_inner_status(self, status_group: str):
        element = self.development_problem
        if not element:
            return ""
        inner = self._find(element, status_group)
        if not inner:
            return ""
        return self._find(inner, "Status").text

    @property
    def supplier_inner_status(self):  # Supplier / Status
        return self._get_inner_status("Supplier")

    @property
    def problem_solver_status(self):  # ProblemSolver / Status
        return self._get_inner_status("ProblemSolver")

    @property
    def coordinator_status(self):  # Coordinator / Status
        return self._get_inner_status("Coordinator")

    @property
    def specialist_coord_status(self):  # SpecialistCoordinator / Status
        return self._get_inner_status("SpecialistCoordinator")

    def __repr__(self):
        yml = self.development_problem_as_yaml()
        if yml:
            return self.development_problem_as_yaml()
        if self.faulty:
            details = {
                "ticket": self.problem_number,
                "fault": self.kpm_fault,
                "code": self.kpm_fault_error_code,
                "msg": self.kpm_fault_message,
            }
            msg = f"KPM FAULT: ticket: {details}"
        else:
            msg = str(self.log_other_fault_type())
        self.logger.debug(f"{msg}", self.problem_number)
        return msg

    def __bool__(self):
        if not self.faulty and self.kpm_id:
            return True
        return False

    def log_output_as_yaml(self):
        # fields values (description field usually) contain code that might
        # cause str format KeyError when added to logs
        # e.g. src:DiagServiceEvents.hpp|lin:211|p_output:
        # {"domainRepairInstructionId":1,"errorCode":50462751, ...
        if self._output_ok_for_str_format is not None:
            return self._output_ok_for_str_format
        try:
            kpm_yml = self.development_problem_as_yaml()
            self.logger.debug(
                f"Checking KPM DevelopmentProblem {self.kpm_id} for sync: \n{kpm_yml}",
                kpm_id=self.kpm_id,
            )
            self._output_ok_for_str_format = True
        except KeyError as e:
            self.logger.warning(
                f"KPM DevelopmentProblem output can't be added to f-strings. "
                f"KeyError: {e}",
                kpm_id=self.kpm_id,
            )
            self._output_ok_for_str_format = False
        except IndexError as e:
            self.logger.warning(
                f"KPM DevelopmentProblem with KPM ID {self.kpm_id} -> "
                f"output log str format has IndexError: {e}"
            )
            self._output_ok_for_str_format = False
        except Exception as e:
            self.logger.error(
                f"KPM DevelopmentProblem with KPM ID {self.kpm_id} -> "
                f"output log str format has Exception: {e}"
            )
            self._output_ok_for_str_format = False
        return self._output_ok_for_str_format
