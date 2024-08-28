# standard
from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class DocumentRequest(BaseRequest):
    def __init__(self, kpm_id: str, user_id: str, document_id: str, uuid=None) -> None:
        self.action = "GetDocumentRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id
        self.document_id = document_id

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:GetDocument>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"<DocumentId>{self.document_id}</DocumentId>"
            f"</v3:GetDocument>"
            f"</soapenv:Body>"
        )


class DocumentListRequest(BaseRequest):
    def __init__(self, kpm_id: str, user_id: str, uuid=None) -> None:
        self.action = "GetDocumentListRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:GetDocumentList>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"</v3:GetDocumentList>"
            f"</soapenv:Body>"
        )


# DocumentReference
