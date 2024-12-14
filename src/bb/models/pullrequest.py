"""Pull request model and related functionality"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Self

from bb.models.base import BaseModel
from bb.tui.types import FileDiffType, RepositoryType
from bb.typeshed import Ok, Result


@dataclass
class PullRequest(BaseModel):
    """Represents a pull request with its key attributes"""

    INCLUDED_FIELDS = [
        "values.repository",
        "values.participants",
        "values.description",
        "values.source",
    ]

    EXCLUDED_FIELDS = [
        "values.summary",
        "values.links",
        "values.participants.links",
    ]

    id: int
    title: str
    author: str
    description: str
    status: str
    branch: str
    created: str
    repository: RepositoryType
    reviewers: List[str] = field(default_factory=list)
    approvals: List[str] = field(default_factory=list)
    comment_count: int = 0
    source_commit: Optional[str] = None
    destination_commit: Optional[str] = None
    links: Dict = field(default_factory=dict)

    @classmethod
    def resource_path(cls) -> str:
        return "pullrequests"

    @classmethod
    def from_api_response(cls, data: Dict) -> Self:
        """Create a PullRequest instance from API response data"""
        from bb.models import Repository

        repo_info = data.get("repository", {})
        if not repo_info:
            workspace = (
                data.get("source", {})
                .get("repository", {})
                .get("workspace", {})
                .get("slug")
            )
            slug = data.get("source", {}).get("repository", {}).get("slug")
            if workspace and slug:
                repo_info = {"workspace": {"slug": workspace}, "slug": slug}

        repository = Repository.from_api_response(repo_info) if repo_info else None
        if not repository:
            raise ValueError("Could not determine repository from PR data")

        participants = data.get("participants", [])
        reviewers = [
            p["user"]["display_name"]
            for p in participants
            if p.get("role") == "REVIEWER"  # Include all participants as reviewers
        ]
        approvals = [
            p["user"]["display_name"]
            for p in participants
            if p.get("approved")  # Track who has approved
        ]

        return cls(
            id=data["id"],
            title=data["title"],
            author=data["author"]["display_name"],
            description=data.get("description", ""),
            status="Approved"
            if any(p["approved"] for p in data.get("participants", []))
            else "Open",
            approvals=approvals,
            comment_count=data.get("comment_count", 0),
            branch=data["source"]["branch"]["name"],
            created=cls.format_date(data["created_on"]),
            reviewers=reviewers,
            source_commit=data.get("source", {}).get("commit", {}).get("hash"),
            destination_commit=data.get("destination", {})
            .get("commit", {})
            .get("hash"),
            links=data.get("links", {}),
            repository=repository,
        )

    @property
    def web_url(self) -> str:
        """Get web URL for this pull request"""
        return f"{self.repository.web_url}/pull-requests/{self.id}"

    @property
    def api_detail_url(self) -> str:
        """Get API URL for this specific pull request"""
        return f"{self.repository.api_detail_url}/pullrequests/{self.id}"

    def get_merge_restrictions(self) -> Result[Dict, Exception]:
        """Get merge restrictions for this PR"""
        return self.client().get(
            f"{self.BASE_API_INTERNAL_URL}/repositories/{self.repository.full_slug}/pullrequests/{self.id}/merge-restrictions",
        )

    def approve(self) -> Result:
        """Approve this pull request"""
        url = f"{self.api_detail_url}/approve"
        return self.client().post(url)

    def get_diff(self) -> Result[List[FileDiffType], Exception]:
        """Get the pull request diff from the Bitbucket API"""
        from bb.models import FileDiff

        result = (
            self.client()
            .get(f"{self.api_detail_url}/diff", headers={"Accept": "text/plain"})
            .unwrap()
        )

        # Parse the raw diff content into FileDiff objects
        diff_content = result
        file_diffs: List[FileDiff] = []
        current_file: Optional[FileDiff] = None

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

        return Ok(file_diffs)

    def get_default_description(self) -> Result[Dict, Exception]:
        """Get the generated default description for this PR"""
        return self.client().get(
            f"{self.BASE_API_URL}/internal/repositories/{self.repository.workspace}/{self.repository.slug}"
            f"/pullrequests/default-messages/{self.branch}%0Dmain?raw=true"
        )

    def get_recommended_reviewers(self) -> Result[Dict, Exception]:
        """Get recommended reviewers for this PR"""
        return self.client().get(
            f"{self.BASE_API_URL}/internal/repositories/{self.repository.workspace}/{self.repository.slug}"
            f"/recommended-reviewers"
        )

    def get_codeowners(self, dest_branch: str = "main") -> Result[Dict, Exception]:
        """Get code owners for the changes in this PR"""
        return self.client().get(
            f"{self.BASE_API_URL}/internal/repositories/{self.repository.workspace}/{self.repository.slug}"
            f"/codeowners/{self.branch}..{dest_branch}"
        )

    @staticmethod
    def format_date(date_str: str) -> str:
        """Format date string from API response"""
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, AttributeError):
            return date_str
