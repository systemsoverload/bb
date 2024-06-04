import click
from rich.console import Console
from rich.table import Table

from bb.api import WEB_BASE_URL, get_prs
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
    prs = get_prs(repo_slug, _all, reviewing, mine)

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
        title =f"PR {_all}{reviewing}{mine}"

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
