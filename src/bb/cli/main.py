import webbrowser

import click

from bb.cli.alias import alias
from bb.cli.auth import auth
from bb.cli.git import git
from bb.cli.pr import pr
from bb.core.config import BBConfig
from bb.utils import repo_context_command
from bb.version import __version__


class AliasedGroup(click.Group):
    """Enable dynamic dispatch to support aliases via `bb alias set`"""

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        conf = BBConfig()
        aliases = conf.get("alias", {})
        if aliases:
            alias = aliases.get(cmd_name)
            if alias:
                alias_cmd, *alias_args = alias.split(" ")
                click_cmd = click.Group.get_command(self, ctx, alias_cmd)
                if click_cmd:
                    click_cmd(alias_args)
                else:
                    ctx.fail(f"No such command or alias {cmd_name}")
        else:
            return None


@click.group(cls=AliasedGroup)
def cli():
    pass


@click.command()
@repo_context_command
def browse(repo_slug):
    """Open current repository in your web browser"""
    webbrowser.open(f"https://bitbucket.org/{repo_slug}", new=2)


@click.command()
def version():
    """Show the version of bb CLI"""
    print(f"bb-cli version {__version__}")


cli.add_command(version)
cli.add_command(alias)
cli.add_command(auth)
cli.add_command(browse)
cli.add_command(pr)
cli.add_command(git)
