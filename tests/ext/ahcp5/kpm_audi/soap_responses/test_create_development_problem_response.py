from app.ext.kpm_audi.soap_responses.create_development_problem_response import (
    CreateDevelopmentProblemResponse,
)


def create_development_porblem_reponse_body():
    return (
        '<ns2:CreateDevelopmentProblemResponse xmlns:ns2="http://xmldefs.volkswagenag.com/PP/QM/GroupProblemManagementService/V3">'
        "<CreateDevelopmentProblemResponseInternal>"
        "<DevelopmentProblemStatusResponseInternal>"
        "<ProblemNumber>12345</ProblemNumber>"
        "</DevelopmentProblemStatusResponseInternal>"
        "</CreateDevelopmentProblemResponseInternal>"
        "</ns2:CreateDevelopmentProblemResponse>"
    )


def test_response(make_mtom_soap_response):
    body = create_development_porblem_reponse_body()
    response = CreateDevelopmentProblemResponse(
        make_mtom_soap_response(soap_body_content=body)
    )
    assert response.problem_number == "12345"
