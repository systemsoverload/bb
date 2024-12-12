"""State management for the TUI application"""

from typing import List, Optional
from bb.models import PullRequest, FileDiff

class PRState:
    """Global application state"""
    def __init__(self, repo_slug: str):
        self.repo_slug = repo_slug
        self.prs: List[PullRequest] = []
        self.current_pr: Optional[PullRequest] = None
        self.file_diffs: List[FileDiff] = []
        self.current_file_index: int = 0

    def set_current_pr(self, pr: PullRequest) -> None:
        """Set the currently selected PR"""
        self.current_pr = pr
        self.file_diffs = []  # Reset diffs when changing PR
        self.current_file_index = 0

    def set_file_diffs(self, diffs: List[FileDiff]) -> None:
        """Set the list of file diffs"""
        self.file_diffs = diffs
        self.current_file_index = 0 if diffs else -1
