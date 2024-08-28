# standard
import sys

# external
import click

# project core
from app.core.jira.exceptions import JiraApiError

# project extension
from app.ext.jira_audi.jira_client import VwAudiJiraClient


# project service
from app.service.hcp5.jira2jira.j2j_custom_logger import logger
from app.service.hcp5.jira2jira.sync import HCP5JiraJiraMainSync

from app.service.hcp5.jira2jira.jira_issue_esr4vw import EsrIssueForVwJiraSync
from app.service.hcp5.jira2jira.jira_client_esr_j2j import (
    ESRLabsJiraClientForVwJiraSync,
    j2j_esr_jira_client,
)

from app.service.hcp5.jira2jira.jira_issue_vwaudi import Hcp5VwAudiJiraIssue
from app.service.hcp5.jira2jira.jira_client_vwaudi import (
    j2j_vw_jira_client,
)


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
    CLI for VW/Audi Jira to ESR Labs Jira issue synchronization.
    """
    ctx.ensure_object(dict)


##### CLI ESR Labs Jira GROUP #####
@cli.group("esr")
@click.pass_context
def esr(ctx) -> None:
    """Interact with the Jira server."""
    ctx.obj["esr_jira_client"] = j2j_esr_jira_client()


@esr.command()
@click.pass_context
@click.argument("issue_id")
def issue(ctx, issue_id: str) -> None:
    """Get Jira issue by ISSUE_ID

    ISSUE_ID is the jira issue id to look for.
    """
    try:
        esr_client: ESRLabsJiraClientForVwJiraSync = ctx.obj["esr_jira_client"]
        ticket: EsrIssueForVwJiraSync = esr_client.issue(issue_id)
        click.echo(ticket)
        if ticket:
            click.echo(ticket.yaml)
    except JiraApiError as ex:
        sys.exit(f"Failed to request jira issue: {issue_id} -> {ex}")


@esr.command()
@click.pass_context
@click.argument("vw_id")
def vwid(ctx, vw_id: str) -> None:
    """Get Jira issue by VW Jira ID (External Reference)"""
    try:
        client: ESRLabsJiraClientForVwJiraSync = ctx.obj["esr_jira_client"]
        ticket: EsrIssueForVwJiraSync = client.issue_by_vw_id(vw_id)
        click.echo(ticket)
        if ticket:
            click.echo(ticket.yaml)
    except JiraApiError as ex:
        sys.exit(f"Failed to request jira issue: {vw_id} -> {ex}")


@esr.command()
@click.pass_context
@click.argument("jql")
def query(ctx, jql: str) -> None:
    """Get ESR Labs Jira issue(s) by JQL

    JQL is is the jira query language string to search for.
    """
    try:
        client: ESRLabsJiraClientForVwJiraSync = ctx.obj["esr_jira_client"]
        issues = client.query(jql)
        click.echo(f"Found {len(issues)} Jira issue for query: '{jql}'")
        click.echo("--------------------------------------------------")
        click.echo("Jira ID       URL")
        for ticket in issues:
            click.echo(f"{ticket.jira_id}   {ticket.url:15}")
    except JiraApiError as jira_error:
        sys.exit(f"Failed to request jira issues: '{jql}' -> {jira_error}")


##### CLI VW Audi Jira GROUP #####
@cli.group("vw")
@click.pass_context
def vw(ctx) -> None:
    """Interact with the VW server."""
    ctx.obj["vw_jira_client"] = j2j_vw_jira_client()


@vw.command()
@click.pass_context
@click.argument("issue_id")
def issue(ctx, issue_id: str) -> None:  # noqa: F811
    """Get Jira issue by ISSUE_ID

    ISSUE_ID is the jira issue id to look for.
    """
    try:
        esr_client: VwAudiJiraClient = ctx.obj["vw_jira_client"]
        ticket: Hcp5VwAudiJiraIssue = esr_client.issue(issue_id)
        click.echo(ticket)
        if ticket:
            click.echo(ticket.yaml)
    except JiraApiError as ex:
        sys.exit(f"Failed to request jira issue: {issue_id} -> {ex}")


@vw.command()
@click.pass_context
@click.argument("jql")
def query(ctx, jql: str) -> None:  # noqa: F811
    """Get VW Audi Jira issue(s) by JQL

    JQL is is the jira query language string to search for.
    """
    try:
        client: ESRLabsJiraClientForVwJiraSync = ctx.obj["vw_jira_client"]
        issues = client.query(jql)
        click.echo(f"Found {len(issues)} Jira issue for query: '{jql}'")
        click.echo("--------------------------------------------------")
        click.echo("Jira ID       URL")
        for ticket in issues:
            click.echo(f"{ticket.jira_id}   {ticket.url:15}")
    except JiraApiError as jira_error:
        sys.exit(f"Failed to request jira issues: '{jql}' -> {jira_error}")


##### CLI VW Audi to ESR Labs Jira to Jira Sync GROUP #####
@cli.group("j2j")
@click.pass_context
def j2j(ctx) -> None:
    """CLI VW Audi to ESR Labs Jira to Jira Sync GROUP"""
    ctx.obj["vw_jira_client"] = j2j_vw_jira_client()
    ctx.obj["esr_jira_client"] = j2j_esr_jira_client()


@j2j.command()
@click.pass_context
@click.argument("vw_id")
def syncone(ctx, vw_id: str) -> None:
    """Create a new Jira issue by VW Jira ID (External Reference)"""
    click.echo("Starting sync one from cli ...")
    try:
        jira_ticket = HCP5JiraJiraMainSync().sync_one(vw_id)

        if jira_ticket:
            logger.info(
                "\n\n\n#################### "
                f"Sync done for {jira_ticket} | VW Jira ID {vw_id} "
                "####################\n\n\n"
            )
        else:
            logger.error(f"Failed to sync VW Jira ID: {vw_id}")

    except JiraApiError as ex:
        logger.error(f"Failed to create jira issue: {vw_id} -> {ex}")

    except Exception as ex:
        logger.error(
            "Failed to sync VW Jira issue -> " f"{ex.__class__.__name__} {ex}",
            vw_id=vw_id,
        )


# dev
@j2j.command()
@click.pass_context
@click.argument("vw_id")
def sync1noerrcatch(ctx, vw_id: str) -> None:
    """Create a new Jira issue by VW Jira ID (External Reference)"""
    jira_ticket = HCP5JiraJiraMainSync().sync_one(vw_id)

    if jira_ticket:
        logger.info(
            "\n\n\n#################### "
            f"Sync done for {jira_ticket} | VW {vw_id} "
            "####################\n\n\n"
        )
    else:
        logger.error(f"Failed to sync VW Jira ID: {vw_id}")


@j2j.command()
@click.pass_context
def sync(ctx) -> None:
    """Create many new Jira issue by KPM IDS list from kpm query (External Reference)"""
    click.echo("Starting main sync from cli ...")
    HCP5JiraJiraMainSync().sync()
