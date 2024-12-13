"""Pull request model and related functionality"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from bb.models.base import BaseModel
from bb.models.repository import Repository
from bb.typeshed import Ok, Result


@dataclass
class PullRequest(BaseModel):
    """Represents a pull request with its key attributes"""

    id: int
    title: str
    author: str
    description: str
    status: str
    branch: str
    created: str
    repository: Repository
    reviewers: List[str] = field(default_factory=list)
    approvals: List[str] = field(default_factory=list)
    comments: int = 0
    source_commit: Optional[str] = None
    destination_commit: Optional[str] = None
    links: Dict = field(default_factory=dict)

    @classmethod
    def resource_path(cls) -> str:
        return "pullrequests"

    @classmethod
    def from_api_response(cls, pr_data: Dict, repository: Repository) -> "PullRequest":
        """Create a PullRequest instance from API response data"""
        return cls(
            id=pr_data["id"],
            title=pr_data["title"],
            author=pr_data["author"]["display_name"],
            description=pr_data.get("description", ""),
            status="Approved"
            if any(p["approved"] for p in pr_data.get("participants", []))
            else "Open",
            approvals=[
                p["user"]["display_name"]
                for p in pr_data.get("participants", [])
                if p["approved"]
            ],
            comments=len(pr_data.get("comments", [])),
            branch=pr_data["source"]["branch"]["name"],
            created=cls.format_date(pr_data["created_on"]),
            reviewers=[r["user"]["display_name"] for r in pr_data.get("reviewers", [])],
            source_commit=pr_data.get("source", {}).get("commit", {}).get("hash"),
            destination_commit=pr_data.get("destination", {})
            .get("commit", {})
            .get("hash"),
            links=pr_data.get("links", {}),
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

    def get_diff(self) -> Result[List["FileDiff"]]:
        """Get the pull request diff from the Bitbucket API"""
        from bb.models import FileDiff

        result = self.client().get(
            f"{self.api_detail_url}/diff", headers={"Accept": "text/plain"}
        )

        if result.is_err():
            return result

        # Parse the raw diff content into FileDiff objects
        diff_content = result.unwrap()
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

    def get_default_description(self) -> Result[Dict]:
        """Get the generated default description for this PR"""
        return self.client().get(
            f"{self.BASE_API_URL}/internal/repositories/{self.repository.workspace}/{self.repository.slug}"
            f"/pullrequests/default-messages/{self.branch}%0Dmain?raw=true"
        )

    def get_recommended_reviewers(self) -> Result[Dict]:
        """Get recommended reviewers for this PR"""
        return self.client().get(
            f"{self.BASE_API_URL}/internal/repositories/{self.repository.workspace}/{self.repository.slug}"
            f"/recommended-reviewers"
        )

    def get_codeowners(self, dest_branch: str = "main") -> Result[Dict]:
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
