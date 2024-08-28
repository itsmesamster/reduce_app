from app.ext.kpm_audi.soap_responses.process_steps_response import (
    ProcessStepItem,
    ProcessStepListResponse,
)


def get_process_step_list_response_body():
    return (
        '<ns5:GetProcessStepListResponse xmlns:ns5="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">'
        "<GetProcessStepListResponse>"
        "<ProcessStepItem>"
        "<ProblemNumber>12345</ProblemNumber>"
        "<ProcessStepId>2023-01-01-00.00.00.000000</ProcessStepId>"
        "<LastChangeDate>2023-01-01-00.00.00.000001</LastChangeDate>"
        "<ProcessStepType>01</ProcessStepType>"
        "<ProcessStepTypeDescription>Description1</ProcessStepTypeDescription>"
        "<Status>1</Status>"
        "<SenderRole>R</SenderRole>"
        "</ProcessStepItem>"
        "<ProcessStepItem>"
        "<ProblemNumber>6789</ProblemNumber>"
        "<ProcessStepId>2023-01-01-00.00.00.000002</ProcessStepId>"
        "<LastChangeDate>2023-01-01-00.00.00.000003</LastChangeDate>"
        "<ProcessStepType>02</ProcessStepType>"
        "<ProcessStepTypeDescription>Description2</ProcessStepTypeDescription>"
        "<Status>2</Status>"
        "<SenderRole>S</SenderRole>"
        "</ProcessStepItem>"
        "</GetProcessStepListResponse>"
        "</ns5:GetProcessStepListResponse>"
    )


def test_response(make_mtom_soap_response):
    body = get_process_step_list_response_body()
    response = ProcessStepListResponse(make_mtom_soap_response(soap_body_content=body))
    assert len(response.as_list) == 2
    step1: ProcessStepItem = response.as_list[0]
    assert step1.problem_number == "12345"
    assert step1.last_change_date == "2023-01-01-00.00.00.000001"
    assert step1.step_id == "2023-01-01-00.00.00.000000"
    assert step1.step_type == "01"
    assert step1.step_type_desc == "Description1"
    assert step1.sender_role == "R"
    assert step1.status == "1"
    step2 = response.as_list[1]
    assert step2.problem_number == "6789"
    assert step2.last_change_date == "2023-01-01-00.00.00.000003"
    assert step2.step_id == "2023-01-01-00.00.00.000002"
    assert step2.step_type == "02"
    assert step2.step_type_desc == "Description2"
    assert step2.sender_role == "S"
    assert step2.status == "2"
