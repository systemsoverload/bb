import os
from pathlib import Path

import click
from requests.exceptions import HTTPError
from rich import print

from bb.core.api import get_auth_user
from bb.core.config import BBConfig

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
        res = get_auth_user(username=username, app_password=app_password).unwrap()

        conf = BBConfig()

        conf.update("auth.username", username)
        conf.update("auth.app_password", app_password)
        conf.update("auth.uuid", res.get("uuid"))
        conf.update("auth.account_id", res.get("account_id"))

        print(
            f":beaming_face_with_smiling_eyes: Successfully logged in as [bold]{username}"
        )
        conf.write()
    except HTTPError as e:
        if e.response.status_code == 401:
            print(
                ":x: [bold]401 - [red]Failed to authenticate, double check your app password and username"
            )
        else:
            print(":x: [bold]Something went wrong")


@auth.command()
def logout():
    # Remove saved app password
    conf = BBConfig()
    conf.delete("auth")
    conf.write()
    print("[bold]Successfully removed saved credentials")


@auth.command()
def status():
    # Return current state of app password saved in conf.toml
    conf = BBConfig()
    app_password = conf.get("auth.app_password")
    if not app_password:
        print(":x: [bold]Not logged in")
        return

    try:
        res = get_auth_user(
            username=conf.get("auth.username"),
            app_password=conf.get("auth.app_password"),
        ).unwrap()

        scopes = [f"'{s}'" for s in res["headers"]["x-oauth-scopes"].split(",")]
        msg = ["[bold]bitbucket.org[/]"]
        msg.append(
            f"- Logged in to bitbucket.org account [bold]{conf.get('auth.username')}[/]"
        )
        msg.append(f"- Account status: {res.get('account_status')}")
        app_password = conf.get("auth.app_password")
        msg.append(f"- App password {app_password[0:4]}{'*' * (len(app_password) - 4)}")
        msg.append(f"- Scopes: {scopes}")
        print("\n".join(msg))

    except HTTPError as e:
        if e.response.status_code == 401:
            print(
                ":x: [bold]401 - Failed to authenticate, double check your app password and username"
            )
        else:
            print(":x: [bold]Something went wrong")
