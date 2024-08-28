from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class DevelopmentProblemDataRequest(BaseRequest):
    def __init__(self, kpm_id: str, user_id: str, uuid=None) -> None:
        self.action = "GetDevelopmentProblemDataRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:GetDevelopmentProblemData>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"</v3:GetDevelopmentProblemData>"
            f"</soapenv:Body>"
        )
