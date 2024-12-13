"""State management for the TUI application"""

from typing import List, Optional

from bb.tui.types import FileDiffType, PullRequestType


class PRState:
    """Global application state"""

    def __init__(self, workspace_slug: str, repo_slug: str):
        from bb.models import Repository

        self.repo = Repository(slug=repo_slug, workspace=workspace_slug)

        self.prs: List[PullRequestType] = []
        self.current_pr: Optional[PullRequestType] = None
        self.file_diffs: List[FileDiffType] = []
        self.current_file_index: int = 0

    def set_current_pr(self, pr: PullRequestType) -> None:
        """Set the currently selected PR"""
        self.current_pr = pr
        self.file_diffs = []  # Reset diffs when changing PR
        self.current_file_index = 0

    def set_file_diffs(self, diffs: List[FileDiffType]) -> None:
        """Set the list of file diffs"""
        self.file_diffs = diffs
        self.current_file_index = 0 if diffs else -1
