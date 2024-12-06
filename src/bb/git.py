import os
import shlex
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Optional

from rich.console import Console

from bb.exceptions import GitPushRejectedException, IPWhitelistException
from bb.typeshed import Err, Ok, Result

# Define client identifier
BB_CLIENT_ID = "bb-cli/1.0"

def _prepare_git_env():
    """Prepare environment variables for git commands with client identification"""
    env = os.environ.copy()
    # Set environment variable for SSH commands
    env['GIT_SSH_COMMAND'] = f'ssh -o SendEnv=BB_CLIENT_ID'
    env['BB_CLIENT_ID'] = BB_CLIENT_ID
    # Set git config for HTTP user agent
    try:
        check_output(
            shlex.split(f'git config --global http.useragent "{BB_CLIENT_ID}"'),
            universal_newlines=True,
            env=env
        )
    except CalledProcessError:
        pass  # Best effort to set user agent
    return env

def _run_git_command(cmd: str, universal_newlines: bool = True) -> Result:
    """Run a git command with prepared environment"""
    try:
        env = _prepare_git_env()
        return Ok(check_output(
            shlex.split(cmd),
            universal_newlines=universal_newlines,
            stderr=STDOUT,
            env=env
        ))
    except CalledProcessError as e:
        return Err(e)

def get_current_repo_slug() -> Result:
    try:
        out = _run_git_command("git remote -v").unwrap()
        first_line = out.splitlines()[0].replace("\t", " ").split(" ")[1].strip()
        if "bitbucket" in first_line:
            return Ok(first_line.split(":")[-1][0:-4])
        else:
            return Err(RuntimeError("No repository detected"))
    except CalledProcessError as e:
        return Err(e)

def get_current_branch() -> Result:
    return _run_git_command("git rev-parse --abbrev-ref HEAD")

def get_current_diff_to_main() -> Result:
    try:
        default_branch = get_default_branch().unwrap()
        current_branch = get_current_branch().unwrap()
        cmd = f"git --no-pager diff {default_branch}...{current_branch}"
        return _run_git_command(cmd, universal_newlines=False)
    except CalledProcessError as e:
        return Err(e)

def push_branch(branch_name: Optional[str] = None) -> Result:
    if not branch_name:
        branch_name = get_current_branch().unwrap().strip()
    try:
        with Console().status(f"[bold]Pushing {branch_name} to origin..."):
            out = _run_git_command(f"git push origin {branch_name}").unwrap()
        return Ok(out.strip())
    except CalledProcessError as e:
        if "[rejected]" in e.output:
            return Err(GitPushRejectedException(e.output))
        if "whitelist your IP" in e.output:
            return Err(IPWhitelistException(e.output))
        return Err(e)

def get_branch(branch_name) -> Result:
    return _run_git_command(f"git rev-parse --abbrev-ref {branch_name}")

def get_default_branch() -> Result:
    return _run_git_command("git symbolic-ref refs/remotes/origin/HEAD --short")

def edit_tmp_file(contents: str = None) -> Result:
    """Open a tempfile with git's configured editor and return the value written when saving/closing"""
    from tempfile import NamedTemporaryFile

    editor = _run_git_command("git config --get core.editor").unwrap().strip().split("/")[-1]

    with NamedTemporaryFile(delete=True, delete_on_close=False) as fp:
        edit_cmd = f"{editor} {fp.name}"
        if contents:
            fp.write(contents.encode("utf-8"))
        fp.close()
        try:
            _run_git_command(edit_cmd).unwrap()
            with open(fp.name) as f:
                contents = f.read()
        except Exception as e:
            return Err(e)

    if not len(contents):
        return Err(ValueError("Aborting due to empty description"))

    return Ok(contents.split("------", maxsplit=1))
