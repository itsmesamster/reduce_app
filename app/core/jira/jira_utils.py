# project core
from app.core.custom_logger import logger


def process_jira_error_msg(html_msg: str):
    title, description = "", ""

    try:
        if title := html_msg.rsplit("</title>"):
            title = title[0].split("<title>")[-1]
        description = html_msg.split("<b>Description</b>")[1].split("<")[0]
    except (ValueError, IndexError):
        pass

    msg = f"{title}\n->{description}" if description else title
    return msg


def aggregated_tickets_link(server_url: str, jira_ids: list[str]) -> str:
    """Create an UI Jira URL to check all the tickets mentioned"""
    if server_url and server_url[-1] != "/":
        server_url += "/"

    if not jira_ids:
        logger.warning(f"No tickets to show for {server_url}")
        return ""

    jira_ids.sort()
    tickets_link = (
        f"{server_url}browse/{jira_ids[-1]}?jql="
        "issuekey%20in%20(" + "%2C%20".join(jira_ids) + ")"  # issuekey in (...)
    )
    logger.info(f"Link to all synced tickets: {tickets_link}")
    return tickets_link
