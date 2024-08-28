# standard
from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class AddSupplierResponseRequest(BaseRequest):
    def __init__(
        self,
        kpm_id: str,
        user_id: str,
        ticket_id: str,
        status: str,
        text: str,
        uuid=None,
    ) -> None:
        self.action = "AddSupplierResponseRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id
        self.ticket_id = ticket_id  # external reference (e.g. JIRA ID)
        self.status = status
        self.response_text = self.escape_xml(text)

    def body(self):
        return (
            "<soapenv:Body>"
            "<v3:AddSupplierResponse>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            "<SupplierResponse>"
            f"<Status>{self.status}</Status>"
            f"<ErrorNumber>{self.ticket_id}</ErrorNumber>"
            "</SupplierResponse>"
            f"<ResponseText>{self.response_text}</ResponseText>"
            "</v3:AddSupplierResponse>"
            "</soapenv:Body>"
        )
