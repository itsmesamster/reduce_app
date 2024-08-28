# standard
from uuid import uuid1

# project
from app.ext.kpm_audi.soap_requests.base_request import BaseRequest


class ProcessStepRequest(BaseRequest):
    def __init__(self, kpm_id: str, user_id: str, step_id: str, uuid=None) -> None:
        self.action = "GetProcessStepRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id
        self.step_id = step_id

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:GetProcessStep>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"<ProcessStepId>{self.step_id}</ProcessStepId>"
            f"</v3:GetProcessStep>"
            f"</soapenv:Body>"
        )


class ProcessStepListRequest(BaseRequest):
    def __init__(self, kpm_id: str, user_id: str, uuid=None) -> None:
        self.action = "GetProcessStepListRequest"
        self.uuid = uuid or str(uuid1())
        self.kpm_id = kpm_id
        self.user_id = user_id

    def body(self):
        return (
            f"<soapenv:Body>"
            f"<v3:GetProcessStepList>"
            f"{self._user_authentification()}"
            f"{self._problem_number()}"
            f"</v3:GetProcessStepList>"
            f"</soapenv:Body>"
        )
