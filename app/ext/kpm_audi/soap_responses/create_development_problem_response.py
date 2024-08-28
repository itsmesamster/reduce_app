from app.ext.kpm_audi.soap_responses.base_response import BaseResponse


class CreateDevelopmentProblemResponse(BaseResponse):
    @property
    def problem_number(self):
        match = "ProblemNumber"
        element = self.get_development_problem_status_response_internal()
        return self._find(element, match).text

    def get_create_development_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}CreateDevelopmentProblemResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_create_development_response_internal(self):
        match = "CreateDevelopmentProblemResponseInternal"
        element = self.get_create_development_response()
        return self._find(element, match)

    def get_development_problem_status_response_internal(self):
        match = "DevelopmentProblemStatusResponseInternal"
        element = self.get_create_development_response_internal()
        return self._find(element, match)
