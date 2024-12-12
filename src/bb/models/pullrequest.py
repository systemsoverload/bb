"""Models for BitBucket data structures and UI state"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from bb.core.config import BBConfig
from bb.exceptions import IPWhitelistException
from bb.tui.types import FileDiffType
from bb.typeshed import Err, Ok, Result

BASE_URL: str = "https://api.bitbucket.org"
WEB_BASE_URL: str = "https://bitbucket.org"

@dataclass
class PullRequest:
    """Represents a pull request with its key attributes"""
    id: int
    title: str
    author: str
    description: str
    status: str
    approvals: List[str]
    comments: int
    branch: str
    created: str
    reviewers: List[str]
    repo_slug: str
    source_commit: Optional[str] = None
    destination_commit: Optional[str] = None
    links: Dict = field(default_factory=dict)


    def get_pr_diff(self) -> Result[List[FileDiffType], Exception]:
        """
        Get the pull request diff from the BitBucket API.
        Returns a Result containing a list of FileDiffType objects.
        """

        # TODO - Have the option to perform the diff locally? Might not be worth the effort
        # to duplicate the bb core diffing algorithms

        from bb.models import FileDiff

        if not self.repo_slug:
            return Err(ValueError("Repository slug not set"))

        conf = BBConfig()

        # First, get the raw diff from the API
        url = f"{BASE_URL}/2.0/repositories/{self.repo_slug}/pullrequests/{self.id}/diff"

        try:
            res = requests.get(
                url,
                auth=(conf.get("auth.username"), conf.get("auth.app_password")),
                headers={"Accept": "text/plain"}
            )

            res.raise_for_status()

            # Parse the raw diff content into FileDiffType objects
            diff_content = res.text
            file_diffs: List[FileDiffType] = []
            current_file: Optional[FileDiffType] = None

            for line in diff_content.splitlines():
                # Start of a new file diff
                if line.startswith("diff --git"):
                    if current_file:
                        file_diffs.append(current_file)
                    # Extract filename from the diff header
                    file_path = line.split(" b/")[-1]
                    current_file = FileDiff(filename=file_path)

                # Add the line to the current file diff
                if current_file:
                    current_file.add_line(line)

            # Add the last file diff if it exists
            if current_file:
                file_diffs.append(current_file)

            # Get additional information about the changes
            url = f"{BASE_URL}/2.0/repositories/{self.repo_slug}/pullrequests/{self.id}/diffstat"
            res = requests.get(
                url,
                auth=(conf.get("auth.username"), conf.get("auth.app_password"))
            )
            res.raise_for_status()

            # Update FileDiffType objects with additional stats from diffstat
            diffstat = res.json()
            for stat in diffstat.get('values', []):
                filename = stat.get('new', {}).get('path') or stat.get('old', {}).get('path')
                if filename:
                    for diff in file_diffs:
                        if diff.filename == filename:
                            diff.status = stat.get('status')
                            diff.content_type = stat.get('new', {}).get('type') or stat.get('old', {}).get('type')
                            break

            return Ok(file_diffs)

        except requests.HTTPError as exc:
            if exc.response.status_code == 403 and "whitelist" in exc.response.text:
                return Err(IPWhitelistException(
                    "[bold red] 403 fetching pull request diff, ensure your IP has been whitelisted"
                ))
            return Err(exc)
        except Exception as exc:
            return Err(exc)

    @classmethod
    def from_api_response(cls, pr_data: Dict, repo_slug: str) -> 'PullRequest':
        """Create a PullRequest instance from API response data"""
        return cls(
            id=pr_data['id'],
            title=pr_data['title'],
            author=pr_data['author']['display_name'],
            description=pr_data.get('description', ''),
            status='Approved' if any(p['approved'] for p in pr_data.get('participants', [])) else 'Open',
            approvals=[p['user']['display_name'] for p in pr_data.get('participants', []) if p['approved']],
            comments=len(pr_data.get('comments', [])),
            branch=pr_data['source']['branch']['name'],
            created=format_date(pr_data['created_on']),
            reviewers=[r['user']['display_name'] for r in pr_data.get('reviewers', [])],
            source_commit=pr_data.get('source', {}).get('commit', {}).get('hash'),
            destination_commit=pr_data.get('destination', {}).get('commit', {}).get('hash'),
            links=pr_data.get('links', {}),
            repo_slug=repo_slug
        )

    @classmethod
    def list(cls, repo_slug: str, _all: bool = False, reviewing: bool = False, mine: bool = False) -> Result:
        """List pull requests for a repository"""
        # TODO - Unused at the moment but belongs on a repository model.
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
                    "+values.description",
                    "-values.summary",
                    "-values.links",
                    "+values.source",
                    "-values.participants.links",
                ]
            ),
            "pagelen": 25,
        }
        if q:
            params["q"] = q

        res = requests.get(
            f"{BASE_URL}/2.0/repositories/{repo_slug}/pullrequests",
            auth=(conf.get("auth.username"), conf.get("auth.app_password")),
            params=params,
        )

        try:
            res.raise_for_status()
            prs_data = res.json()["values"]
            return Ok([cls.from_api_response(pr) for pr in prs_data])
        except requests.HTTPError as exc:
            if exc.response.status_code == 403 and "whitelist" in exc.response.content.decode(
                exc.response.encoding or "utf-8"
            ):
                return Err(
                    IPWhitelistException("[bold red] 403 fetching pull requests, ensure your IP has been whitelisted")
                )
            return Err(exc)
        except Exception as e:
            return Err(e)

    def get_default_description(self) -> Result:
        """Get the generated default description for this PR"""
        if not self.repo_slug:
            return Err(ValueError("Repository slug not set"))

        conf = BBConfig()
        url = f"{BASE_URL}/internal/repositories/{self.repo_slug}/pullrequests/default-messages/{self.branch}%0Dmain?raw=true"

        try:
            res = requests.get(
                url,
                auth=(conf.get("auth.username"), conf.get("auth.app_password")),
            )
            res.raise_for_status()
            return Ok(res.json())
        except Exception as exc:
            return Err(exc)

    def get_recommended_reviewers(self) -> Result:
        """Get recommended reviewers for this PR"""
        if not self.repo_slug:
            return Err(ValueError("Repository slug not set"))

        conf = BBConfig()
        url = f"{BASE_URL}/internal/repositories/{self.repo_slug}/recommended-reviewers"

        try:
            res = requests.get(
                url,
                auth=(conf.get("auth.username"), conf.get("auth.app_password")),
            )
            res.raise_for_status()
            return Ok(res.json())
        except Exception as exc:
            return Err(exc)

    def get_codeowners(self, dest_branch: str = "main") -> Result:
        """Get code owners for the changes in this PR"""
        if not self.repo_slug:
            return Err(ValueError("Repository slug not set"))

        conf = BBConfig()
        url = f"{BASE_URL}/internal/repositories/{self.repo_slug}/codeowners/{self.branch}..{dest_branch}"

        try:
            res = requests.get(
                url,
                auth=(conf.get("auth.username"), conf.get("auth.app_password")),
            )
            res.raise_for_status()
            return Ok(res.json())
        except Exception as exc:
            return Err(exc)

    @property
    def web_url(self) -> Optional[str]:
        """Get web URL for the pull request"""
        if not self.repo_slug:
            return None
        return f"{WEB_BASE_URL}/{self.repo_slug}/pull-requests/{self.id}"

    @property
    def api_url(self) -> Optional[str]:
        """Get API URL for the pull request"""
        if not self.repo_slug:
            return None
        return f"{BASE_URL}/2.0/repositories/{self.repo_slug}/pullrequests/{self.id}"

def format_date(date_str: str) -> str:
    """Format date string from API response"""
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d %H:%M:%S UTC')
    except (ValueError, AttributeError):
        return date_str
