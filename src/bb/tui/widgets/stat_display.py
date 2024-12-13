from typing import Optional

from rich.style import Style
from rich.text import Text
from textual.widgets import Static


class StatDisplay(Static):
    DEFAULT_CSS = """
    StatDisplay {
        height: auto;
        padding: 0 1;
    }

    StatDisplay > .stat {
        margin-right: 2;
    }

    StatDisplay > .stat--positive {
        color: $success;
    }

    StatDisplay > .stat--negative {
        color: $error;
    }
    """

    def __init__(
        self, additions: int = 0, deletions: int = 0, comments: int = 0, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.additions = additions
        self.deletions = deletions
        self.comments = comments

    def compose(self):
        """Create the stat display layout"""
        stats_text = Text()

        # Additions
        if self.additions:
            stats_text.append(
                f"+{self.additions} ", style=Style(color="green", bold=True)
            )

        # Deletions
        if self.deletions:
            stats_text.append(
                f"-{self.deletions} ", style=Style(color="red", bold=True)
            )

        # Comments
        if self.comments:
            stats_text.append(
                f"💬 {self.comments}", style=Style(color="yellow", bold=True)
            )

        yield Static(stats_text)

    def update_stats(
        self,
        additions: Optional[int] = None,
        deletions: Optional[int] = None,
        comments: Optional[int] = None,
    ) -> None:
        """Update the displayed statistics"""
        if additions is not None:
            self.additions = additions
        if deletions is not None:
            self.deletions = deletions
        if comments is not None:
            self.comments = comments
        self.refresh()
