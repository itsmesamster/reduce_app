import pytest
import xml.etree.ElementTree as ET
from requests import Response
from requests.structures import CaseInsensitiveDict


@pytest.fixture
def make_mtom_soap_response(
    mtom_soap_headers_uuid,
    make_mtom_soap_headers,
    mtom_soap_multipart_headers,
    make_soap_envelope,
):
    def _make(
        response=None,
        uuid=None,
        headers=None,
        multipart_headers=None,
        multipart_content=None,
        soap_body_content="The Body",
        soap_header_content="The Header",
    ):
        requests_response = response or Response()
        uuid = uuid or mtom_soap_headers_uuid
        headers = headers or make_mtom_soap_headers(uuid)
        multipart_headers = multipart_headers or mtom_soap_multipart_headers
        multipart_content = multipart_content or make_soap_envelope(
            soap_header_content, soap_body_content
        )
        requests_response.headers = headers
        content = (
            f"\r\n--{uuid}"
            f"{multipart_headers}"
            f"\r\n"
            f"\r\n"
            f"{multipart_content}"
            f"\r\n--{uuid}--"
        )
        requests_response._content = bytes(content, "utf-8")
        return requests_response

    return _make


@pytest.fixture
def make_soap_header():
    def _add_content(content="The Header"):
        return (
            f'<soap:Header xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            f"{content}"
            f"</soap:Header>"
        )

    return _add_content


@pytest.fixture
def make_soap_body():
    def _add_content(content="The Body"):
        return (
            f'<soap:Body xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            f"{content}"
            f"</soap:Body>"
        )

    return _add_content


@pytest.fixture
def soap_body_xml(make_soap_body):
    return ET.fromstring(make_soap_body())


@pytest.fixture
def make_soap_envelope(make_soap_header, make_soap_body):
    def _make(header_content="The Header", body_content="The Body"):
        header = make_soap_header(header_content)
        body = make_soap_body(body_content)
        return (
            f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            f"{header}"
            f"{body}"
            f"</soap:Envelope>"
        )

    return _make


@pytest.fixture
def soap_envelope_xml(make_soap_envelope):
    return ET.fromstring(make_soap_envelope())


@pytest.fixture
def mtom_soap_headers_uuid():
    return "uuid:43f59cc1-440c-4031-a265-ad083053d3e1"


@pytest.fixture
def make_mtom_soap_headers():
    def _set_uuid(uuid):
        return CaseInsensitiveDict(
            {
                "Transfer-Encoding": "chunked",
                "Content-Type": f'multipart/related; \
                type="application/xop+xml"; \
                boundary="{uuid}"; \
                start="<root.message@cxf.apache.org>"; \
                start-info="text/xml"',
            }
        )

    return _set_uuid


@pytest.fixture
def mtom_soap_multipart_headers():
    return (
        "\r\nContent-Type: text/xml; charset=UTF-8\r\nContent-Transfer-Encoding: binary"
        "\r\nContent-ID: <root.message@cxf.apache.org>"
    )


@pytest.fixture
def mtom_soap_response_soap(make_mtom_soap_response):
    return make_mtom_soap_response()


@pytest.fixture
def json_response():
    requests_response = Response()
    requests_response.headers = CaseInsensitiveDict(
        {"Content-Type": "application/json"}
    )
    requests_response._content = b"{}"
    return requests_response


@pytest.fixture
def xml_response_kpm_fault():
    requests_response = Response()
    requests_response.headers = CaseInsensitiveDict({"Content-Type": "text/xml"})
    requests_response._content = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        b"<soap:Header></soap:Header>"
        b"<soap:Body>"
        b'<ns1:Fault xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/">'
        b"<faultcode>ns1:Server</faultcode>"
        b"<faultstring/>"
        b"<detail>"
        b'<ns2:KpmFault xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">'
        b"<errorCode>Some Error Code</errorCode>"
        b"<message>Ups</message>"
        b"</ns2:KpmFault>"
        b"</detail>"
        b"</ns1:Fault>"
        b"</soap:Body>"
        b"</soap:Envelope>"
    )
    return requests_response
