import os
from pathlib import Path

import click
from atlassian.bitbucket import Cloud
from requests.exceptions import HTTPError
from rich import print

from bb.config import BBConfig

# TODO - Make this configurable
CONF_DIR = Path(os.path.expanduser("~/.config/bb/"))
CONF_PATH = Path(os.path.expanduser("~/.config/bb/config.toml"))


@click.group()
def auth():
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

    bitbucket = Cloud(username=username, password=app_password)
    try:
        res = bitbucket.request("GET", "user")

        conf = BBConfig()

        conf.update("auth.username", username)
        conf.update("auth.app_password", app_password)
        conf.update("auth.uuid", res.json().get("uuid"))
        conf.update("auth.account_id", res.json().get("account_id"))
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
    conf.delete("auth.username")
    conf.delete("auth.app_password")
    conf.delete("auth.uuid")
    conf.delete("auth.account_id")
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

    bitbucket = Cloud(
        username=conf.get("auth.username"), password=conf.get("auth.app_password")
    )
    try:
        res = bitbucket.request("GET", "user")
        scopes = [f"'{s}'" for s in res.headers["x-oauth-scopes"].split(",")]
        msg = ["[bold]bitbucket.org[/]"]
        msg.append(
            f"- Logged in to bitbucket.org account [bold]{conf.get('auth.username')}[/]"
        )
        msg.append(f"- Account status: {res.json().get('account_status')}")
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
