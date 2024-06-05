import click
from rich import print

from bb.config import BBConfig


@click.group()
def alias():
    pass


@alias.command()
@click.argument("alias_name")
@click.argument("cmd")
def set(alias_name, cmd):
    conf = BBConfig()
    conf.update(f"alias.{alias_name}", cmd)
    conf.write()

    print(f"[bold]Successfully added alias {alias_name} for {cmd}")


@alias.command()
@click.argument("alias_name")
def remove(alias_name):
    conf = BBConfig()
    conf.delete(f"alias.{alias_name}")
    conf.write()
    print(f"[bold]Successfully removed alias {alias_name}")
