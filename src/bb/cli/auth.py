import os
from pathlib import Path

import click
from requests.exceptions import HTTPError
from rich import print

from bb.core.config import BBConfig
from bb.models import User

# TODO - Make this configurable
CONF_DIR = Path(os.path.expanduser("~/.config/bb/"))
CONF_PATH = Path(os.path.expanduser("~/.config/bb/config.toml"))


@click.group()
def auth():
    """Authentication sub commands --help for more information"""
    pass


@auth.command()
@click.option(
    "--app-password", help="App password associated with bitbucket cloud account"
)
@click.option("--username", help="Username of bitbucket user")
def login(username, app_password):
    if not username:
        username = click.prompt("Username")

    if not app_password:
        app_password = click.prompt("App password", hide_input=True)

    try:
        # Validate credentials first
        result = User.validate_credentials(username, app_password)
        status = result.unwrap()

        # Save validated credentials
        conf = BBConfig()
        conf.update("auth.username", username)
        conf.update("auth.app_password", app_password)
        conf.update("auth.account_status", status.account_status)
        conf.update("auth.uuid", status.uuid)
        conf.write()

        print(
            f":beaming_face_with_smiling_eyes: Successfully logged in as [bold]{status.display_name}"
        )

    except HTTPError as e:
        if e.response.status_code == 401:
            print(
                ":x: [bold]401 - [red]Failed to authenticate, double check your app password and username"
            )
        else:
            print(":x: [bold]Something went wrong")


@auth.command()
def status():
    """Show current authentication status"""
    conf = BBConfig()
    app_password = conf.get("auth.app_password")
    if not app_password:
        print(":x: [bold]Not logged in")
        return

    try:
        result = User.get_status()
        if result.is_err():
            raise result.unwrap_err()

        status = result.unwrap()
        print("\n".join(status.format_message()))

    except HTTPError as e:
        if e.response.status_code == 401:
            print(
                ":x: [bold]401 - Failed to authenticate, double check your app password and username"
            )
        else:
            print(e)
            print(":x: [bold]Something went wrong")


@auth.command()
def logout():
    # Remove saved app password
    conf = BBConfig()
    conf.delete("auth")
    conf.write()
    print("[bold]Successfully removed saved credentials")
