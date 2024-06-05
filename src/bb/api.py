import requests

from bb.config import BBConfig
from bb.typing import Err, Ok, Result
from bb.utils import IPWhitelistException

BASE_URL = "https://api.bitbucket.org"
WEB_BASE_URL = "https://bitbucket.org"


def get_prs(full_slug: str, _all: bool = False, reviewing: bool = False, mine: bool = False) -> Result:
    conf = BBConfig()
    q = None
    uuid = f'"{conf.get("auth.uuid")}"'
    if _all:
        q = 'state="OPEN"'
    elif reviewing:
        q = f'state="OPEN" AND reviewers.uuid={uuid}'
    elif mine:
        q = f'state="OPEN" AND author.uuid={uuid}'

    params = {
        "fields": ",".join(
            [
                "+values.participants",
                "-values.description",
                "-values.summary",
                "-values.links",
                "-values.destination",
                "-values.source",
                "-values.participants.links",
            ]
        ),
        "pagelen": 25,
    }
    if q:
        params["q"] = q

    res = requests.get(
        f"{BASE_URL}/2.0/repositories/{full_slug}/pullrequests",
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
        params=params,
    )

    try:
        res.raise_for_status()
    except requests.HTTPError as exc:
        # TODO - more generic handling of IPWL blocks
        if exc.response.status_code == 403 and "whitelist" in exc.response.content.decode(
            exc.response.encoding or "utf-8"
        ):
            return Err(IPWhitelistException("[bold red] 403 fetching pull requests, ensure your IP has been whitelisted"))
        else:
            return Err(exc)


    return Ok(res.json()["values"])


def create_pr(full_slug: str, title: str, src: str, dest: str, description: str, close_source_branch: str) -> Result:
    conf = BBConfig()

    data = {
        "title": title,
        "source": {"branch": {"name": src}},
        "destination": {"branch": {"name": dest}},
        "close_source_branch": close_source_branch,
    }

    if description:
        data["description"] =  description

    res = requests.post(
        f"{BASE_URL}/2.0/repositories/{full_slug}/pullrequests",
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
        json=data
    )

    try:
        res.raise_for_status()
    except Exception as exc:
        return Err(exc)

    return Ok(res)



def get_auth_user(username: str, app_password: str) -> Result:
    """Get currently authenticated user data"""
    res = requests.get(
        f"{BASE_URL}/2.0/user",
        auth=(username, app_password),
    )

    try:
        res.raise_for_status()
    except Exception as e:
        return Err(e)

    ret = res.json()
    ret['headers'] = res.headers
    return Ok(ret)
