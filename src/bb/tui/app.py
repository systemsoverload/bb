"""Main TUI application class"""

from textual.app import App

from .screens import PRDetailScreen, PRDiffScreen, PRListScreen
from .state import PRState


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

    .pr-diffs {
        width: 100%;
        padding: 1;
        border: solid $primary;
    }

    #diffs_container {
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
        # TODO - replace this with an instance of Repository model
        self.state = PRState(repo_slug)

    def on_mount(self) -> None:
        """Mount the initial screen"""
        self.push_screen("pr_list")
