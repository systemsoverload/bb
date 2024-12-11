from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

from .models import PullRequest, FileDiff


class ViewState(Enum):
    """Enumeration of possible view states in the TUI"""
    LIST = auto()
    DETAIL = auto()
    DIFF = auto()
    SEARCH = auto()


@dataclass
class AppState:
    """Global application state container"""
    repo_slug: str
    view_state: ViewState = ViewState.LIST
    current_pr_index: int = 0
    scroll_position: int = 0
    status_message: str = ""
    search_term: str = ""
    last_key: Optional[str] = None
    viewport_height: int = 0

    # PR-related state
    prs: List[PullRequest] = None
    selected_pr: Optional[PullRequest] = None

    # Diff-related state
    diff_content: str = ""
    diff_lines: List[str] = None
    file_diffs: List[FileDiff] = None
    current_file_index: int = -1

    def __post_init__(self):
        """Initialize collections after instance creation"""
        if self.prs is None:
            self.prs = []
        if self.diff_lines is None:
            self.diff_lines = []
        if self.file_diffs is None:
            self.file_diffs = []

    @property
    def current_pr(self) -> Optional[PullRequest]:
        """Get the currently selected PR"""
        if not self.prs or self.current_pr_index >= len(self.prs):
            return None
        return self.prs[self.current_pr_index]

    @property
    def current_file_diff(self) -> Optional[FileDiff]:
        """Get the currently selected file diff"""
        if not self.file_diffs or self.current_file_index >= len(self.file_diffs):
            return None
        return self.file_diffs[self.current_file_index]

    def reset_scroll(self):
        """Reset scroll position"""
        self.scroll_position = 0

    def reset_search(self):
        """Reset search state"""
        self.search_term = ""

    def update_viewport_height(self, console_height: int):
        """Update viewport height based on console dimensions"""
        self.viewport_height = console_height - 8  # Account for headers/footers
