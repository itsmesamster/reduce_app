# standard
from dataclasses import dataclass, fields
from pprint import pprint

# 3rd party


# project core
from app.core.custom_logger import logger

# project extension
from app.ext.kpm_audi.kpm_client import KPMClient
from app.ext.kpm_audi.soap_responses.development_problem_data_response import (
    DevelopmentProblemDataResponse,
)

# project service
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import ESRLabsJiraClientForKpmSync
from app.service.hcp5.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync


# KPM vs Jira fields mapping
@dataclass(frozen=True)
class KpmJiraMap:
    Description: str = "description"


def compare_tickets(kpm_id: str, kpm: KPMClient, jira: ESRLabsJiraClientForKpmSync):
    # 1. query single problem from KPM
    kpm_issue: DevelopmentProblemDataResponse = kpm.issue(kpm_id)
    if kpm_issue:
        logger.debug(kpm_issue)
    else:
        logger.debug(f"KPM issue {kpm_id} not found in KPM", kpm_id=kpm_id)

    # 2. query single ticket from Jira
    jira_issue: EsrLabsJiraIssueForKpmSync = jira.issue_by_kpm_id(kpm_id)
    if not jira_issue:
        logger.debug(f"Jira issue for KPM {kpm_id} not found", kpm_id=kpm_id)

    # 3. diff
    if not kpm_issue or not jira_issue:
        logger.error("Failed to compare KPM and Jira tickets", kpm_id=kpm_id)
        return {}
    diff = {}

    # KPM
    kpm_dict: dict = kpm_issue.development_problem_as_dict().get(
        "DevelopmentProblem", {}
    )
    logger.debug(
        "\n\n\n\n\n######################## KPM: ########################### \n\n",
        kpm_id=kpm_id,
        jira_id=jira_issue.jira_id,
    )
    pprint(kpm_dict)

    # JIRA
    jira_dict: dict = jira_issue.get_all_fields()
    logger.debug(
        "\n\n\n\n\n######################## JIRA: ########################### \n\n",
        kpm_id=kpm_id,
        jira_id=jira_issue.jira_id,
    )
    pprint(jira_dict)

    # compare fields
    for field in fields(KpmJiraMap):
        kpm_field = kpm_dict.get(field.name, "")
        jira_field = jira_dict.get(getattr(KpmJiraMap, field.name), "")
        if kpm_field != jira_field:
            diff[field.name] = {"kpm": kpm_field, "jira": jira_field}

    if not diff:
        logger.info(
            f"KPM {kpm_id} and Jira {jira_issue.jira_id} tickets "
            "are identical [based on {KpmJiraMap()}]"
        )
    else:
        logger.error(
            "KPM and Jira tickets are different",
            kpm_id=kpm_id,
            jira_id=jira_issue.jira_id,
        )
        pprint(diff)

    return diff
