"""Pull request diff screen module"""

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Header, Static
from textual.worker import get_current_worker

from bb.core.git import get_pr_diff
from bb.models import FileDiff
from bb.tui.screens.base import BaseScreen

# TODO - this entire screen should just be integrated into the detail view.
# reuse what makes sense, delete the rest.


class PRDiffScreen(BaseScreen):
    """Screen for viewing pull request diffs"""

    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down", show=True),
        Binding("k", "scroll_up", "Scroll Up", show=True),
        Binding("l", "next_file", "Next File", show=True),
        Binding("h", "prev_file", "Previous File", show=True),
        Binding("right", "next_file", "Next File", show=False),
        Binding("left", "prev_file", "Previous File", show=False),
        Binding("q", "back", "Back", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("/", "search", "Search", show=False),  # Not implemented yet
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen"""
        yield Header()
        yield ScrollableContainer(
            Static(id="diff_content", classes="diff-content"), id="diff_container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load diff content when screen is mounted"""
        if self.state.current_pr:
            self.load_diff()
        else:
            self.notify("No PR selected", severity="error", timeout=1)
            self.action_back()

    @work(exclusive=True, thread=True)
    def load_diff(self) -> None:
        """Load diff content in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            self.app.call_from_thread(self.notify, "Loading diff...", timeout=1)

            # Get diff content using git command
            diff_result = get_pr_diff(self.state.current_pr.branch)
            if diff_result.is_err():
                self.app.call_from_thread(
                    self.notify,
                    f"Error loading diff: {diff_result.unwrap_err()}",
                    severity="error",
                )
                return

            diff_content = diff_result.unwrap()

            # Parse diff content into file diffs
            current_file = None
            file_diffs = []

            for line in diff_content.splitlines():
                if line.startswith("diff --git"):
                    if current_file:
                        file_diffs.append(current_file)
                    file_path = line.split(" b/")[-1]
                    current_file = FileDiff(filename=file_path)
                if current_file:
                    current_file.add_line(line)

            if current_file:
                file_diffs.append(current_file)

            if not worker.is_cancelled:
                self.state.set_file_diffs(file_diffs)

                def update_display():
                    self.display_current_diff()

                self.app.call_from_thread(update_display)

        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify, f"Error loading diff: {str(e)}", severity="error"
                )

    def format_diff_line(self, line: str) -> str:
        """Format a diff line with color"""
        if line.startswith("+"):
            return f"[green]{line}[/]"
        elif line.startswith("-"):
            return f"[red]{line}[/]"
        elif line.startswith("@@"):
            return f"[blue]{line}[/]"
        elif line.startswith("diff --git"):
            return f"[bold yellow]{line}[/]"
        return line

    def display_current_diff(self) -> None:
        """Display the current file diff"""
        if not self.state.file_diffs:
            self.query_one("#diff_content").update("[dim]No changes to display[/]")
            return

        current_diff = self.state.file_diffs[self.state.current_file_index]

        # Format the diff header
        content = [
            f"[bold]File {self.state.current_file_index + 1} of {len(self.state.file_diffs)}:[/]",
            f"[bold yellow]{current_diff.filename}[/]",
            f"[bold]Changes:[/] [green]+{current_diff.stats['additions']}[/] [red]-{current_diff.stats['deletions']}[/]",
            "",
        ]

        # Format each line of the diff
        diff_lines = [self.format_diff_line(line) for line in current_diff.lines]

        content.extend(diff_lines)
        self.query_one("#diff_content").update("\n".join(content))

    def action_next_file(self) -> None:
        """Show next file diff"""
        if (
            self.state.file_diffs
            and self.state.current_file_index < len(self.state.file_diffs) - 1
        ):
            self.state.current_file_index += 1
            self.display_current_diff()
            self.notify(
                f"Showing file {self.state.current_file_index + 1} of {len(self.state.file_diffs)}",
                timeout=1,
            )

    def action_prev_file(self) -> None:
        """Show previous file diff"""
        if self.state.file_diffs and self.state.current_file_index > 0:
            self.state.current_file_index -= 1
            self.display_current_diff()
            self.notify(
                f"Showing file {self.state.current_file_index + 1} of {len(self.state.file_diffs)}",
                timeout=1,
            )

    def action_scroll_down(self) -> None:
        """Scroll diff content down"""
        container = self.query_one("#diff_container")
        container.scroll_page(1)

    def action_scroll_up(self) -> None:
        """Scroll diff content up"""
        container = self.query_one("#diff_container")
        container.scroll_page(-1)

    def action_back(self) -> None:
        """Return to previous screen"""
        self.app.pop_screen()

    def action_refresh(self) -> None:
        """Reload the diff content"""
        self.load_diff()

    class Meta:
        name = "pr_diff"
