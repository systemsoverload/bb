import shlex
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Optional

from rich.console import Console

from bb.typing import Err, Ok, Result
from bb.utils import IPWhitelistException


def get_current_repo_slug() -> Result:
    try:
        out = (
            check_output(shlex.split("git remote -v"), universal_newlines=True)
            .splitlines()[0]
            .replace("\t", " ")
            .split(" ")[1]
            .strip()
        )
        if "bitbucket" in out:
            return Ok(out.split(":")[-1].strip(".git"))
        else:
            return Err(RuntimeError("No repository detected"))
    except CalledProcessError as e:
        return Err(e)


def get_current_branch() -> Result:
    try:
        out = check_output(shlex.split("git rev-parse --abbrev-ref HEAD"), universal_newlines=True)
        return Ok(out.strip())
    except CalledProcessError as e:
        return Err(e)


def push_branch(branch_name: Optional[str] = None) -> Result:
    if not branch_name:
        branch_name = get_current_branch().unwrap().strip()
    try:
        with Console().status(f"[bold]Pushing {branch_name} to origin..."):
            out = check_output(shlex.split(f"git push origin {branch_name}"), universal_newlines=True, stderr=STDOUT)
        return Ok(out.strip())
    except CalledProcessError as e:
        # TODO - This probably needs to be used everywhere that attempts to interact with bb remotes
        if "whitelist your IP" in e.output:
            return Err(IPWhitelistException(e.output))
        return Err(e)


def get_branch(branch_name) -> Result:
    try:
        out = check_output(
            shlex.split(f"git rev-parse --abbrev-ref {branch_name}"), universal_newlines=True, stderr=STDOUT
        )
        return Ok(out.strip())
    except CalledProcessError as e:
        return Err(e)


def get_default_branch() -> Result:
    try:
        out = check_output(
            shlex.split("git symbolic-ref refs/remotes/origin/HEAD --short"), universal_newlines=True, stderr=STDOUT
        )
        return Ok(out.strip().split('/')[-1])
    except CalledProcessError as e:
        return Err(e)
