"""File diff widget with collapsible content"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Collapsible, Static


class DiffContent(Static):
    """Content container for diff lines"""

    def __init__(self, lines: list[str]):
        super().__init__()
        self.lines = lines

    def compose(self) -> ComposeResult:
        for line in self.lines:
            # Determine line type and apply appropriate class and style
            if line.startswith("+") and not line.startswith("+++"):
                classes = "diff-line diff-line--addition"
                style = "green"
            elif line.startswith("-") and not line.startswith("---"):
                classes = "diff-line diff-line--deletion"
                style = "red"
            elif line.startswith("@@"):
                classes = "diff-line diff-line--info"
                style = "blue"
            else:
                classes = "diff-line"
                style = None

            # Create styled line
            content = line if not style else f"[{style}]{line}[/]"
            yield Static(content, classes=classes)


class DiffHeader(Static):
    """Header showing filename and stats"""

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static(f"[bold]{self.filename}[/]", classes="filename"),
            classes="header-content",
        )

    def __init__(self, filename: str, additions: int, deletions: int):
        super().__init__()
        self.filename = filename
        self.additions = additions
        self.deletions = deletions


class FileDiff(Static):
    """A component that shows file diff with collapsible content"""

    def __init__(self, filename: str, lines: list[str], additions: int, deletions: int):
        super().__init__()
        self.filename = filename
        self.lines = lines
        self.additions = additions
        self.deletions = deletions

    def compose(self) -> ComposeResult:
        """Create the header and collapsible diff content"""
        yield DiffHeader(self.filename, self.additions, self.deletions)

        # Create collapsible section for diff content
        diff_content = DiffContent(self.lines)
        collapsible = Collapsible(
            diff_content,
            title="",
            expanded_symbol="",
            collapsed_symbol="",
            collapsed=True,
            classes="diff-collapsible",
        )
        yield collapsible

    def on_click(self) -> None:
        """Toggle collapsed state of the diff content on click"""
        collapsible = self.query_one(Collapsible)
        collapsible.collapsed = not collapsible.collapsed
