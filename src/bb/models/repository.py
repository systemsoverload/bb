"""Repository model and related collection classes"""

from dataclasses import dataclass
from typing import List, Optional

from bb.exceptions import IPWhitelistException
from bb.models import PullRequest, Repository
from bb.models.base import BaseModel
from bb.typeshed import Err, Ok, Result, User


@dataclass
class PullRequestCollection:
    """Collection class for repository pull requests"""

    def __init__(self, repository: "Repository"):
        self.repository = repository

    def list(
        self, _all: bool = False, reviewing: bool = False, mine: bool = False
    ) -> Result[List[PullRequest], Exception]:
        """List pull requests with optional filters"""
        uuid = f'"{self.repository.client().config.get("auth.uuid")}"'
        q = None
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

        result = self.repository.client().get(
            f"{self.repository.api_detail_url}/pullrequests", params=params
        )

        if result.is_err():
            return result

        from bb.models import PullRequest

        return Ok(
            [
                PullRequest.from_api_response(pr_data, self.repository)
                for pr_data in result.unwrap()["values"]
            ]
        )

    def get(self, id: int) -> Result["PullRequest"]:
        """Get a specific pull request by ID"""
        result = self.repository.client().get(
            f"{self.repository.api_detail_url}/pullrequests/{id}"
        )
        if result.is_err():
            return result

        from bb.models import PullRequest

        return Ok(PullRequest.from_api_response(result.unwrap(), self.repository))

    def create(
        self,
        title: str,
        source_branch: str,
        dest_branch: str,
        description: str = "",
        reviewers: List[User] = None,
    ) -> Result["PullRequest"]:
        """Create a new pull request"""
        data = {
            "title": title,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": dest_branch}},
            "description": description,
            "reviewers": [{"uuid": r.uuid} for r in (reviewers or [])],
        }

        result = self.repository.client().post(
            f"{self.repository.api_detail_url}/pullrequests", json=data
        )
        if result.is_err():
            return result

        from bb.models import PullRequest

        return Ok(PullRequest.from_api_response(result.unwrap(), self.repository))


@dataclass
class Repository(BaseModel):
    """Bitbucket repository model"""

    slug: str
    workspace: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: bool = True

    @classmethod
    def resource_path(cls) -> str:
        return "repositories"

    @property
    def api_detail_url(self) -> str:
        """Full API URL for this specific repository"""
        return f"{self.api_url()}/{self.workspace}/{self.slug}"

    @property
    def web_url(self) -> str:
        """Web UI URL for this repository"""
        return f"{self.BASE_WEB_URL}/{self.workspace}/{self.slug}"

    @property
    def pullrequests(self) -> PullRequestCollection:
        """Access repository pull requests"""
        return PullRequestCollection(self)

    @classmethod
    def get_by_full_slug(cls, full_slug: str) -> Result[Repository]:
        """Fetch a repository by its full slug"""
        workspace, slug = full_slug.split("/")
        repo = cls(workspace=workspace, slug=slug)
        result = cls.client().get(repo.api_detail_url)

        if result.is_err():
            return result

        return Ok(cls.from_api_response(result.unwrap()))
