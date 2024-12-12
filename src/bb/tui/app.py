"""Main TUI application class"""

from textual.app import App
from .state import PRState
from .screens import PRListScreen, PRDetailScreen, PRDiffScreen

class PRReviewApp(App[None]):
    """BitBucket Pull Request review application"""

    CSS = """
    #pr_table {
        height: 1fr;
        border: solid $primary;
    }

    .pr-title {
        dock: top;
        height: 3;
        background: $boost;
        color: $text;
        padding: 1;
    }

    .pr-container {
        height: 1fr;
    }

    .pr-meta {
        width: 30%;
        height: 100%;
        padding: 1;
        border: solid $primary;
    }

    .pr-description {
        width: 70%;
        height: 100%;
        padding: 1;
        border: solid $primary;
    }

    .diff-content {
        padding: 1;
        width: 100%;
    }

    #diff_container {
        height: 1fr;
        border: solid $primary;
    }

    DataTable > .datatable--cursor {
        background: $accent;
        color: $text;
    }
    """

    TITLE = "BitBucket PR Review"
    SCREENS = {
        "pr_list": PRListScreen,
        "pr_detail": PRDetailScreen,
        "pr_diff": PRDiffScreen
    }

    def __init__(self, repo_slug: str):
        super().__init__()
        self.state = PRState(repo_slug)

    def on_mount(self) -> None:
        """Mount the initial screen"""
        self.push_screen("pr_list")
