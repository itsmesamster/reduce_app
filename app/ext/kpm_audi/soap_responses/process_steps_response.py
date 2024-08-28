# standard
from dataclasses import dataclass, asdict
from xml.etree.ElementTree import Element

# 3rd party
import yaml

# project
from .base_response import BaseResponse
from app.core.utils import xml_to_dict


# ProcessStep:
"""
'{http://schemas.xmlsoap.org/soap/envelope/}Body':
    '{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetProcessStepResponse':
        GetProcessStepResponse:
            ProcessStep:
                CreationDate: 2022-11-04-12.02.12.791160
                Creator:
                    Email: john.doe@example.com
                    Phone: null
                    UserId: SOMEID
                    UserName: DOE,JOHN
                LastChangeDate: '2022-11-04 12:02:12.943396'
                LastChanger:
                    Email: john.doe@example.com
                    Phone: null
                    UserId: SOMEID
                    UserName: DOE,JOHN
                ProblemNumber: '9194767'
                ProcessStepId: 2022-11-04-12.02.12.791160
                ProcessStepType: '01'
                ProcessStepTypeDescription: erfasst
                SenderRole: E
                Status: '1'
                Text: "Test environment..."
            ResponseMessage:
                MessageId: INFO_001
                MessageText: Method completed successfully
                MessageType: MT_INFO
                SessionKey: de.volkswagen.kpm.backend.command.KPMSessionImpl@8b9b16fb
                VersionDate: Fri May 12 08:59:18 CEST 2023
                VersionId: release_17.5.0

'{http://schemas.xmlsoap.org/soap/envelope/}Header':
    ....
"""


def user_data_to_dict(user: Element) -> dict:
    usr = xml_to_dict(user)
    return {
        "email": usr.get("Email"),
        "phone": usr.get("Phone"),
        "user_id": usr.get("UserId"),
        "user_name": usr.get("UserName"),
    }


@dataclass
class ProcessStep:
    creation_date: str
    creator: dict

    last_change_date: str
    last_changer: dict

    problem_number: str
    step_id: str
    step_type: str
    step_type_desc: str
    sender_role: str
    status: str
    text: str

    def as_dict(self) -> dict:
        return asdict(self)

    def __repr__(self) -> str:
        return f"\n{yaml.safe_dump({'ProcessStep': self.as_dict()})}"

    def __str__(self) -> str:
        return self.__repr__()


class ProcessStepResponse(BaseResponse):
    def get_process_step_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetProcessStepResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_process_step(self):
        match = "GetProcessStepResponse"
        element = self.get_process_step_response()
        return self._find(element, match)

    def _create_process_step(self, step_item) -> ProcessStep:
        return ProcessStep(
            creation_date=self._find(step_item, "CreationDate").text,
            creator=user_data_to_dict(self._find(step_item, "Creator")),
            last_change_date=self._find(step_item, "LastChangeDate").text,
            last_changer=user_data_to_dict(self._find(step_item, "LastChanger")),
            problem_number=self._find(step_item, "ProblemNumber").text,
            step_id=self._find(step_item, "ProcessStepId").text,
            step_type=self._find(step_item, "ProcessStepType").text,
            step_type_desc=self._find(step_item, "ProcessStepTypeDescription").text,
            sender_role=self._find(step_item, "SenderRole").text,
            status=self._find(step_item, "Status").text,
            text=self._find_text(step_item, "Text"),
        )

    @property
    def step(self) -> ProcessStep:
        if self.__dict__.get("_step"):
            return self._step
        match = "ProcessStep"
        element = self.get_process_step()
        process_step = element.findall(match)
        self._step = list(map(self._create_process_step, process_step))[0]
        return self._step

    @property
    def yaml(self):
        process_step: ProcessStep = self.step
        return yaml.safe_dump(process_step.as_dict())

    @property
    def for_jira_ui(self) -> str:
        """Clean data for Jira UI Issue page custom fields"""
        process_step: ProcessStep = self.step
        date = process_step.last_change_date.split(".")[0].replace("-", "/")
        name = process_step.last_changer.get("user_name", "")
        email = process_step.last_changer.get("email", "")
        # Lieferantenaussage -> feedback to oem
        if process_step.step_type_desc == "Lieferantenaussage":
            # no need for extra details as the user is the ESR Labs System User
            first_row = f" 📆 \t {date}"
        elif email:
            first_row = f" 📆 \t {date} \t\t | \t\t 📮 {email}"
        elif name:
            first_row = f" 📆 \t {date} \t\t | \t\t 📮 {name}"
        if process_step.text:
            second_row = f" 📝 \t {process_step.text}\n\n".replace("<b>", "").replace(
                "</b>", ""
            )
        else:
            second_row = (
                f" 📝 \t [issue-sync] No text found in "
                f'this "{process_step.step_type_desc}"\n\n'
            )
        return f"""{first_row}
        {second_row}"""


