# standard
import sys

# external
import click

# project core
from app.core.custom_logger import logger
from app.core.utils import setup_logging, since_timestamp
from app.core.scheduler import scheduler
from app.core.jira.exceptions import JiraApiError

# project extension
from app.ext.kpm_audi.soap_responses.development_problem_data_response import (
    DevelopmentProblemDataResponse,
)
from app.ext.kpm_audi.soap_responses.process_steps_response import (
    ProcessStepItem,
    ProcessStepListResponse,
)
from app.ext.kpm_audi.kpm_client import KPMClient
from app.ext.kpm_audi.soap_responses.multiple_problem_data_response import (
    MultipleProblemDataResponse,
    ProblemReference,
)
from app.ext.kpm_audi.exceptions import KPMApiError

# project service
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import ESRLabsJiraClientForKpmSync
from app.service.hcp5.kpm2jira.jira_issue_k2j import EsrLabsJiraIssueForKpmSync
from app.service.hcp5.kpm2jira.compare import compare_tickets
from app.service.hcp5.kpm2jira.sync import KPMJiraMainSync, kpm_client
from app.service.hcp5.kpm2jira.jira_esr_client_k2j import esr_jira_client


##### CLI GROUP #####
@click.group(
    "cli",
    context_settings={
        "show_default": True,
        "max_content_width": 100,
    },
)
@click.pass_context
def cli(ctx) -> None:
    """
    Run KPM to Jira issue synchronization.
    """
    setup_logging()
    ctx.ensure_object(dict)


###### CLI/JIRA GROUP ######
@cli.group("jira")
@click.pass_context
def jira(ctx) -> None:
    """Interact with the Jira server."""
    ctx.obj["jira_client"] = esr_jira_client()


@jira.command()
@click.pass_context
@click.argument("issue_id")
def issue(ctx, issue_id: str) -> None:
    """Get Jira issue by ISSUE_ID

    ISSUE_ID is the jira issue id to look for.
    """
    try:
        client: ESRLabsJiraClientForKpmSync = ctx.obj["jira_client"]
        ticket: EsrLabsJiraIssueForKpmSync = client.issue(issue_id)
        click.echo(ticket)
        if ticket:
            click.echo(ticket.yaml)
    except JiraApiError as ex:
        sys.exit(f"Failed to request jira issue: {issue_id} -> {ex}")


@jira.command()
@click.pass_context
@click.argument("kpm_id")
def kpmid(ctx, kpm_id: str) -> None:
    """Get Jira issue by KPM ID (External Reference)"""
    try:
        client: ESRLabsJiraClientForKpmSync = ctx.obj["jira_client"]
        ticket: EsrLabsJiraIssueForKpmSync = client.issue_by_kpm_id(kpm_id)
        click.echo(ticket)
        if ticket:
            click.echo(ticket.yaml)
    except JiraApiError as ex:
        sys.exit(f"Failed to request jira issue: {kpm_id} -> {ex}")


@jira.command()
@click.pass_context
@click.argument("jql")
def query(ctx, jql: str) -> None:
    """Get Jira issue(s) by JQL

    JQL is is the jira query language string to search for.
    """
    try:
        client = ctx.obj["jira_client"]
        issues = client.query(jql)
        click.echo(f"Found {len(issues)} Jira issue for query: '{jql}'")
        click.echo("--------------------------------------------------")
        click.echo("Jira ID       URL")
        for ticket in issues:
            click.echo(f"{ticket.jira_id}   {ticket.url:15}")
    except JiraApiError as jira_error:
        sys.exit(f"Failed to request jira issues: '{jql}' -> {jira_error}")


##### CLI/KPM GROUP #####
@cli.group("kpm")
@click.pass_context
def kpm(ctx) -> None:
    """Interact with the KPM server."""
    ctx.obj["kpm_client"] = kpm_client()


@kpm.command()
@click.pass_context
@click.argument("issue_id")
def issue(ctx, issue_id: str) -> None:  # noqa: F811
    """Get KPM issue by ISSUE_ID

    ISSUE_ID is the KPM development problem number to look for.
    """
    try:
        client: KPMClient = ctx.obj["kpm_client"]
        ticket: DevelopmentProblemDataResponse = client.issue(issue_id)
        click.echo(ticket.summary())
        click.echo(ticket.development_problem_as_dict())
        click.echo(ticket.development_problem_as_yaml())
    except KPMApiError as ex:
        sys.exit(f"Failed to request KPM issue: {issue_id} -> {ex}")


@kpm.command()
@click.pass_context
@click.argument("kpm_id")
def processsteps(ctx, kpm_id: str) -> None:
    """Get KPM process step list by KPM ID"""
    try:
        client: KPMClient = ctx.obj["kpm_client"]
        response: ProcessStepListResponse = client.process_step_list(kpm_id)
        steps: list[ProcessStepItem] = response.as_list
        click.echo(f"Found {len(steps)} KPM process steps for issue: {kpm_id}.")
        click.echo("----------------------------------------------------------")
        for step in steps:
            client.process_step(kpm_id, step.step_id)
    except KPMApiError as ex:
        sys.exit(f"Failed to request KPM issue: {kpm_id} -> {ex}")


