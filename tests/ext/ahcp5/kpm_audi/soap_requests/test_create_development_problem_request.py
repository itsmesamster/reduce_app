from app.ext.kpm_audi.soap_requests.create_development_problem_request import (
    CreateDevelopmentProblemRequest,
)


def test_request():
    user_id = "user"
    plant = "FF"
    org_unit = "HCP5BS-ESR"
    project = "AU"
    project_brand = "416"
    rating = "rating"
    desc = "description"
    short_text = "short-text"
    frequency = "frequency"
    repeatable = "repeatable"
    pre_number = "pre-number"
    middle_group = "middle-group"
    end_number = "end-number"
    hardware = "hardware"
    software = "software"
    uuid = "some_uuid"
    reference = (
        """<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.w3.org/2005/08/addressing" xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">"""  # noqa: E501
        f"""
  <ns0:Header>
    <ns1:To>ws://volkswagenag.com/PP/QM/GroupProblemManagementService/V3</ns1:To>
    <ns1:Action>http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3/KpmService/CreateDevelopmentProblemRequest</ns1:Action>
    <ns1:MessageID>urn:uuid:some_uuid</ns1:MessageID>
  </ns0:Header>
  <ns0:Body>
    <ns2:CreateDevelopmentProblem>
      <UserAuthentification>
        <UserId>user</UserId>
      </UserAuthentification>
      <DevelopmentProblem>
        <Workflow>42</Workflow>
        <Rating>rating</Rating>
        <Description>description</Description>
        <ShortText>short-text</ShortText>
        <Origin>
          <Phase>EL</Phase>
          <PhaseAddition>ESRLABS</PhaseAddition>
          <SubProcess>EE</SubProcess>
          <MainProcess>PEP</MainProcess>
        </Origin>
        <Creator>
          <Address>
            <OrganisationalUnit>{org_unit}</OrganisationalUnit>
            <Plant>{plant}</Plant>
          </Address>
          <PersonalContractor>
            <UserId>user</UserId>
          </PersonalContractor>
        </Creator>
        <Coordinator>
          <Contractor>
            <Address>
              <OrganisationalUnit>{org_unit}</OrganisationalUnit>
              <Plant>{plant}</Plant>
            </Address>
            <PersonalContractor>
              <UserId>{user_id}</UserId>
            </PersonalContractor>
          </Contractor>
        </Coordinator>
        <ForemostGroupProject>
          <Brand>{project_brand}</Brand>
          <Project>{project}</Project>
        </ForemostGroupProject>
        <Frequency>frequency</Frequency>
        <Repeatable>repeatable</Repeatable>
        <ForemostTestPart>
          <PartNumber>
            <PreNumber>pre-number</PreNumber>
            <MiddleGroup>middle-group</MiddleGroup>
            <EndNumber>end-number</EndNumber>
          </PartNumber>
          <Hardware>hardware</Hardware>
          <Software>software</Software>
        </ForemostTestPart>
      </DevelopmentProblem>
    </ns2:CreateDevelopmentProblem>
  </ns0:Body>
</ns0:Envelope>"""
    )
    request = CreateDevelopmentProblemRequest(
        user_id=user_id,
        plant=plant,
        org_unit=org_unit,
        project=project,
        project_brand=project_brand,
        rating=rating,
        desc=desc,
        short_text=short_text,
        frequency=frequency,
        repeatable=repeatable,
        pre_number=pre_number,
        middle_group=middle_group,
        end_number=end_number,
        hardware=hardware,
        software=software,
        uuid=uuid,
    )
    assert request.to_string(indent=True) == reference
