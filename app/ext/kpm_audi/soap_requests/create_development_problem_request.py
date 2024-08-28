# standard
from uuid import uuid1

# project extension
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class CreateDevelopmentProblemRequest(BaseRequest):
    def __init__(
        self,
        user_id: str,
        plant: str,
        org_unit: str,
        project: str,
        project_brand: str,
        rating: str,
        desc: str,
        short_text: str,
        frequency: str,
        repeatable: str,
        pre_number: str,
        middle_group: str,
        end_number: str,
        hardware: str,
        software: str,
        uuid=None,
    ) -> None:
        self.user_id = user_id
        self.plant = plant
        self.org_unit = org_unit
        self.project = project
        self.project_brand = project_brand
        self.rating = rating
        self.desc = desc
        self.short_text = short_text
        self.frequency = frequency
        self.repeatable = repeatable
        self.pre_number = pre_number
        self.middle_group = middle_group
        self.end_number = end_number
        self.hardware = hardware
        self.software = software
        self.uuid = uuid or str(uuid1())
        self.action = "CreateDevelopmentProblemRequest"

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:CreateDevelopmentProblem>"
            f"{self._user_authentification()}"
            f"<DevelopmentProblem>"
            f"{self.development_problem()}"
            f"</DevelopmentProblem>"
            f"</v3:CreateDevelopmentProblem>"
            f"</soapenv:Body>"
        )

    def development_problem(self):
        return (
            f"<Workflow>42</Workflow>"  #
            f"<Rating>{self.rating}</Rating>"
            f"<Description>{self.desc}</Description>"
            f"<ShortText>{self.short_text}</ShortText>"
            f"{self.origin()}"
            f"{self.creator()}"
            f"{self.coordinator()}"
            f"{self.foremost_group_project()}"
            f"<Frequency>{self.frequency}</Frequency>"
            f"<Repeatable>{self.repeatable}</Repeatable>"
            f"<ForemostTestPart>"
            f"{self.part_number()}"
            f"<Hardware>{self.hardware}</Hardware>"
            f"<Software>{self.software}</Software>"
            f"</ForemostTestPart>"
        )
        # -> past hardcoded params

    def origin(self):
        return (
            "<Origin>"
            "<Phase>EL</Phase>"  # EL
            "<PhaseAddition>ESRLABS</PhaseAddition>"  # ESRLABS
            "<SubProcess>EE</SubProcess>"  # EE
            "<MainProcess>PEP</MainProcess>"  # PEP
            "</Origin>"
        )

    def creator(self):
        return (
            f"<Creator>"
            f"<Address>"
            f"<OrganisationalUnit>{self.org_unit}</OrganisationalUnit>"
            f"<Plant>{self.plant}</Plant>"
            f"</Address>"
            f"<PersonalContractor>"
            f"<UserId>{self.user_id}</UserId>"
            f"</PersonalContractor>"
            f"</Creator>"
        )

    def coordinator(self):
        return (
            "<Coordinator>"
            "<Contractor>"
            "<Address>"
            f"<OrganisationalUnit>{self.org_unit}</OrganisationalUnit>"  # HCP5
            f"<Plant>{self.plant}</Plant>"  # 21
            "</Address>"
            "<PersonalContractor>"
            f"<UserId>{self.user_id}</UserId>"  # EV6K03O
            "</PersonalContractor>"
            "</Contractor>"
            "</Coordinator>"
        )

    def foremost_group_project(self):
        return (
            "<ForemostGroupProject>"
            f"<Brand>{self.project_brand}</Brand>"  # AU
            f"<Project>{self.project}</Project>"  # 416
            "</ForemostGroupProject>"
        )

    def part_number(self):
        return (
            f"<PartNumber>"
            f"<PreNumber>{self.pre_number}</PreNumber>"
            f"<MiddleGroup>{self.middle_group}</MiddleGroup>"
            f"<EndNumber>{self.end_number}</EndNumber>"
            f"</PartNumber>"
        )
