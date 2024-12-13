import click
from rich.console import Console

from bb.core.git import (
    amend_commit,
    clean,
    commit,
    create_branch,
    create_tag,
    delete_branch,
    delete_tag,
    diff,
    fetch,
    get_config,
    list_tags,
    print_branch_list,
    print_status,
    pull,
    push,
    rename_branch,
    set_config,
    stash_list,
    stash_pop,
    stash_save,
)
from bb.typeshed import Ok, Result


@click.group()
def git():
    """Git operations"""
    pass


# Status Commands
@git.command(name="status")
@click.option("--short", "-s", is_flag=True, help="Show status in short format")
def status_cmd(short):
    """Show working tree status"""
    print_status()


@git.command(name="diff")
@click.option("--cached", "-c", is_flag=True, help="Show staged changes")
@click.argument("files", nargs=-1)
def diff_cmd(cached, files):
    """Show changes between commits, commit and working tree, etc"""
    result: Result = diff(cached, list(files) if files else None)
    if isinstance(result, Ok):
        print(result.unwrap())
    else:
        print(f"Error showing diff: {result.unwrap_err()}")


# Branch Commands
@git.group()
def branch():
    """Branch operations"""
    pass


@branch.command(name="list")
@click.option("--remote", "-r", is_flag=True, help="List remote branches")
def list_branches_cmd(remote):
    """List branches"""
    print_branch_list()


@branch.command(name="create")
@click.argument("name")
@click.option("--start-point", "-s", help="Starting point for new branch")
def create_cmd(name, start_point):
    """Create a new branch"""
    result = create_branch(name, start_point)
    if isinstance(result, Ok):
        print(f"Created branch '{name}'")
    else:
        print(f"Error creating branch: {result.unwrap_err()}")


@branch.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force delete branch")
def delete_cmd(name, force):
    """Delete a branch"""
    result = delete_branch(name, force)
    if isinstance(result, Ok):
        print(f"Deleted branch '{name}'")
    else:
        print(f"Error deleting branch: {result.unwrap_err()}")


@branch.command(name="rename")
@click.argument("old_name")
@click.argument("new_name")
def rename_cmd(old_name, new_name):
    """Rename a branch"""
    result = rename_branch(old_name, new_name)
    if isinstance(result, Ok):
        print(f"Renamed branch '{old_name}' to '{new_name}'")
    else:
        print(f"Error renaming branch: {result.unwrap_err()}")


# Commit Commands
@git.command(name="commit")
@click.option("--message", "-m", required=True, help="Commit message")
@click.argument("files", nargs=-1)
def commit_cmd(message, files):
    """Record changes to the repository"""
    result = commit(message, list(files) if files else None)
    if isinstance(result, Ok):
        print("Changes committed successfully")
    else:
        print(f"Error committing changes: {result.unwrap_err()}")


@git.command(name="amend")
@click.option("--message", "-m", help="New commit message")
def amend_cmd(message):
    """Amend the last commit"""
    result = amend_commit(message)
    if isinstance(result, Ok):
        print("Commit amended successfully")
    else:
        print(f"Error amending commit: {result.unwrap_err()}")


# Remote Operations
@git.command(name="pull")
@click.option("--remote", "-r", default="origin", help="Remote name")
@click.option("--branch", "-b", help="Branch name")
def pull_cmd(remote, branch):
    """Fetch from and integrate with another repository or branch"""
    with Console().status(f"Pulling from {remote}..."):
        result = pull(remote, branch)
    if isinstance(result, Ok):
        print("Pull successful")
    else:
        print(f"Error pulling changes: {result.unwrap_err()}")


@git.command(name="push")
@click.option("--remote", "-r", default="origin", help="Remote name")
@click.option("--branch", "-b", help="Branch name")
@click.option("--force", "-f", is_flag=True, help="Force push")
def push_cmd(remote, branch, force):
    """Update remote refs along with associated objects"""
    result = push(remote, branch, force)
    if isinstance(result, Ok):
        print("Push successful")
    else:
        print(f"Error pushing changes: {result.unwrap_err()}")


@git.command(name="fetch")
@click.option("--remote", "-r", help="Remote to fetch from")
@click.option("--all", "-a", is_flag=True, help="Fetch all remotes")
def fetch_cmd(remote, all):
    """Download objects and refs from another repository"""
    result = fetch(remote, all)
    if isinstance(result, Ok):
        print("Fetch successful")
    else:
        print(f"Error fetching: {result.unwrap_err()}")


# Stash Commands
@git.group()
def stash():
    """Stash operations"""
    pass


@stash.command(name="save")
@click.option("--message", "-m", help="Stash message")
def stash_save_cmd(message):
    """Save changes to stash"""
    result = stash_save(message)
    if isinstance(result, Ok):
        print("Changes stashed successfully")
    else:
        print(f"Error stashing changes: {result.unwrap_err()}")


@stash.command(name="pop")
@click.option("--index", "-i", default=0, help="Stash index to pop")
def stash_pop_cmd(index):
    """Pop changes from stash"""
    result = stash_pop(index)
    if isinstance(result, Ok):
        print("Stashed changes applied successfully")
    else:
        print(f"Error applying stashed changes: {result.unwrap_err()}")


@stash.command(name="list")
def stash_list_cmd():
    """List stashed changes"""
    result = stash_list()
    if isinstance(result, Ok):
        print(result.unwrap())
    else:
        print(f"Error listing stash: {result.unwrap_err()}")


# Tag Commands
@git.group()
def tag():
    """Tag operations"""
    pass


@tag.command(name="create")
@click.argument("name")
@click.option("--message", "-m", help="Tag message")
def create_tag_cmd(name, message):
    """Create a new tag"""
    result = create_tag(name, message)
    if isinstance(result, Ok):
        print(f"Created tag '{name}'")
    else:
        print(f"Error creating tag: {result.unwrap_err()}")


@tag.command(name="delete")
@click.argument("name")
def delete_tag_cmd(name):
    """Delete a tag"""
    result = delete_tag(name)
    if isinstance(result, Ok):
        print(f"Deleted tag '{name}'")
    else:
        print(f"Error deleting tag: {result.unwrap_err()}")


@tag.command(name="list")
def list_tags_cmd():
    """List tags"""
    result = list_tags()
    if isinstance(result, Ok):
        print(result.unwrap())
    else:
        print(f"Error listing tags: {result.unwrap_err()}")


# Config Commands
@git.group()
def config():
    """Config operations"""
    pass


@config.command(name="get")
@click.argument("key")
@click.option("--global", "-g", "global_", is_flag=True, help="Use global config")
def get_config_cmd(key, global_):
    """Get config value"""
    result = get_config(key, global_)
    if isinstance(result, Ok):
        print(result.unwrap().strip())
    else:
        print(f"Error getting config: {result.unwrap_err()}")


@config.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "-g", "global_", is_flag=True, help="Use global config")
def set_config_cmd(key, value, global_):
    """Set config value"""
    result = set_config(key, value, global_)
    if isinstance(result, Ok):
        print(f"Set {key}={value}")
    else:
        print(f"Error setting config: {result.unwrap_err()}")


# Cleanup Commands
@git.command()
@click.option("--force", "-f", is_flag=True, help="Force clean untracked files")
@click.option(
    "--directories", "-d", is_flag=True, help="Remove untracked directories too"
)
def clean_cmd(force, directories):
    """Clean untracked files from working tree"""
    result = clean(force, directories)
    if isinstance(result, Ok):
        print("Clean successful")
    else:
        print(f"Error cleaning: {result.unwrap_err()}")
