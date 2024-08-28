from app.ext.kpm_audi.soap_responses.base_response import BaseResponse


class AddSupplierResponseResponse(BaseResponse):
    def get_add_supplier_response_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}AddSupplierResponseResponse"
        element = self.soap_body
        return self._find(element, match)