@kpm.command()
@click.pass_context
@click.argument("issue_id")
@click.argument("step_id")
def process_step(ctx, issue_id: str, step_id: str) -> None:
    """Get KPM process step by ISSUE_ID and STEP_ID

    ISSUE_ID is the KPM development problem number to look for.
    STEP_ID is the KPM process step id in form of "yyyy-mm-dd.hh.mm.ss.ms"
    """
    try:
        client = ctx.obj["kpm_client"]
        step = client.process_step(issue_id, step_id)
        click.echo(step.to_string())
    except KPMApiError as ex:
        sys.exit(f"Failed to request KPM issue: {issue_id} -> {ex}")


@kpm.command()
@click.pass_context
@click.option("--since", default=since_timestamp(), help="Last changed date")
def query(ctx, since: str) -> None:  # noqa: F811
    """Get all KPM issue(s) SINCE given timestamp and by PROJECT.

    SINCE is the timestamp when the last change was done.
    All changes with a newer timestamp are included.
          Example: "2022-12-15 09:00.00.0"
    PROJECT is the project name to look for.
    """
    try:
        client: KPMClient = ctx.obj["kpm_client"]
        response: MultipleProblemDataResponse = client.query(since=since)
        issues: list[ProblemReference] = response.problem_references()
        click.echo(f"Found {len(issues)} KPM issues changed since: {since}")
        click.echo("--------------------------------------------------")
        for ticket in issues:
            click.echo(ticket.summary)
    except KPMApiError as kpm_error:
        sys.exit(
            "Failed to request KPM issues -> "
            f"{kpm_error.__class__.__name__} {kpm_error}"
        )


@cli.group("k2j")
@click.pass_context
def k2j(ctx) -> None:
    """Interact with KPM and JIRA."""
    pass


@k2j.command()
@click.pass_context
@click.argument("kpm_id")
def diff(ctx, kpm_id: str) -> None:
    """See compared KPM problem vs JIRA ticket diff by KPM_ID (External Reference)

    KPM_ID is the KPM development problem number to look for in KPM and JIRA
    """
    try:
        compare_tickets(kpm_id, ctx.obj["kpm_client"], ctx.obj["jira_client"])
    except JiraApiError as ex:
        sys.exit(f"Failed to request Jira issue: {kpm_id=} -> {ex}")
    except KPMApiError as ex:
        sys.exit(f"Failed to request KPM issue: {kpm_id=} -> {ex}")
    except Exception as ex:
        sys.exit(
            f"Failed to compare KPM {kpm_id} ticket with Jira: "
            f"{ex.__class__.__name__} -> {ex}"
        )


@k2j.command()
@click.argument("kpm_id")
def syncone(kpm_id: str) -> None:
    """Create a new Jira issue by KPM ID (External Reference)"""
    click.echo("Starting sync one from cli ...")
    try:
        jira_ticket = KPMJiraMainSync().sync_one(kpm_id)

        if jira_ticket:
            logger.info(
                "\n\n\n#################### "
                f"Sync done for {jira_ticket} | KPM {kpm_id} "
                "####################\n\n\n"
            )
        else:
            logger.error(f"Failed to sync KPM ID: {kpm_id}")

    except JiraApiError as ex:
        logger.error(f"Failed to create jira issue: {kpm_id} -> {ex}")

    except KPMApiError as ex:
        logger.error(
            "Failed to request KPM issues -> " f"{ex.__class__.__name__} {ex}",
            kpm_id=kpm_id,
        )
    except Exception as ex:
        logger.error(
            "Failed to sync KPM issue -> " f"{ex.__class__.__name__} {ex}",
            kpm_id=kpm_id,
        )


@k2j.command()
@click.argument("kpm_id")
def sync1noerrcatch(kpm_id: str) -> None:
    """Create a new Jira issue by KPM ID (External Reference)"""
    jira_ticket = KPMJiraMainSync().sync_one(kpm_id)

    if jira_ticket:
        logger.info(
            "\n\n\n#################### "
            f"Sync done for {jira_ticket} | KPM {kpm_id} "
            "####################\n\n\n"
        )
    else:
        logger.error(f"Failed to sync KPM ID: {kpm_id}")


@k2j.command()
@click.option("--since", default=since_timestamp(), help="Last changed date")
def sync(since) -> None:
    """Create many new Jira issue by KPM IDS list from kpm query (External Reference)"""
    click.echo("Starting main sync from cli ...")
    KPMJiraMainSync().sync(since)


@k2j.command()
def scheduledsync() -> None:
    """Start Scheduled Sync"""
    click.echo("Starting main scheduled sync from cli ...")
    scheduler(KPMJiraMainSync().sync)
