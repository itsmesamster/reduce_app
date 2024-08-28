# standard
import re
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

# 3rd party

# project
from app.core.utils import (
    since_timestamp,
    xml_to_dict,
    xml_to_yaml,
)

# test data
from tests.data.ext.ahcp5 import (
    XML_IN_01,
    XML_TO_DICT_OUT_01,
    DEVELOPMENT_PROBLEM_RESPONSE_01_XML,
    DEVELOPMENT_PROBLEM_RESPONSE_01_YAML,
)


def test_since_timestamp():
    # Test that the function returns a string
    assert isinstance(since_timestamp(), str)

    # Test that the function returns a string in the correct format
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d", since_timestamp())

    # Test that the function returns a string that is 36 hours ago
    now = datetime.now()
    hours = 36
    if now.weekday() == 0:  # Monday
        hours += 48
    expected = (now - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S.0")

    result = since_timestamp(hours=36)
    assert result == expected


def test_xml_to_dict_using_element_tree():
    xml_root = ET.fromstring(XML_IN_01)

    assert xml_to_dict(xml_root) == XML_TO_DICT_OUT_01


def test_xml_to_dict():
    assert xml_to_dict(XML_IN_01) == XML_TO_DICT_OUT_01


def test_xml_to_yaml():
    result = xml_to_yaml(DEVELOPMENT_PROBLEM_RESPONSE_01_XML)
    expected = DEVELOPMENT_PROBLEM_RESPONSE_01_YAML
    assert result == expected
