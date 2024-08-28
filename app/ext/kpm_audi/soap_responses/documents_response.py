# standard
from dataclasses import dataclass, asdict
from xml.etree.ElementTree import Element
from requests import Response

# 3rd party
import yaml

# project
from app.ext.kpm_audi.soap_responses.base_response import BaseResponse

"""
'{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDocumentResponse':
GetDocumentResponseInternal:
    Document:
        AccessRight: '0'
        ContainsPersonalData: 'true'
        Data:
            '{http://www.w3.org/2004/08/xop/include}Include': null
        Name: AW  Fehlerspeicheranforderung DUM_909_A_NonOBD_80114
        Suffix: msg
"""


class DocumentResponse(BaseResponse):
    def get_document_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDocumentResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_document_internal(self):
        match = "GetDocumentResponseInternal"
        element = self.get_document_response()
        return self._find(element, match)

    def get_document(self):
        match = "Document"
        element = self.get_document_internal()
        return self._find(element, match)

    def get_data(self) -> Element:
        # <Data>
        #       <xop:Include href="cid:8b559b22-8c7f-4d5a-935e-aa0abcdefg-18551
        # @cxf.apache.org" xmlns:xop="http://www.w3.org/2004/08/xop/include"/>
        # </Data>
        match = "Data"
        element = self.get_document()
        return self._find(element, match)

    def get_xop_include_href_cid(self):
        match = "{http://www.w3.org/2004/08/xop/include}Include"
        element = self.get_data()
        xop = self._find(element, match)
        href = xop.attrib.get("href", "")
        if href.startswith("cid:"):
            return href.lstrip("cid:")

    def split_header(self, header: bytes):
        header_dict = {}
        for line in header.split(b"\r\n"):
            if b": " in line:
                key, value = line.split(b": ")
                if b"Content-ID" in value:
                    header_dict[key] = value.lstrip(b"<")
                else:
                    header_dict[key] = value
        return header_dict

    def clean_attachment(self, attachment: bytes):
        split_list = attachment.split(b"\r\n--uuid:")
        if len(split_list) == 2:
            return split_list[0].lstrip(b"\r\n\r\n")

    def get_xop_data(self) -> dict | None:
        """Get MTOM/XOP raw binary attachment file"""
        """
        e.g:
        --uuid:8df5f235-fba1-492f-8425-example
        Content-Type: text/xml; charset=UTF-8
        Content-Transfer-Encoding: binary
        Content-ID: <root.message@cxf.apache.org>

        <?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        [...]
        <Data>
        <xop:Include href="cid:example-8c7f-4d5a-935e-aa0abcdefg-18551@cxf.apache.org" 
        xmlns:xop="http://www.w3.org/2004/08/xop/include"/>
        </Data>
        [...]
        </soap:Envelope>
        --uuid:8df5f235-fba1-492f-8425-example
        Content-Type: application/octet-stream
        Content-Transfer-Encoding: binary
        Content-ID: <example-8c7f-4d5a-935e-aa0abcdefg-18551@cxf.apache.org>
        
        //Binary data here

        --uuid:8df5f235-fba1-492f-8425-example--
        """
        # try:
        ROOT_CONTENT_ID = b"Content-ID: <root.message@cxf.apache.org>"
        CONTENT_ID_CFX = b"@cxf.apache.org>"
        SPLIT_SEPARATOR = (
            b"</Data></Document></GetDocumentResponseInternal>"
            b"</ns2:GetDocumentResponse></soap:Body></soap:Envelope>"
        )

        xop_mime_data = {}  # mtom/xop mime document/attachment details

        if isinstance(self.raw, Response):
            if self.raw.status_code != 200:
                return
            raw_content = self.raw.content
        if not raw_content:
            return

        split_content = raw_content.split(SPLIT_SEPARATOR)
        for i, byte_seq in enumerate(split_content):
            # self.logger.debug(f'\n\nbyte_seq: {i}')
            if ROOT_CONTENT_ID in byte_seq:
                continue
            # self.logger.debug(f'\n\t\t\t{byte_seq[:500]=}')
            # self.logger.debug(f'\n\t\t\t{byte_seq[-200:]=}')
            split_inner = byte_seq.split(CONTENT_ID_CFX)
            if len(split_inner) == 2:
                xop_mime_data["header"] = self.split_header(split_inner[0])
                xop_mime_data["attachment"] = self.clean_attachment(split_inner[1])
                # self.logger.debug(f"\n\t{xop_mime_data['header']=}")
                # self.logger.debug(f"\n\t{xop_mime_data['attachment'][:100]=}")
                # self.logger.debug(f"\n\t{xop_mime_data['attachment'][-100:]=}")
                return xop_mime_data
        self.logger.error(
            f"Unable to split raw binary attachment byte_seq using {CONTENT_ID_CFX}"
        )
        # except Exception as e:
        #     self.logger.error(f'Unable to extract raw binary attachment: {e}')

    @property
    def attachment(self) -> bytes | None:
        """Get MTOM/XOP raw binary attachment file"""
        if not self.__dict__.get("_attachment"):
            xop = self.get_xop_data()
            if isinstance(xop, dict):
                self._attachment = xop.get("attachment")
                return self._attachment


#######################################################################################################################


@dataclass
class DocumentReference:
    id: str
    name: str
    size: str
    access_right: str
    suffix: str
    dtype: str

    def as_dict(self):
        return asdict(self)

    def __str__(self) -> str:
        return f"\n{yaml.safe_dump({'DocumentReference': self.as_dict()})}"

    def __repr__(self) -> str:
        return self.__str__()


class DocumentListResponse(BaseResponse):
    def get_document_list_response(self):
        match = "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDocumentListResponse"
        element = self.soap_body
        return self._find(element, match)

    def get_document_list(self):
        match = "GetDocumentListResponseInternal"
        element = self.get_document_list_response()
        return self._find(element, match)

    @property
    def as_list(self) -> list[DocumentReference]:
        """List of KPM issue Documents"""
        if self.__dict__.get("_list"):
            return self._list
        match = "DocumentReference"
        element = self.get_document_list()
        documents = element.findall(match)
        self._list = list(map(self._create_document_reference, documents))
        return self._list

    def _create_document_reference(self, step_item) -> DocumentReference:
        return DocumentReference(
            id=self._find(step_item, "DocumentId").text,
            name=self._find(step_item, "Name").text,
            size=self._find(step_item, "Size").text,
            access_right=self._find(step_item, "AccessRight").text,
            suffix=self._find(step_item, "Suffix").text,
            dtype=self._find(step_item, "Type").text,
        )
