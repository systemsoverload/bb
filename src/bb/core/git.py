import os
import shlex
from subprocess import STDOUT, CalledProcessError, check_output
from tempfile import NamedTemporaryFile
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from bb.exceptions import GitPushRejectedException, IPWhitelistException
from bb.typeshed import Err, Ok, Result
from bb.version import get_user_agent

BB_CLIENT_ID = get_user_agent()


class GitCommand:
    """Wrapper for git commands with validation and error handling"""

    def __init__(self, command: str, *args, check_repo: bool = True):
        self.command = command
        self.args = args
        self.check_repo = check_repo

    def run(self, universal_newlines: bool = True) -> Result:
        """Execute the git command with proper environment and error handling"""
        if self.check_repo and not is_git_repo():
            return Err(RuntimeError("Not a git repository"))

        cmd = f"git {self.command} {' '.join(str(arg) for arg in self.args)}"
        try:
            env = _prepare_git_env()
            return Ok(
                check_output(
                    shlex.split(cmd),
                    universal_newlines=universal_newlines,
                    stderr=STDOUT,
                    env=env,
                ).strip()
            )
        except CalledProcessError as e:
            if "whitelist your IP" in getattr(e, "output", ""):
                return Err(IPWhitelistException(e.output))
            return Err(e)


def _prepare_git_env():
    """Prepare environment variables for git commands with client identification"""
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o SendEnv=BB_CLIENT_ID"
    env["BB_CLIENT_ID"] = BB_CLIENT_ID
    try:
        check_output(
            shlex.split(f'git config --global http.useragent "{BB_CLIENT_ID}"'),
            universal_newlines=True,
            env=env,
        )
    except CalledProcessError:
        pass
    return env


def is_git_repo() -> bool:
    """Check if current directory is a git repository"""
    try:
        check_output(["git", "rev-parse", "--git-dir"], stderr=STDOUT)
        return True
    except CalledProcessError:
        return False


# Repository Information Commands
def get_current_repo_slug() -> Result:
    """Get the Bitbucket repository slug from remote URL"""
    cmd = GitCommand("remote", "-v")
    try:
        out = cmd.run().unwrap()
        first_line = out.splitlines()[0].replace("\t", " ").split(" ")[1].strip()
        if "bitbucket" in first_line:
            return Ok(first_line.split(":")[-1][0:-4])
        return Err(RuntimeError("No Bitbucket repository detected"))
    except Exception as e:
        return Err(e)


def get_remotes() -> Result:
    """Get list of configured remotes"""
    return GitCommand("remote", "-v").run()


def get_remote_url(remote: str = "origin") -> Result:
    """Get URL for specified remote"""
    return GitCommand("remote", "get-url", remote).run()


# Branch Operations
def get_current_branch() -> Result:
    """Get name of current branch"""
    return GitCommand("rev-parse", "--abbrev-ref", "HEAD").run()


def get_branch(branch_name: str) -> Result:
    """Get the full branch name from a branch reference"""
    return GitCommand("rev-parse", "--abbrev-ref", branch_name).run()


def get_all_branches(remote: bool = False) -> Result:
    """Get list of all branches"""
    args = ["--list", "--format=%(refname:short)"]
    if remote:
        args.append("--remote")
    return GitCommand("branch", *args).run()


def create_branch(name: str, start_point: Optional[str] = None) -> Result:
    """Create a new branch"""
    args = [name]
    if start_point:
        args.append(start_point)
    return GitCommand("checkout", "-b", *args).run()


def delete_branch(name: str, force: bool = False) -> Result:
    """Delete a branch"""
    args = ["-d"]
    if force:
        args = ["-D"]
    args.append(name)
    return GitCommand("branch", *args).run()


def rename_branch(old_name: str, new_name: str) -> Result:
    """Rename a branch"""
    return GitCommand("branch", "-m", old_name, new_name).run()


