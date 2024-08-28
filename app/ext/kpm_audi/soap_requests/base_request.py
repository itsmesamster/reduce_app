import abc
import xml.etree.ElementTree as ET


class BaseRequest:
    def __init__(self) -> None:
        self.action = None
        self.uuid = None
        self.user_id = None
        self.kpm_id = None

    def escape_xml(self, xml_content: str):
        return (
            xml_content.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def to_xml(self):
        return ET.fromstring(self._document())

    def to_string(self, indent=False):
        # The conversion to string serves like a xml validation
        xml = self.to_xml()
        if indent:
            ET.indent(xml)
        str_xml = ET.tostring(xml, encoding="unicode")
        return str_xml

    @abc.abstractmethod
    def body(self):
        "The Soapenv Envelope Body"
        return

    def soap_env_header(self):
        return (
            f"<soapenv:Header>"
            f'<To xmlns="{self._xmlns_addr()}">'
            f"ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3"
            f"</To>"
            f'<Action xmlns="{self._xmlns_addr()}">'
            f"{self._xmldef_v3()}/KpmService/{self.action}"
            f"</Action>"
            f'<MessageID xmlns="{self._xmlns_addr()}">'
            f"urn:uuid:{self.uuid}"
            f"</MessageID>"
            f"</soapenv:Header>"
        )

    def _document(self):
        return (
            f'<soapenv:Envelope xmlns:soapenv="{self._xmlns_soapenv()}" '
            f'xmlns:v3="{self._xmldef_v3()}">'
            f"{self.soap_env_header()}"
            f"{self.body()}"
            f"</soapenv:Envelope>"
        )

    def _user_authentification(self):
        return (
            f"<UserAuthentification>"
            f"<UserId>{self.user_id}</UserId>"
            f"</UserAuthentification>"
        )

    def _problem_number(self):
        return f"<ProblemNumber>{self.kpm_id}</ProblemNumber>"

    def _xmldef_v3(self):
        return "http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3"

    def _xmlns_soapenv(self):
        return "http://schemas.xmlsoap.org/soap/envelope/"

    def _xmlns_addr(self):
        return "http://www.w3.org/2005/08/addressing"
