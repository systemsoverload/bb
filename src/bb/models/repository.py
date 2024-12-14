"""Repository model and related collection classes"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Self, Set

from bb.models.base import BaseModel
from bb.tui.types import PullRequestType, UserType
from bb.typeshed import Ok, Result


@dataclass
class DefaultDescription:
    """Default title and description template for a pull request"""

    title: str
    description: str
    headers: dict

    def format_for_editor(self) -> str:
        """Format the description for editing in a temporary file"""
        return f"{self.title}\n------\n{self.description}"


@dataclass
class PullRequestCollection:
    """Collection class for repository pull requests"""

    def __init__(self, repository: "Repository"):
        self.repository = repository

    def list(
        self, _all: bool = False, reviewing: bool = False, mine: bool = False
    ) -> Result[List[PullRequestType], Exception]:
        """List pull requests with optional filters"""
        # Build query params based on filter type
        from bb.models import PullRequest

        query_params = {}
        if _all:
            query_params["state"] = "OPEN"
        elif reviewing:
            query_params.update(
                {"state": "OPEN", "reviewers_uuid": self.repository.client().user_uuid}
            )
        elif mine:
            query_params.update(
                {"state": "OPEN", "author_uuid": self.repository.client().user_uuid}
            )

        result = self.repository.client().get(
            f"{self.repository.api_detail_url}/pullrequests",
            model_cls=PullRequest,
            query_params=query_params,
            params={"pagelen": 25},
        )

        if result.is_err():
            return result

        # Add repository info to each PR data
        pr_data_list = result.unwrap()["values"]
        for pr_data in pr_data_list:
            pr_data["repository"] = {
                "workspace": {"slug": self.repository.workspace},
                "slug": self.repository.slug,
            }

        return Ok([PullRequest.from_api_response(pr_data) for pr_data in pr_data_list])

    def get(self, id: int) -> Result[PullRequestType, Exception]:
        """Get a specific pull request by ID"""
        from textual import log

        log.error(self.repository.api_detail_url)
        result = self.repository.client().get(
            f"{self.repository.api_detail_url}/pullrequests/{id}"
        )
        if result.is_err():
            return result

        from bb.models import PullRequest

        return Ok(PullRequest.from_api_response(result.unwrap()))

    def create(
        self,
        title: str,
        source_branch: str,
        dest_branch: str,
        description: str = "",
        reviewers: List[UserType] = [],
    ) -> Result[PullRequestType, Exception]:
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

        result = result.unwrap()
        from bb.models import PullRequest

        # Manually patch the repo data from the local instance to avoid fetching API data
        # we already have
        result.unwrap()["repository"] = {
            "workspace": {"slug": self.repository.workspace},
            "slug": self.repository.slug,
        }

        return Ok(PullRequest.from_api_response(result))


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
    def full_slug(self) -> str:
        return f"{self.workspace}/{self.slug}"

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
    def get_by_full_slug(cls, full_slug: str) -> Result[Self, Exception]:
        """Fetch a repository by its full slug"""
        workspace, slug = full_slug.split("/")
        repo = cls(workspace=workspace, slug=slug)
        result = cls.client().get(repo.api_detail_url)

        if result.is_err():
            return result

        return Ok(cls.from_api_response(result.unwrap()))

    def get_default_description(
        self, src_branch: str, dest_branch: str
    ) -> Result[DefaultDescription, Exception]:
        """Get the default PR description template for this repository

        Args:
            src_branch: Source branch name
            dest_branch: Destination branch name

        Returns:
            DefaultDescription containing template title and description
        """
        # TODO - push this into the default description class? Delete the class?
        url = (
            f"{self.BASE_API_INTERNAL_URL}/repositories"
            f"/{self.workspace}/{self.slug}"
            f"/pullrequests/default-messages/{src_branch}%0D{dest_branch}?raw=true"
        )

        result = self.client().get(url)
        if result.is_err():
            return result

        return Ok(DefaultDescription(**result.unwrap()))

    def get_effective_reviewers(
        self, src_branch: str, dest_branch: str
    ) -> Result[Set[UserType], Exception]:
        """Given a src and destination branch, query both the effective reviewers and codeowners
        returning a unified set of 'effective reviewers'"""
        users: Set[UserType] = set()

        # Default reviewers
        dr_url = f"{self.BASE_API_URL}/repositories/{self.workspace}/{self.slug}/effective-default-reviewers"
        dr_result = self.client().get(dr_url)

        if dr_result.is_err():
            return dr_result

        from bb.models import User

        [
            users.add(User.from_api_response(u.get("user")))
            for u in dr_result.unwrap().get("values")
        ]

        # CODEOWNERS
        co_url = f"{self.BASE_API_INTERNAL_URL}/repositories/bitbucket/core/codeowners/{src_branch}..{dest_branch}"

        co_result = self.client().get(co_url)

        if co_result.is_err():
            return co_result

        [users.add(User.from_api_response(u)) for u in co_result.unwrap()]

        return Ok(users)

    def get_recommended_reviewers(
        self, src_branch, dest_branch
    ) -> Result[Set[UserType], Exception]:
        users: Set[UserType] = set()

        rr_url = f"{self.BASE_API_INTERNAL_URL}/repositories/{self.workspace}/{self.slug}/recommended-reviewers"
        rr_result = self.client().get(rr_url)

        if rr_result.is_err():
            return rr_result

        from bb.models import User

        [users.add(User.from_api_response(u)) for u in rr_result.unwrap()]

        return Ok(users)

    @classmethod
    def from_api_response(cls, data: Dict) -> "Repository":
        """Create Repository instance from API response data"""
        # Handle both full API responses and nested repository data
        workspace_slug = None
        repo_slug = None
        # data = {"workspace": {"slug": workspace}, "slug": slug}
        # Try to get workspace from various possible locations in the response
        workspace_data = data.get("workspace", {})
        if isinstance(workspace_data, dict):
            workspace_slug = workspace_data.get("slug")
        elif isinstance(workspace_data, str):
            workspace_slug = workspace_data

        # Try to get repo slug from various possible locations
        repo_slug = data.get("slug")
        if not repo_slug and "/" in (data.get("full_name", "") or ""):
            # Handle cases where we get full_name instead
            workspace_slug, repo_slug = data["full_name"].split("/")

        if not workspace_slug or not repo_slug:
            raise ValueError(
                f"Could not determine repository details from data: {data}"
            )

        return cls(
            workspace=workspace_slug,
            slug=repo_slug,
            name=data.get("name"),
            description=data.get("description"),
            is_private=data.get("is_private", True),
        )
