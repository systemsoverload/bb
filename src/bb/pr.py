import click
from rich import print
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from bb.api import WEB_BASE_URL, create_pr, get_prs
from bb.git import (
    IPWhitelistException,
    get_branch,
    get_current_branch,
    get_default_branch,
    push_branch,
)
from bb.utils import repo_context_command


@click.group()
def pr():
    pass


@pr.command()
@click.option(
    "--all",
    "-a",
    "_all",
    is_flag=True,
    help="Show all open pullrequests",
    default=False,
)
@click.option(
    "--mine",
    "-m",
    is_flag=True,
    help="Show only my open pullrequests",
    default=False,
)
@click.option(
    "--reviewing",
    "-r",
    is_flag=True,
    help="Show only my open pullrequests",
    default=False,
)
@repo_context_command
def list(repo_slug, _all, mine, reviewing):
    """Fetch your open pullrequests from current repository"""
    with Console().status("Fetching pull requests..."):
        try:
            prs = get_prs(repo_slug, _all, reviewing, mine).unwrap()
        except IPWhitelistException as e:
            print(f"{e}")
            return

    # Default to --mine, cant quite figure out how to do this in click.option directly
    if not any([_all, reviewing, mine]):
        mine = True

    if _all:
        title = "All open pullrequests"
    elif reviewing:
        title = "Open pullrequests I'm reviewing"
    elif mine:
        title = "My open pullrequests"
    else:
        title = f"PR {_all}{reviewing}{mine}"

    table = Table(title=title)
    table.add_column("Id", justify="left", style="cyan")
    table.add_column("author", style="magenta")
    table.add_column("Title")
    table.add_column("Approvals", style="green", justify="right", no_wrap=True)

    for pr in prs:
        approvers = []
        for p in pr.get("participants", []):
            if p["approved"]:
                approvers.append(p["user"]["display_name"])
        table.add_row(
            f"[link={WEB_BASE_URL}{repo_slug}/pull-requests/{pr['id']}]{pr['id']}[/link]",
            pr["author"]["display_name"],
            pr["title"],
            ",".join(approvers),
        )
    console = Console()
    console.print(table)


@pr.command()
@click.option("--title", "-t", help="PR title")
@click.option("--description", "-d", help="PR description")
@click.option("--src", "-s", help="Source branch for pull request (default [current branch])")
@click.option("--dest", "-d", help="Destination branch for pull request (default [current branch])")
@click.option("--close-source-branch", "-c", is_flag=True, default=True, help="Close source branch after merge [bool]")
@repo_context_command
def create(repo_slug, title, description, close_source_branch, src, dest):
    # TODO - Check if the PR exists on BB already

    if not src:
        src = get_current_branch().unwrap()
    else:
        try:
            src = get_branch(src).unwrap()
        except Exception:
            print(f"[bold red]Unable to find branch {src}")
            return

    dest = dest or get_default_branch().unwrap()

    # If branch not pushed, do it now
    try:
        push_branch(src).unwrap()
    except IPWhitelistException as e:
        print(f"[bold red]{e}")
        return

    # TODO - Fetch description template and do something cool with it?

    print(f"Create new pull request for [bold blue]{src}[/] into [bold blue]{dest}[/] for {repo_slug}")

    if not title:
        title = Prompt.ask("[bold]Title")
    if not description:
        description = Prompt.ask("[bold]Description (enter to default to generated description)")

    with Console().status("Creating pull request"):
        res = create_pr(repo_slug, title, src, dest, description, close_source_branch).unwrap()
    print(f"Successfully created PR - {res.json()['links']['html']['href']}")
