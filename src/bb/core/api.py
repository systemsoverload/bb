import requests

from bb.core.config import BBConfig
from bb.exceptions import IPWhitelistException
from bb.typeshed import Err, Ok, Result, User

BASE_URL = "https://api.bitbucket.org"
WEB_BASE_URL = "https://bitbucket.org"


def get_prs(
    full_slug: str, _all: bool = False, reviewing: bool = False, mine: bool = False
) -> Result:
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
                # TODO - maybe make these configurable for thin responses on the list view?
                # "-values.description",
                # "-values.source",
                "-values.summary",
                "-values.links",
                "-values.destination",
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
        if (
            exc.response.status_code == 403
            and "whitelist"
            in exc.response.content.decode(exc.response.encoding or "utf-8")
        ):
            return Err(
                IPWhitelistException(
                    "[bold red] 403 fetching pull requests, ensure your IP has been whitelisted"
                )
            )
        else:
            return Err(exc)

    return Ok(res.json()["values"])


def create_pr(
    full_slug: str,
    title: str,
    src: str,
    dest: str,
    description: str,
    close_source_branch: str,
    reviewers: list[User],
) -> Result:
    conf = BBConfig()

    data = {
        "title": title,
        "source": {"branch": {"name": src}},
        "destination": {"branch": {"name": dest}},
        "close_source_branch": close_source_branch,
        "reviewers": [{"uuid": r.uuid} for r in reviewers],
    }

    if description:
        data["description"] = description

    res = requests.post(
        f"{BASE_URL}/2.0/repositories/{full_slug}/pullrequests",
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
        json=data,
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
    ret["headers"] = res.headers
    return Ok(ret)


def get_default_description(full_slug: str, src: str, dest: str) -> Result:
    conf = BBConfig()
    src = src.strip()
    dest = dest.strip()

    url = f"{BASE_URL}/internal/repositories/{full_slug}/pullrequests/default-messages/{src}%0D{dest}?raw=true"
    res = requests.get(
        url,
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
    )

    try:
        res.raise_for_status()
    except Exception as exc:
        return Err(exc)

    return Ok(res)


def get_recommended_reviewers(full_slug: str) -> Result:
    conf = BBConfig()
    url = f"{BASE_URL}/internal/repositories/{full_slug}/recommended-reviewers"
    res = requests.get(
        url,
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
    )

    try:
        res.raise_for_status()
    except Exception as exc:
        return Err(exc)

    return Ok(res)


def get_codeowners(full_slug: str, src: str, dest: str) -> Result:
    conf = BBConfig()
    url = f"{BASE_URL}/internal/repositories/{full_slug}/codeowners/{src}..{dest}"
    res = requests.get(
        url,
        auth=(conf.get("auth.username"), conf.get("auth.app_password")),
    )

    try:
        res.raise_for_status()
    except Exception as exc:
        return Err(exc)

    return Ok(res)
