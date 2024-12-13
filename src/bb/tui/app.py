"""Main TUI application class"""

from textual.app import App
from textual.binding import Binding

from bb.tui.screens import PRDetailScreen, PRDiffScreen, PRListScreen
from bb.tui.state import PRState


class PRReviewApp(App[None]):
    """Bitbucket Pull Request review application"""

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

    TITLE = "Bitbucket Cloud"
    SCREENS = {
        "pr_list": PRListScreen,
        "pr_detail": PRDetailScreen,
        "pr_diff": PRDiffScreen,
    }

    def __init__(self, repo_slug: str):
        super().__init__()
        # XXX - Setup textual logger for local dev - this might be better behind a flag
        from textual.logging import TextualHandler
        import logging

        logging.basicConfig(level=logging.DEBUG, handlers=[TextualHandler()])

        # TODO - replace this with an instance of Repository model
        self.state = PRState(repo_slug)

    def on_mount(self) -> None:
        """Mount the initial screen"""
        self.push_screen("pr_list")
