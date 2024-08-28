from app.ext.kpm_audi.soap_requests.development_problem_data_request import (
    DevelopmentProblemDataRequest,
)


def test_request():
    kpm_id = "1234"
    user_id = "5678"
    uuid = "some_uuid"
    reference = (
        """<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.w3.org/2005/08/addressing" xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">"""  # noqa: E501
        """
  <ns0:Header>
    <ns1:To>ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3</ns1:To>
    <ns1:Action>http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3/KpmService/GetDevelopmentProblemDataRequest</ns1:Action>
    <ns1:MessageID>urn:uuid:some_uuid</ns1:MessageID>
  </ns0:Header>
  <ns0:Body>
    <ns2:GetDevelopmentProblemData>
      <UserAuthentification>
        <UserId>5678</UserId>
      </UserAuthentification>
      <ProblemNumber>1234</ProblemNumber>
    </ns2:GetDevelopmentProblemData>
  </ns0:Body>
</ns0:Envelope>"""
    )
    request = DevelopmentProblemDataRequest(kpm_id=kpm_id, user_id=user_id, uuid=uuid)
    assert request.to_string(indent=True) == reference
