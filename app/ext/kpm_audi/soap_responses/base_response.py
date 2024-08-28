from collections import OrderedDict
import re
from requests import Response
import xmltodict
import xml.etree.ElementTree as ET
from json import dumps, loads

# project core
from app.core.custom_logger import logger
from app.core.utils import xml_to_yaml

# project extension
from app.ext.kpm_audi.exceptions import KpmResponseError


class BaseResponse:
    def __init__(self, response: Response, kpm_id="") -> None:
        self.kpm_id = kpm_id
        self.raw = response
        self.logger = logger
        self.content_type = response.headers.get("content-type", "")
        self._soap_envelope = None
        self._soap_fault = False

    def __getitem__(self, key):
        return self._find(key)

    def to_ord_dict(self) -> OrderedDict:
        return xmltodict.parse(self.to_string())

    def to_dict(self) -> dict:
        return loads(dumps(self.to_ord_dict()))

    def to_string(self):
        return ET.tostring(self.xml())

    def is_valid(self) -> bool | None:
        """Validate KPM SOAP response"""
        """ OK response e.g. (changed from xml to yaml):
        '{http://schemas.xmlsoap.org/soap/envelope/}Body':
        '{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}AddSupplierResponseResponse':
        AddSupplierResponseResponseInternal:
            EngineeringStatus: '2'
            ProblemStatus: '2'
            ProcessStepId: 2023-08-01-09.42.53.466570
            ResponseMessage:
                MessageId: INFO_001
                MessageText: Method completed successfully
                MessageType: MT_INFO
                SessionKey: de.volkswagen.kpm.backend.command.KPMSessionImpl@19033a56
                VersionDate: Mon Jul 10 12:34:32 CEST 2023
                VersionId: release_17.7.0
            SupplierStatus: '0'
        """

        yaml_body = xml_to_yaml(self.soap_body)

        success_msg = "MessageText: Method completed successfully"
        if success_msg in yaml_body:
            logger.info(
                f'KPM "success" response validation passed for {type(self).__name__}'
            )
            return True

        logger.error(f"KPM response validation failed:\n{yaml_body}")

    @property
    def soap_envelope(self):
        return self.xml()

    @property
    def soap_body(self):
        match = f"{self.xmldef_soap_envelope}Body"
        element = self.xml()
        return self._find(element, match)

    @property
    def faulty(self):
        return self._soap_fault

    @property
    def soap_fault(self):
        if not self.faulty:
            return None
        match = f"{self.xmldef_soap_envelope}Fault"
        element = self.soap_body
        return self._find(element, match)

    @property
    def soap_fault_detail(self):
        if not self.faulty:
            return None
        match = "detail"
        element = self.soap_fault
        return self._find(element, match)

    @property
    def kpm_fault(self):
        if not self.faulty:
            return None
        match = f"{self.xmldef_kpm_v3}KpmFault"
        element = self.soap_fault_detail
        return self._find(element, match)

    @property
    def kpm_fault_error_code(self):
        if not self.faulty:
            return None
        match = "errorCode"
        element = self.kpm_fault
        return self._find(element, match).text

    @property
    def kpm_fault_message(self):
        if not self.faulty:
            return None
        match = "message"
        element = self.kpm_fault
        return self._find(element, match).text

    @property
    def xmldef_soap_envelope(self):
        return "{http://schemas.xmlsoap.org/soap/envelope/}"

    @property
    def xmldef_kpm_v3(self):
        return (
            "{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}"
        )

    def xml(self):
        # TODO: Improve. We assume here that we have a valid xml+xop
        # Therefore the first part is the xml with the xop references.
        # Following parts could be binary attachments referenced via xop.
        if self._soap_envelope is not None:
            return self._soap_envelope
        parts = self.parts()
        if parts:
            header, body = parts[0].split(b"\r\n\r\n")
            if "Content-Type: text/xml" in header.decode("utf-8"):
                content = body.decode("utf-8")
                try:
                    self._soap_envelope = ET.fromstring(content)
                    if self._soap_envelope is not None:
                        return self._soap_envelope
                    raise KpmResponseError(
                        f"Could not find SOAP Envelope in response: {content}"
                    )
                except Exception as ex:
                    if isinstance(ex, KpmResponseError):
                        raise ex
                    raise KpmResponseError(
                        f"Invalid XML in Response body: {ex}"
                    ) from ex
            else:
                raise KpmResponseError(
                    f"Unexpected first body content-type. Expected: 'text/xml' "
                    f"but received {header.decode('utf-8')}"
                )
        try:
            self._soap_fault = True
            self._soap_envelope = ET.fromstring(self.raw.content.decode("utf-8"))
            message = (
                f"Request failed with error: {self.kpm_fault_error_code}, "
                f"-> {self.kpm_fault_message}"
            )
            raise KpmResponseError(message)
        except Exception as ex:
            if isinstance(ex, KpmResponseError):
                raise ex
            raise KpmResponseError(
                f"Expected xml+xop parts or KpmFault but received: "
                f"Content-Type: {self.content_type}, Content: {self.raw.text}"
            ) from ex

    def parts(self):
        if self.is_multipart() and self.is_xop_xml():
            boundary_string = f"--{self.boundary()}"
            parts = self.raw.content.split(bytes(boundary_string, "utf-8"))
            # Before the first boundary there is an empty line,
            # the last one finishes with `--`
            return parts[1::-2]

    def is_multipart(self):
        return "multipart/related" in self.content_type

    def is_xop_xml(self):
        return 'type="application/xop+xml"' in self.content_type

    def boundary(self):
        boundary_pattern = re.compile(r'boundary="([\w\-\:]+)"')
        try:
            return re.search(boundary_pattern, self.content_type)[1]
        except TypeError:
            raise KpmResponseError(
                f"Received Content-Type: 'multipart/related', but could "
                f"not read 'boundary' from: {self.content_type}"
            )

    def _find(self, element: ET.Element = None, match: str = "") -> ET.Element | str:
        if not len(element):
            element = self.xml()
        item = element.find(match)
        if item is not None:
            return item
        msg = f"Expected field: '{match}' in element: {element.tag}, but found none"
        self.logger.warning(msg)
        # self.logger.debug(f'{msg}: \n{xml_to_yaml(element)}.')
        return ""

    def _find_text(self, element: ET.Element = None, match: str = "") -> str:
        elem = self._find(element, match)
        if elem is not None and isinstance(elem, ET.Element) and elem.text:
            return elem.text
        return ""

    def has_no_access(self) -> bool | None:
        """Check KPM SOAP response for NO access -> will return True if
        there is NO KPM ACCESS to this ticket"""
        """ No access response e.g. (changed from xml to yaml):
        '{http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDevelopmentProblemDataResponse':
        GetDevelopmentProblemDataResponseInternal:
            ResponseMessage:
            MessageId: FC_512
            MessageText: The user has no permission to read the problem
            MessageType: MT_FAULT
            SessionKey: de.volkswagen.kpm.backend.command.KPMSessionImpl@c0101c11
            VersionDate: Thu Aug 03 13:49:00 CEST 2023
            VersionId: release_17.8.0
        """

        yaml_body = xml_to_yaml(self.soap_body)

        success_msg = "MessageText: Method completed successfully"
        if success_msg in yaml_body:
            logger.info(f"KPM access validation passed for {type(self).__name__}")
            return

        no_kpm_access_msg = (
            "MessageText: The user has no permission to read the problem"
        )
        if no_kpm_access_msg in yaml_body:
            logger.warning(f"NO KPM ACCESS - {type(self).__name__}", kpm_id=self.kpm_id)
            return True

        logger.error(f"KPM response validation failed:\n{yaml_body}")