def push_branch(branch_name: Optional[str] = None) -> Result:
    """Push a branch to origin. If no branch name provided, pushes current branch."""
    try:
        if not branch_name:
            current_branch = get_current_branch().unwrap()
            branch_name = current_branch.strip()

        with Console().status(f"[bold]Pushing {branch_name} to origin..."):
            result = GitCommand("push", "origin", branch_name).run()

            if isinstance(result, Ok):
                return result

            # At this point we know it's an Err so unwrap_err is safe
            error = result.unwrap_err()
            if hasattr(error, "output"):
                output = error.output
                if "[rejected]" in output:
                    return Err(GitPushRejectedException(output))
                elif "whitelist your IP" in output:
                    return Err(IPWhitelistException(output))
                else:
                    # Include the actual git error output in the error message
                    return Err(RuntimeError(f"Failed to push branch: {output}"))
            return result

    except Exception as e:
        return Err(RuntimeError(f"Unexpected error pushing branch: {str(e)}"))


# Commit Operations
def commit(message: str, files: Optional[List[str]] = None) -> Result:
    """Create a commit"""
    if files:
        GitCommand("add", *files).run()
    return GitCommand("commit", "-m", message).run()


def amend_commit(message: Optional[str] = None) -> Result:
    """Amend the last commit"""
    args = ["--amend"]
    if message:
        args.extend(["-m", message])
    else:
        args.append("--no-edit")
    return GitCommand("commit", *args).run()


def get_commit_log(n: int = 10, format: str = None) -> Result:
    """Get commit history"""
    args = ["-n", str(n)]
    if format:
        args.extend(["--format", format])
    return GitCommand("log", *args).run()


# Status and Diff Operations
def status(short: bool = False) -> Result:
    """Get repository status"""
    args = []
    if short:
        args.append("-s")
    return GitCommand("status", *args).run()


def diff(cached: bool = False, files: Optional[List[str]] = None) -> Result:
    """Get diff of changes"""
    args = []
    if cached:
        args.append("--cached")
    if files:
        args.extend(files)
    return GitCommand("diff", *args).run()


# Remote Operations
def fetch(
    remote: Optional[str] = "origin", _all: bool = False, branch_name: str = ""
) -> Result:
    """Fetch from remote"""
    args = [
        remote,
    ]

    if _all:
        args.append("--all")

    if branch_name:
        args.append(branch_name)

    return GitCommand("fetch", *args).run()


def pull(remote: str = "origin", branch: Optional[str] = None) -> Result:
    """Pull from remote"""
    args = [remote]
    if branch:
        args.append(branch)
    return GitCommand("pull", *args).run()


def push(
    remote: str = "origin", branch: Optional[str] = None, force: bool = False
) -> Result:
    """Push to remote"""
    try:
        if not branch:
            current_branch = get_current_branch()
            if isinstance(current_branch, Err):
                return current_branch
            branch = current_branch.unwrap().strip()

        args = [remote, branch]
        if force:
            args.append("--force")

        result = GitCommand("push", *args).run()

        if isinstance(result, Ok):
            return result

        # Handle specific error conditions
        try:
            error = result.unwrap()
        except CalledProcessError as error:
            if hasattr(error, "output"):
                if "[rejected]" in error.output:
                    return Err(GitPushRejectedException(error.output))
                if "whitelist your IP" in error.output:
                    return Err(IPWhitelistException(error.output))
        except Exception as e:
            return Err(e)

    except Exception as e:
        return Err(e)


# Stash Operations
def stash_save(message: Optional[str] = None) -> Result:
    """Stash changes"""
    args = ["push"]
    if message:
        args.extend(["-m", message])
    return GitCommand("stash", *args).run()


def stash_pop(index: int = 0) -> Result:
    """Pop stashed changes"""
    return GitCommand("stash", "pop", f"stash@{{{index}}}").run()


def stash_list() -> Result:
    """List stashed changes"""
    return GitCommand("stash", "list").run()


