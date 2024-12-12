"""Pull request list screen module"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Header, Footer
from textual.worker import Worker, get_current_worker
from textual import work

from bb.core.api import get_prs, WEB_BASE_URL
from bb.models import PullRequest
from bb.exceptions import IPWhitelistException
from bb.tui.screens.base import BaseScreen

class PRListScreen(BaseScreen):
    """Pull request list screen showing all open PRs"""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=True),
        Binding("k", "cursor_up", "Up", show=True),
        Binding("v", "view_details", "View Details", show=True),
        Binding("D", "view_diff", "View Diff", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("/", "search", "Search", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen"""
        yield Header(show_clock=True)
        yield DataTable(id="pr_table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen and load data"""
        table = self.query_one("#pr_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column("ID", width=8)
        table.add_column("Title", width=40)
        table.add_column("Author", width=20)
        table.add_column("Status", width=12)
        table.add_column("Approvals", width=10)

        # Start loading PRs
        self.load_prs()

    @work(exclusive=True, thread=True)
    def load_prs(self) -> None:
        """Load pull requests in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            # Clear existing table
            table = self.query_one("#pr_table", DataTable)
            self.app.call_from_thread(table.clear)
            self.app.call_from_thread(self.notify, "Loading pull requests...")

            # Fetch PRs
            prs_result = get_prs(self.state.repo_slug, _all=True)
            if prs_result.is_err():
                error = prs_result.unwrap_err()
                if isinstance(error, IPWhitelistException):
                    self.app.call_from_thread(
                        self.notify,
                        "IP not whitelisted. Please check your BitBucket settings.",
                        severity="error"
                    )
                else:
                    self.app.call_from_thread(
                        self.notify,
                        f"Error loading PRs: {str(error)}",
                        severity="error"
                    )
                return

            prs_data = prs_result.unwrap()
            if not worker.is_cancelled:
                if prs_data:
                    # Update state and table
                    self.state.prs = [PullRequest.from_api_response(pr) for pr in prs_data]

                    def update_table():
                        table.clear()
                        for pr in self.state.prs:
                            table.add_row(
                                f"[link={WEB_BASE_URL}/{self.state.repo_slug}/pull-requests/{pr.id}]{pr.id}[/link]",
                                pr.title,
                                pr.author,
                                pr.status,
                                str(len(pr.approvals))
                            )
                        if table.row_count > 0:
                            table.move_cursor(row=0)
                    self.app.call_from_thread(update_table)
                else:
                    self.app.call_from_thread(self.notify, "No pull requests found", severity="warning")

        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self.notify, f"Error loading PRs: {str(e)}", severity="error")

    def action_cursor_down(self) -> None:
        """Move cursor down"""
        table = self.query_one("#pr_table", DataTable)
        if table.row_count > 0:
            current = table.cursor_coordinate
            if current.row < table.row_count - 1:
                table.move_cursor(row=current.row + 1)

    def action_cursor_up(self) -> None:
        """Move cursor up"""
        table = self.query_one("#pr_table", DataTable)
        if table.row_count > 0:
            current = table.cursor_coordinate
            if current.row > 0:
                table.move_cursor(row=current.row - 1)

    def action_view_details(self) -> None:
        """View PR details"""
        table = self.query_one("#pr_table", DataTable)
        if table.row_count > 0 and self.state.prs:
            current_row = table.cursor_coordinate.row
            self.state.set_current_pr(self.state.prs[current_row])
            self.app.push_screen("pr_detail")

    def action_view_diff(self) -> None:
        """View PR diff directly from list"""
        table = self.query_one("#pr_table", DataTable)
        if table.row_count > 0 and self.state.prs:
            current_row = table.cursor_coordinate.row
            self.state.set_current_pr(self.state.prs[current_row])
            self.app.push_screen("pr_diff")

    def action_refresh(self) -> None:
        """Refresh PR list"""
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
                self.notify(f"Error loading PRs: {event.worker.error}", severity="error")

