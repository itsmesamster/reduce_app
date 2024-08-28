from app.ext.kpm_audi.soap_requests.process_steps_request import (
    ProcessStepRequest,
    ProcessStepListRequest,
)


def test_process_step_request():
    kpm_id = "1234"
    user_id = "5678"
    uuid = "some_uuid"
    step_id = "2023-00-00-00.00.00.000000"
    reference = (
        """<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.w3.org/2005/08/addressing" xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">"""  # noqa: E501
        """
  <ns0:Header>
    <ns1:To>ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3</ns1:To>
    <ns1:Action>http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3/KpmService/GetProcessStepRequest</ns1:Action>
    <ns1:MessageID>urn:uuid:some_uuid</ns1:MessageID>
  </ns0:Header>
  <ns0:Body>
    <ns2:GetProcessStep>
      <UserAuthentification>
        <UserId>5678</UserId>
      </UserAuthentification>
      <ProblemNumber>1234</ProblemNumber>
      <ProcessStepId>2023-00-00-00.00.00.000000</ProcessStepId>
    </ns2:GetProcessStep>
  </ns0:Body>
</ns0:Envelope>"""
    )
    request = ProcessStepRequest(
        kpm_id=kpm_id, user_id=user_id, step_id=step_id, uuid=uuid
    )
    assert request.to_string(indent=True) == reference


def test_process_step_list_request():
    kpm_id = "1234"
    user_id = "5678"
    uuid = "some_uuid"
    reference = (
        """<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.w3.org/2005/08/addressing" xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">"""  # noqa: E501
        """
  <ns0:Header>
    <ns1:To>ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3</ns1:To>
    <ns1:Action>http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3/KpmService/GetProcessStepListRequest</ns1:Action>
    <ns1:MessageID>urn:uuid:some_uuid</ns1:MessageID>
  </ns0:Header>
  <ns0:Body>
    <ns2:GetProcessStepList>
      <UserAuthentification>
        <UserId>5678</UserId>
      </UserAuthentification>
      <ProblemNumber>1234</ProblemNumber>
    </ns2:GetProcessStepList>
  </ns0:Body>
</ns0:Envelope>"""
    )
    request = ProcessStepListRequest(kpm_id=kpm_id, user_id=user_id, uuid=uuid)
    assert request.to_string(indent=True) == reference
