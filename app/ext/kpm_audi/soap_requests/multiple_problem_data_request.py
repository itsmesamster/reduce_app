# standard
from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class MultipleProblemDataRequest(BaseRequest):
    def __init__(
        self,
        user_id: str,
        since: str,
        inbox: str,
        desc="",
        contact="",
        addr_timestamp="",
        uuid=None,
    ) -> None:
        """
        since: LastChangeTimestamp -> All tickets that changed since this date in the
        form off: "2022-05-01 15:00:00.0"
        inbox: Plant/OrganisationalUnit/Group
        desc: Description
        contact: ContactPerson
        addr_timestamp: AddressTimestamp
        """
        self.action = "GetMultipleProblemDataRequest"
        self.user_id = user_id
        self.uuid = uuid or str(uuid1())
        self.since = since
        self.inbox = inbox
        self.desc = desc
        self.contact = contact
        self.addr_timestamp = addr_timestamp

    def body(self) -> str:
        return (
            f"<soapenv:Body>"
            f"<v3:GetMultipleProblemData>"
            f"{self._user_authentification()}"
            f"<LastChangeTimestamp>{self.since}</LastChangeTimestamp>"
            f"<OverviewAddress>"
            f"<AddressTimestamp>{self.addr_timestamp}</AddressTimestamp>"
            f"<ContactPerson>{self.contact}</ContactPerson>"
            f"<Description>{self.desc}</Description>"
            f"<OrganisationalUnit>{self._unit()}</OrganisationalUnit>"
            f"<Group>{self._group()}</Group>"
            f"<Plant>{self._plant()}</Plant>"
            f"</OverviewAddress>"
            f"<ActiveOverview>true</ActiveOverview>"
            f"<PassiveOverview>false</PassiveOverview>"
            f"</v3:GetMultipleProblemData>"
            f"</soapenv:Body>"
        )

    # TODO: FIXME: split errors not handled
    # 'NoneType' object has no attribute 'split'
    # index issues
    def _plant(self) -> str:
        """Get the Plant from inbox."""
        return self.inbox.split("/")[0]

    def _unit(self) -> str:
        """Get the Organisational unit from inbox."""
        return self.inbox.split("/")[1]

    def _group(self) -> str:
        """Get the Group from inbox."""
        return self.inbox.split("/")[2]
