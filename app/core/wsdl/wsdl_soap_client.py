# standard libs


# 3rd party libs
from requests import Session
from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.proxy import ServiceProxy
from lxml import etree

# project
from app.core.custom_logger import logger


class DefaultLoggingPlugin(Plugin):
    # out / request
    def egress(self, envelope, http_headers, operation, binding_options):
        logger.debug("---------- LoggingPlugin egress / out / request: ")
        logger.debug(etree.tostring(envelope))
        return envelope, http_headers

    # in / response
    def ingress(self, envelope, http_headers, operation):
        logger.debug("---------- LoggingPlugin ingress / in / response")
        logger.debug(etree.tostring(envelope))
        return envelope, http_headers


class WSDLClient:
    """
    Please note that the WSDL file contents are of extreme importance

    The actual HTTP/S URI must be found in the WSDL file,
        under service/port/soap:address location=
    """

    def __init__(
        self,
        wsdl_file_path: str,
        certificate_path: str,
        service_name: str,
        port_name: str,
        xsd_attribute: str,
        api_version: str | None = None,
        settings: Settings = Settings(strict=False),  # xml_huge_tree=True
        plugins: list[Plugin] = [DefaultLoggingPlugin()],
    ):
        self.wsdl_file_path = wsdl_file_path
        self.certificate_path = certificate_path
        self.service_name = service_name
        self.port_name = port_name
        self.xsd_attribute = xsd_attribute
        self.api_version = api_version
        self.settings = settings
        self.plugins = plugins
        self.wsdl_client = None
        self.wsdl_service = None

    def __create_wsdl_client(self):
        session = Session()
        session.cert = self.certificate_path
        client = Client(
            self.wsdl_file_path,
            service_name=self.service_name,
            port_name=self.port_name,
            transport=Transport(session=session),
            settings=self.settings,
            plugins=self.plugins,
        )
        client.set_ns_prefix("soapenv", "Envelope")
        client.set_ns_prefix("soapenv", "Header")
        client.set_ns_prefix("soapenv", "Body")
        self.wsdl_client = client
        return self.wsdl_client

    def get_wsdl_client(self) -> Client:
        """
        returns a zeep.Client instance
        """
        if self.wsdl_client:
            return self.wsdl_client
        return self.__create_wsdl_client()

    def __create_wsdl_service(self):
        return self.get_wsdl_client().bind(
            service_name=self.service_name,
            port_name=self.port_name,
        )

    def get_wsdl_service(self) -> ServiceProxy:
        """
        returns a zeep.proxy.ServiceProxy instance
        """
        if self.wsdl_service:
            return self.wsdl_service
        return self.__create_wsdl_service()

    def get_all_available_wsdl_actions(self):
        service = self.get_wsdl_service()
        return sorted(list(service._operations.keys()))

    def build_soap_flat_header(
        self, data: dict, addressing_attrib: str = None
    ) -> list[etree.Element]:
        """
        This is the soapenv Header that will be send inside the Envelope,
        it's not the actual Request Header
        """
        xml_str_list = []
        if addressing_attrib:
            for tag, value in data.items():
                xml_str_list.append(f"<{tag} {addressing_attrib}>{value}</{tag}>")
        else:
            for tag, value in data.items():
                xml_str_list.append(f"<{tag}>{value}</{tag}>")
        return [etree.fromstring(xml_str) for xml_str in xml_str_list]
