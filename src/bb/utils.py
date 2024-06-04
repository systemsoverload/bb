import shlex
from functools import reduce, update_wrapper
from subprocess import CalledProcessError, check_output

import click
from rich import print

from bb.typing import Err, Ok, Result


def rget(dct, keys, default=None, getter=None):
    """Safe nested dictionary key lookup helper

    >>> dct = {'foo': {'bar': 123}}
    >>> rget(dct, 'foo.bar') == 123
    >>> rget(dct, ['foo', 'bar') == 123
    >>> rget(dct, 'foo.baz', 42) == 42

    :param dct: Dictionary to perform nested .get()'s on
    :param keys: Any iterable or dot separated string of keys to accumlate from
    :default: Default return value when .get()'s fail
    """
    if isinstance(keys, bytes):
        keys = keys.split(b".")
    elif isinstance(keys, str):
        keys = keys.split(".")

    if getter is None:
        getter = lambda a, i: (a.get(i, default) if hasattr(a, "get") else default)  # noqa: NVR1 (AUTO)

    return reduce(getter, keys, dct)


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


def repo_context_command(fn):
    "Ensure command execution is in context of bb repo"

    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        try:
            repo_slug = get_current_repo_slug().unwrap()
        except CalledProcessError as e:
            print("[bold][red]Command called outside of the context of a git repository")
            return
        except RuntimeError as e:
            print("[red][bold]Error:[/] Repository has no bitbucket remotes")
            return
        return ctx.invoke(fn, repo_slug, *args, **kwargs)

    return update_wrapper(wrapper, fn)
