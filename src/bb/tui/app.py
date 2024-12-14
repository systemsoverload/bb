"""Main TUI application class"""

from textual.app import App

from bb.tui.screens import PRDetailScreen, PRDiffScreen, PRListScreen
from bb.tui.state import PRState


class PRReviewApp(App[None]):
    """Bitbucket Pull Request review application"""

    CSS = """
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
        import logging

        from textual.logging import TextualHandler

        logging.basicConfig(level=logging.DEBUG, handlers=[TextualHandler()])
        ws, s = repo_slug.split("/")
        self.state = PRState(workspace_slug=ws, repo_slug=s)

    def on_mount(self) -> None:
        """Mount the initial screen"""
        self.push_screen("pr_list")
