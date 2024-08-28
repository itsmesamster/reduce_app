import pytest
import xml.etree.ElementTree as ET
from app.ext.kpm_audi.soap_responses.base_response import BaseResponse
from app.ext.kpm_audi.exceptions import KpmResponseError


def test_mtom_soap_response_soap_message_to_string(
    make_mtom_soap_response, soap_envelope_xml
):
    response = BaseResponse(make_mtom_soap_response())
    assert ET.tostring(response.soap_envelope) == ET.tostring(soap_envelope_xml)
    assert response.to_string() == ET.tostring(soap_envelope_xml)


def test_mtom_soap_response_soap_body_can_be_read(
    make_mtom_soap_response, soap_body_xml
):
    response = BaseResponse(make_mtom_soap_response())
    assert ET.tostring(response.soap_body) == ET.tostring(soap_body_xml)


def test_invalid_first_multipart_content_type(make_mtom_soap_response):
    mutlipart_headers = "\r\nContent-Type: application/binary"
    response = BaseResponse(
        make_mtom_soap_response(multipart_headers=mutlipart_headers)
    )
    with pytest.raises(KpmResponseError) as ex:
        response.xml()
    error_msg = "Unexpected first body content-type. Expected: 'text/xml' but received"
    assert error_msg in str(ex.value)


def test_invalid_response_content_type(json_response):
    response = BaseResponse(json_response)
    with pytest.raises(KpmResponseError) as ex:
        response.xml()
    error_msg = (
        "Expected xml+xop parts or KpmFault but received: "
        "Content-Type: application/json, Content: {}"
    )
    assert error_msg == str(ex.value)


def test_xml_soapukpm_fault(xml_response_kpm_fault):
    response = BaseResponse(xml_response_kpm_fault)
    with pytest.raises(KpmResponseError) as ex:
        assert response.xml()
    assert "Request failed with error: Some Error Code, -> Ups" == str(ex.value)
