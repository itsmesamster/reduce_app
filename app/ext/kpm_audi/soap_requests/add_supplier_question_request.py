# standard
from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


# Question to OEM / question_to_oem
class AddSupplierQuestionRequest(BaseRequest):
    def __init__(
        self, kpm_id: str, user_id: str, question_to_oem: str, uuid=None
    ) -> None:
        self.action = "AddSupplierQuestionRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id
        self.question_to_oem = self.escape_xml(question_to_oem)

    def body(self):
        return (
            "<soapenv:Body>"
            "<v3:AddSupplierQuestion>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"<SupplierQuestion>{self.question_to_oem}</SupplierQuestion>"
            "</v3:AddSupplierQuestion>"
            "</soapenv:Body>"
        )
