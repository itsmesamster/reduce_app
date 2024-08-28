from app.ext.kpm_audi.soap_responses.base_response import BaseResponse


class AddSupplierQuestionResponse(BaseResponse):
    def get_add_supplier_question_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}AddSupplierQuestionResponse"
        element = self.soap_body
        return self._find(element, match)
