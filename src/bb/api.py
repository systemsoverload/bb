import requests

from bb.config import BBConfig

BASE_URL = "https://api.bitbucket.org/"
WEB_BASE_URL = "https://bitbucket.org/"


def get_prs(full_slug: str, _all: bool = False, reviewing: bool = False, mine: bool = False) -> dict:
    conf = BBConfig()
    q = None
    uuid = f'"{conf.get("auth.uuid")}"'
    if _all:
        q = f'state="OPEN"'
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

    return res.json()["values"]
