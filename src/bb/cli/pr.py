import click
from requests.exceptions import HTTPError
from rich import print
from rich.console import Console
from rich.table import Table
from rich.text import Text

from bb.core.api import (WEB_BASE_URL, create_pr, get_codeowners,
                         get_default_description, get_prs,
                         get_recommended_reviewers)
from bb.core.git import (GitPushRejectedException, IPWhitelistException,
                         edit_tmp_file, get_branch, get_current_branch,
                         get_current_diff_to_main, get_default_branch,
                         push_branch)
from bb.live_table import SelectableRow, generate_live_table
from bb.typeshed import User
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
            f"[link={WEB_BASE_URL}/{repo_slug}/pull-requests/{pr['id']}]{pr['id']}[/link]",
            pr["author"]["display_name"],
            pr["title"],
            ",".join(approvers),
        )
    console = Console()
    console.print(table)


@pr.command()
# TODO - Should we allow manual inputs here? Do we need to prompt the user for this data if the API call fails?
# @click.option("--title", "-t", help="PR title")
# @click.option("--description", "-d", help="PR description")
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

    # Fetch the generated default description from BB API and open configured editor
    with Console().status("Generating PR Description"):
        dd_res = get_default_description(repo_slug, src, dest).unwrap().json()
        try:
            title, description = edit_tmp_file(
                f"{dd_res['title']}\n------\n{dd_res['description']}"
            ).unwrap()
        except ValueError:
            print("[bold red]Aborting due to empty description")
            return

    reviewers = []
    with Console().status("Calculating CODEOWNERS"):
        code_owners = get_codeowners(repo_slug, src, dest).unwrap().json()

    reviewers.extend(code_owners)

    with Console().status("Calculating recommended reviewers"):
        recommended_reviewers = get_recommended_reviewers(repo_slug).unwrap().json()

    headers = ["name"]
    rows = []

    # Wrap reviewer names in Text objects to apply UUID as hidden meta data
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

    reviewers = [
        User(display_name=u[0].plain, uuid=u[0].spans[0].style.meta["uuid"])
        for u in generate_live_table(
            "\n\n[bold]Select Reviewers[/bold]\n(space to select, enter to submit)",
            headers,
            rows,
        )
    ]

    try:
        with Console().status("Creating pull request"):
            res = create_pr(
                repo_slug, title, src, dest, description, close_source_branch, reviewers
            ).unwrap()
        print(f"Successfully created PR - {res.json()['links']['html']['href']}")
    except HTTPError as exc:
        # TODO - Handle possible errors here - eg 400 if no diff commits in branch
        print(f"[bold red]Aborting: {exc.response.json()['error']['message']}")


@pr.command()
@repo_context_command
def review(repo_slug):
    """Interactive TUI for reviewing pull requests"""
    from bb.tui import review_prs

    review_prs(repo_slug)
