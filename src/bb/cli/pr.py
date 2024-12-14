import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from bb.core.git import (
    edit_tmp_file,
    get_branch,
    get_current_branch,
    get_current_diff_to_main,
    get_default_branch,
    push_branch,
)
from bb.exceptions import GitPushRejectedException, IPWhitelistException
from bb.models import Repository, User
from bb.utils import repo_context_command
from bb.live_table import SelectableRow, generate_live_table

console = Console()


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
    help="Show only pullrequests I'm reviewing",
    default=False,
)
@repo_context_command
def list(repo_slug, _all, mine, reviewing):
    """Fetch open pullrequests from current repository"""
    workspace, slug = repo_slug.split("/")
    repo = Repository(workspace=workspace, slug=slug)

    with Console().status("Fetching pull requests..."):
        try:
            result = repo.pullrequests.list(_all=_all, reviewing=reviewing, mine=mine)
            prs = result.unwrap()
        except Exception as e:
            print(f"{e}")
            return

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
        table.add_row(
            f"[link={pr.web_url}]{pr.id}[/link]",
            pr.author,
            pr.title,
            ",".join(pr.approvals),
        )
    console.print(table)


@pr.command()
@click.option(
    "--src", "-s", help="Source branch for pull request (default [current branch])"
)
@click.option(
    "--dest",
    "-d",
    help="Destination branch for pull request (default [current branch])",
)
@click.option(
    "--close-source-branch",
    "-c",
    is_flag=True,
    default=True,
    help="Close source branch after merge [bool]",
)
@repo_context_command
def create(repo_slug, close_source_branch, src, dest):
    workspace, slug = repo_slug.split("/")
    repo = Repository(workspace=workspace, slug=slug)

    if not src:
        src = get_current_branch().unwrap()
    else:
        try:
            src = get_branch(src).unwrap()
        except Exception:
            console.print(f"[bold red]Unable to find branch {src}")
            return

    dest = dest or get_default_branch().unwrap()

    console.print(
        f"Creating new pull request for [bold blue]{src}[/] into [bold blue]{dest}[/] for {repo_slug}"
    )
    if not get_current_diff_to_main().unwrap():
        return console.print("[bold red]Aborting - no changes on local branch")

    with Console().status("Pushing local branch"):
        try:
            push_branch(src).unwrap()
        except (GitPushRejectedException, IPWhitelistException) as e:
            console.print(f"[bold red]Error pushing {src}")
            console.print(f"[bold red]{e}")
            return

    # Generate default description
    with Console().status("Generating PR Description"):
        default_desc = repo.get_default_description(src, dest).unwrap()
        try:
            title, description = edit_tmp_file(
                default_desc.format_for_editor()
            ).unwrap()
        except ValueError:
            console.print("[bold red]Aborting due to empty description")
            return

    # Fetch 'effective_reviewers' which should be the total set of default reviewers
    # and CODEOWNERS defined reviewers - pre-selected, and some number of recommended reviewers - un-selected.
    # Generate a list of `live_table` rows that have all of these users pre-selected
    with Console().status("Calculating effective reviewers"):
        effective_reviewers = repo.get_effective_reviewers(src, dest).unwrap()
        # recommended_reviewers = recommended_result.json()

    with Console().status("Fetching recommended reviewers"):
        recommended_reviewers = repo.get_recommended_reviewers(src, dest).unwrap()

    rows = []

    for rev in recommended_reviewers:
        # Look ahead into effective reviewers, if the user is already in there, dont add them
        if (
            rev not in effective_reviewers
            and rev.uuid != User.from_current_config().uuid
        ):
            name = Text(rev.display_name)
            name.apply_meta({"uuid": rev.uuid})
            rows.append(SelectableRow([name], selected=False))

    # Effective reviewers should be added by default
    for er in effective_reviewers:
        if er.uuid != User.from_current_config().uuid:
            name = Text(er.display_name, style="bold magenta")
            name.apply_meta({"uuid": er.uuid})
            rows.append(SelectableRow([name], selected=True))

    selected_reviewers = [
        User(display_name=u[0].plain, uuid=u[0].spans[0].style.meta["uuid"])
        for u in generate_live_table(
            "\n\n[bold]Select Reviewers[/bold]\n(space to select, enter to submit)",
            ["name"],
            rows,
        )
    ]

    try:
        with Console().status("Creating pull request"):
            result = repo.pullrequests.create(
                title=title,
                source_branch=src,
                dest_branch=dest,
                description=description,
                reviewers=selected_reviewers,
            )
            pr = result.unwrap()
            console.print(f"Successfully created PR - {pr.web_url}")
    except Exception as exc:
        console.print(f"[bold red]Aborting: {str(exc)}")


@pr.command()
@repo_context_command
def review(repo_slug):
    """Interactive TUI for reviewing pull requests"""
    from bb.tui import review_prs

    review_prs(repo_slug)
