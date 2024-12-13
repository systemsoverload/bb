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
    console = Console()
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
            print(f"[bold red]Unable to find branch {src}")
            return

    dest = dest or get_default_branch().unwrap()

    print(
        f"Creating new pull request for [bold blue]{src}[/] into [bold blue]{dest}[/] for {repo_slug}"
    )
    if not get_current_diff_to_main().unwrap():
        return print("[bold red]Aborting - no changes on local branch")

    with Console().status("Pushing local branch"):
        try:
            push_branch(src).unwrap()
        except (GitPushRejectedException, IPWhitelistException) as e:
            print(f"[bold red]Error pushing {src}")
            print(f"[bold red]{e}")
            return

    # Generate default description
    with Console().status("Generating PR Description"):
        desc_result = repo.pullrequests.get_default_description(src, dest).unwrap()
        try:
            title, description = edit_tmp_file(
                f"{desc_result['title']}\n------\n{desc_result['description']}"
            ).unwrap()
        except ValueError:
            print("[bold red]Aborting due to empty description")
            return

    reviewers = []
    with Console().status("Calculating CODEOWNERS"):
        code_owners_result = repo.pullrequests.get_codeowners(src, dest).unwrap()
        code_owners = code_owners_result.json()
        reviewers.extend(code_owners)

    with Console().status("Calculating recommended reviewers"):
        recommended_result = repo.pullrequests.get_recommended_reviewers().unwrap()
        recommended_reviewers = recommended_result.json()

    headers = ["name"]
    rows = []

    # Process reviewers for selection
    owner_names = [c["display_name"] for c in code_owners]
    for rev in recommended_reviewers:
        if rev["display_name"] not in owner_names:
            name = Text(rev["display_name"])
            name.apply_meta({"uuid": rev["uuid"]})
            rows.append(SelectableRow([name], selected=False))

    for co in code_owners:
        name = Text(co["display_name"], style="bold magenta")
        name.apply_meta({"uuid": co["uuid"]})
        rows.append(SelectableRow([name], selected=True))

    selected_reviewers = [
        User(display_name=u[0].plain, uuid=u[0].spans[0].style.meta["uuid"])
        for u in generate_live_table(
            "\n\n[bold]Select Reviewers[/bold]\n(space to select, enter to submit)",
            headers,
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
            print(f"Successfully created PR - {pr.web_url}")
    except Exception as exc:
        print(f"[bold red]Aborting: {str(exc)}")
