KPM_SERVICE_ENDPOINT = "volkswagenag.com/PP/QM/GroupProblemManagementService/V3"


XML_IN_01 = (
    '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:ns1="http://www.w3.org/2005/08/addressing" '
    f'xmlns:ns2="{KPM_SERVICE_ENDPOINT}">'
    "<ns0:Header>"
    f"<ns1:To>ws://{KPM_SERVICE_ENDPOINT}</ns1:To>"
    "<ns1:Action>"
    f"http://xmldefs.{KPM_SERVICE_ENDPOINT}/KpmService/GetDocumentListRequest"
    "</ns1:Action>"
    "<ns1:MessageID>urn:uuid:d1761620-675c</ns1:MessageID>"
    "</ns0:Header>"
    "<ns0:Body>"
    "<ns2:GetDocumentList>"
    "<UserAuthentification>"
    "<UserId>TESTP83FG</UserId>"
    "</UserAuthentification>"
    "<ProblemNumber>90100XX</ProblemNumber>"
    "</ns2:GetDocumentList>"
    "</ns0:Body>"
    "</ns0:Envelope>"
)

XML_TO_DICT_OUT_01 = {
    "{http://schemas.xmlsoap.org/soap/envelope/}Header": {
        "{http://www.w3.org/2005/08/addressing}To": "ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3",
        "{http://www.w3.org/2005/08/addressing}Action": "http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3/KpmService/GetDocumentListRequest",
        "{http://www.w3.org/2005/08/addressing}MessageID": "urn:uuid:d1761620-675c",
    },
    "{http://schemas.xmlsoap.org/soap/envelope/}Body": {
        "{volkswagenag.com/PP/QM/GroupProblemManagementService/V3}GetDocumentList": {
            "UserAuthentification": {"UserId": "TESTP83FG"},
            "ProblemNumber": "90100XX",
        }
    },
}
