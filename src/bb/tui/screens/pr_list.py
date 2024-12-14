"""Pull request list screen module"""

from typing import Literal

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header
from textual.worker import Worker, get_current_worker

from bb.tui.screens.base import BaseScreen
from bb.tui.widgets import SelectableTable


class PRListScreen(BaseScreen):
    """Pull request list screen showing all open PRs"""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=True),
        Binding("k", "cursor_up", "Up", show=True),
        Binding("v", "view_details", "View Details", show=True),
        Binding("D", "view_diff", "View Diff", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("a", "show_all", "Show All PRs", show=True),
        Binding("m", "show_mine", "Show My PRs", show=True),
        Binding("n", "show_reviewing", "Show PRs to Review", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
        #pr_table {
            height: 1fr;
            border: solid $primary;
        }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_filter: Literal["_all", "mine", "reviewing"] = "mine"

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen"""
        yield Header(show_clock=True)
        yield SelectableTable(id="pr_table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen and load data"""
        table = self.query_one("#pr_table", SelectableTable)
        table.zebra_stripes = True

        # Add columns
        table.add_column("ID", width=8)
        table.add_column("Title", width=40)
        table.add_column("Author", width=20)
        table.add_column("Status", width=12)
        table.add_column("Comments", width=15)
        table.add_column("Approvals", width=15)

        # Start loading PRs
        self.load_prs()

    def on_selectable_table_row_selected(
        self, event: SelectableTable.RowSelected
    ) -> None:
        """Handle row selection in SelectableTable"""
        if self.state.prs:
            self.state.set_current_pr(self.state.prs[event.row_index])
            self.app.push_screen("pr_detail")

    @work(exclusive=True, thread=True)
    def load_prs(self) -> None:
        """Load pull requests in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            # Clear existing table
            table = self.query_one("#pr_table", SelectableTable)
            self.app.call_from_thread(table.clear)

            filter_msg = {
                "_all": "Loading all pull requests...",
                "mine": "Loading your pull requests...",
                "reviewing": "Loading pull requests to review...",
            }.get(self.current_filter, "Loading pull requests...")

            self.app.call_from_thread(self.notify, filter_msg, timeout=1)

            prs_result = self.state.repo.pullrequests.list(
                _all=self.current_filter == "_all",
                reviewing=self.current_filter == "reviewing",
                mine=self.current_filter == "mine",
            )

            if prs_result.is_err():
                self.app.call_from_thread(
                    self.notify,
                    f"Error loading PRs: {str(prs_result.unwrap_err())}",
                    severity="error",
                )
                return

            prs = prs_result.unwrap()
            if not worker.is_cancelled:
                if prs:
                    self.state.prs = prs

                    def update_table():
                        table.clear()
                        for pr in self.state.prs:
                            table.add_row(
                                f"[link={pr.web_url}]{pr.id}[/link]",
                                pr.title,
                                pr.author,
                                pr.status,
                                pr.comment_count,
                                len(pr.approvals),
                            )
                        if table.row_count > 0:
                            table.move_cursor(row=0)

                    self.app.call_from_thread(update_table)
                else:
                    filter_type = {
                        "_all": "open pull requests",
                        "mine": "pull requests authored by you",
                        "reviewing": "pull requests for you to review",
                    }[self.current_filter]
                    self.app.call_from_thread(
                        self.notify, f"No {filter_type} found", severity="warning"
                    )

        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify, f"Error loading PRs: {str(e)}", severity="error"
                )

    def action_cursor_down(self) -> None:
        """Move cursor down"""
        table = self.query_one("#pr_table", SelectableTable)
        if table.row_count > 0:
            current = table.cursor_coordinate
            if current.row < table.row_count - 1:
                table.move_cursor(row=current.row + 1)

    def action_cursor_up(self) -> None:
        """Move cursor up"""
        table = self.query_one("#pr_table", SelectableTable)
        if table.row_count > 0:
            current = table.cursor_coordinate
            if current.row > 0:
                table.move_cursor(row=current.row - 1)

    def action_view_details(self) -> None:
        """View PR details"""
        table = self.query_one("#pr_table", SelectableTable)
        if table.row_count > 0 and self.state.prs:
            current_row = table.cursor_coordinate.row
            self.state.set_current_pr(self.state.prs[current_row])
            self.app.push_screen("pr_detail")

    def action_view_diff(self) -> None:
        """View PR diff directly from list"""
        table = self.query_one("#pr_table", SelectableTable)
        if table.row_count > 0 and self.state.prs:
            current_row = table.cursor_coordinate.row
            self.state.set_current_pr(self.state.prs[current_row])
            self.app.push_screen("pr_diff")

    def action_show_all(self) -> None:
        """Show all open PRs"""
        self.current_filter = "_all"
        self.load_prs()

    def action_show_mine(self) -> None:
        """Show PRs authored by current user"""
        self.current_filter = "mine"
        self.load_prs()

    def action_show_reviewing(self) -> None:
        """Show PRs where current user is a reviewer"""
        self.current_filter = "reviewing"
        self.load_prs()

    def action_refresh(self) -> None:
        """Refresh PR list with current filter"""
        self.load_prs()

    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes"""
        if event.worker.name == "load_prs":
            if event.state == "cancelled":
                self.notify("PR loading cancelled", severity="warning")
            elif event.state == "error":
                self.notify(
                    f"Error loading PRs: {event.worker.error}", severity="error"
                )
