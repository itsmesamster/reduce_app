from app.core.jira.jira_utils import (
    process_jira_error_msg,
    aggregated_tickets_link,
)


JIRA_ERR_MSG_DESCRIPTION = (
    " The server is currently unable to handle "
    "the request due to a temporary overload or "
    "scheduled maintenance, which will likely "
    "be alleviated after some delay."
)

JIRA_ERR_MSG_EXAMPLE = f"""
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <title>HTTP Status 503 – Service Unavailable</title>
                <style type="text/css">...</style>
            </head>
            <body>
                <h1>HTTP Status 503 – Service Unavailable</h1>
                <hr class="line" />
                <p><b>Type</b> Status Report</p>
                <p><b>Message</b> Service Unavailable</p>
                <p><b>Description</b>{JIRA_ERR_MSG_DESCRIPTION}</p>
                <hr class="line" />
                <h3>Apache Tomcat/9.0.68</h3>
            </body>
        </html>"""


def test_process_jira_error_msg(caplog):
    result = process_jira_error_msg(JIRA_ERR_MSG_EXAMPLE)
    assert result == (
        "HTTP Status 503 – Service Unavailable"
        "\n-> The server is currently unable to handle the request due to "
        "a temporary overload or scheduled maintenance, which will likely "
        "be alleviated after some delay."
    )


def test_create_aggregated_tickets_link(caplog):
    # Test with a valid server URL and list of JIRA IDs
    url = "https://example.com"
    jira_ids = ["ABC-123", "DEF-456"]
    result = aggregated_tickets_link(url, jira_ids)
    assert result == f"{url}/browse/DEF-456?jql=issuekey%20in%20(ABC-123%2C%20DEF-456)"