# Configuration
def get_config(key: str, global_config: bool = False) -> Result:
    """Get git config value"""
    args = ["--get"]
    if global_config:
        args.append("--global")
    args.append(key)
    return GitCommand("config", *args, check_repo=False).run()


def set_config(key: str, value: str, global_config: bool = False) -> Result:
    """Set git config value"""
    args = []
    if global_config:
        args.append("--global")
    args.extend([key, value])
    return GitCommand("config", *args, check_repo=False).run()


# Tag Operations
def create_tag(name: str, message: Optional[str] = None) -> Result:
    """Create a new tag"""
    args = [name]
    if message:
        args.extend(["-m", message])
    return GitCommand("tag", *args).run()


def delete_tag(name: str) -> Result:
    """Delete a tag"""
    return GitCommand("tag", "-d", name).run()


def list_tags() -> Result:
    """List all tags"""
    return GitCommand("tag", "--list").run()


# Utility Functions
def get_repo_root() -> Result:
    """Get the root directory of the git repository"""
    return GitCommand("rev-parse", "--show-toplevel").run()


def clean(force: bool = False, directories: bool = False) -> Result:
    """Clean untracked files"""
    args = []
    if force:
        args.append("-f")
    if directories:
        args.append("-d")
    return GitCommand("clean", *args).run()


def check_ignore(*paths: str) -> Result:
    """Check if paths are ignored by git"""
    return GitCommand("check-ignore", *paths).run()


def get_current_diff_to_main() -> Result:
    """Get diff between current branch and default branch"""
    try:
        default_branch = get_default_branch().unwrap()
        current_branch = get_current_branch().unwrap()
        return GitCommand(
            "--no-pager", "diff", f"{default_branch}...{current_branch}"
        ).run()
    except Exception as e:
        return Err(e)


def get_default_branch() -> Result:
    """Get the default branch name from git remote"""
    try:
        out = (
            GitCommand("symbolic-ref", "refs/remotes/origin/HEAD", "--short")
            .run()
            .unwrap()
        )
        return Ok(out.strip().split("/")[-1])
    except Exception as e:
        return Err(e)


def get_pr_diff(src_branch: str) -> Result:
    """Get the diff for a specific pull request"""
    # TODO - pass in the dest branch
    cmd = GitCommand("diff", f"origin/main...origin/{src_branch}")
    return cmd.run()


def edit_tmp_file(contents: str = "") -> Result:
    """Open a tempfile with git's configured editor and return the value written when saving/closing.
    Returns a tuple of (title, description) split on '------'."""

    try:
        # Get the configured editor using GitCommand
        editor = (
            GitCommand("config", "--get", "core.editor", check_repo=False)
            .run()
            .unwrap()
            .strip()
        )

        with NamedTemporaryFile(delete=True, delete_on_close=False) as fp:
            edit_cmd = f"{editor} {fp.name}"
            if contents:
                fp.write(contents.encode("utf-8"))
            fp.close()
            check_output(shlex.split(edit_cmd), universal_newlines=True, stderr=STDOUT)

            with open(fp.name) as f:
                contents = f.read()

        if not contents:
            return Err(ValueError("Aborting due to empty description"))

        return Ok(contents.split("------", maxsplit=1))

    except Exception as e:
        return Err(e)


# Pretty Printing Functions
def print_status(console: Console = Console()) -> None:
    """Print formatted repository status"""
    status_result = status()
    if isinstance(status_result, Ok):
        console.print(status_result.unwrap())
    else:
        console.print("[red]Error getting repository status[/]")


def print_branch_list(console: Console = Console()) -> None:
    """Print formatted branch list"""
    table = Table(title="Git Branches")
    table.add_column("Branch Name")
    table.add_column("Last Commit")

    try:
        branches = get_all_branches().unwrap().strip().split("\n")
        for branch in branches:
            if branch:
                commit = get_commit_log(n=1, format="%h - %s").unwrap().strip()
                table.add_row(branch, commit)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing branches: {e}[/]")