####################################################################################


@dataclass
class ProcessStepItem:
    problem_number: str
    step_id: str
    last_change_date: str
    step_type: str
    step_type_desc: str
    status: str
    sender_role: str

    def as_dict(self):
        return asdict(self)

    def __str__(self) -> str:
        return f"\n{yaml.safe_dump({'ProcessStepItem': self.as_dict()})}"

    def __repr__(self) -> str:
        return self.__str__()


class ProcessStepListResponse(BaseResponse):
    def get_process_step_list_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetProcessStepListResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_process_step_list(self):
        match = "GetProcessStepListResponse"
        element = self.get_process_step_list_response()
        return self._find(element, match)

    @property
    def as_list(self) -> list[ProcessStepItem]:
        """List of Process steps."""
        if self.__dict__.get("_list"):
            return self._list
        match = "ProcessStepItem"
        element = self.get_process_step_list()
        process_step_items = element.findall(match)
        self._list = list(map(self._create_process_step_item, process_step_items))
        return self._list

    def _create_process_step_item(self, step_item) -> ProcessStepItem:
        return ProcessStepItem(
            problem_number=self._find(step_item, "ProblemNumber").text,
            step_id=self._find(step_item, "ProcessStepId").text,
            last_change_date=self._find(step_item, "LastChangeDate").text,
            step_type=self._find(step_item, "ProcessStepType").text,
            step_type_desc=self._find(step_item, "ProcessStepTypeDescription").text,
            status=self._find(step_item, "Status").text,
            sender_role=self._find(step_item, "SenderRole").text,
        )

    @property
    def feedback_to_oem_step_list(self) -> list[ProcessStepItem]:
        """select all process steps where
        step['ProcessStepTypeDescription'] == "Lieferantenaussage" """
        feedback_items: list = []
        for process_step in self.as_list:
            if process_step.step_type_desc == "Lieferantenaussage":
                feedback_items.append(process_step)
        return feedback_items

    @property
    def feedback_from_oem_step_list(self) -> list[ProcessStepItem]:
        """select all process steps where
        step['ProcessStepTypeDescription'] == "Analyse abgeschlossen" """
        feedback_items: list = []
        for process_step in self.as_list:
            if process_step.step_type_desc == "Analyse abgeschlossen":
                feedback_items.append(process_step)
        return feedback_items

    @property
    def questions_to_oem_step_list(self) -> list[ProcessStepItem]:
        """select all process steps where
        step['ProcessStepTypeDescription'] == "Analyse abgeschlossen" """
        questions_to_oem: list = []
        for process_step in self.as_list:
            if process_step.step_type_desc == "Analyse abgeschlossen":
                questions_to_oem.append(process_step)
        return questions_to_oem

    @property
    def answers_from_oem_step_list(self) -> list[ProcessStepItem]:
        """select all process steps where
        step['ProcessStepTypeDescription'] == "Antwort" """
        answers_from_oem: list = []
        for process_step in self.as_list:
            if "Antwort" in process_step.step_type_desc:
                answers_from_oem.append(process_step)
        return answers_from_oem
