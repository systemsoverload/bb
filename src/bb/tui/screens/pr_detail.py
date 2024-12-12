"""Pull request detail screen module"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static
from textual import work
from textual.worker import get_current_worker

from bb.tui.screens.base import BaseScreen

class PRDetailScreen(BaseScreen):
    """Screen for displaying pull request details"""

    BINDINGS = [
        Binding("v", "back_to_list", "Return to List", show=True),
        Binding("D", "view_diff", "View Diff", show=True),
        Binding("a", "approve", "Approve", show=True),
        Binding("c", "comment", "Comment", show=True),
        Binding("q", "back", "Back", show=True),
        Binding("o", "open_browser", "Open in Browser", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen"""
        yield Header()
        yield Container(
            Static(id="pr_title", classes="pr-title"),
            Horizontal(
                ScrollableContainer(
                    Static(id="pr_meta", classes="pr-meta"),
                    id="meta_container"
                ),
                ScrollableContainer(
                    Static(id="pr_description", classes="pr-description"),
                    id="description_container"
                ),
            ),
            classes="pr-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen with PR data"""
        if not self.state.current_pr:
            self.notify("No PR selected", severity="error")
            self.action_back()
            return

        self.load_pr_details()

    @work(exclusive=True, thread=True)
    def load_pr_details(self) -> None:
        """Load PR details in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            pr = self.state.current_pr

            def update_display():
                # Update title
                self.query_one("#pr_title").update(
                    f"PR #{pr.id}: {pr.title}"
                )

                # Update metadata
                meta = [
                    f"[bold]Author:[/] {pr.author}",
                    f"[bold]Branch:[/] {pr.branch}",
                    f"[bold]Status:[/] {pr.status}",
                    f"[bold]Created:[/] {pr.created}",
                    "",
                    "[bold]Reviewers:[/]",
                    *[f"  • {reviewer}" for reviewer in pr.reviewers],
                    "",
                    "[bold]Approvals:[/]",
                    *[f"  • {approver}" for approver in pr.approvals],
                    "",
                    f"[link={pr.web_url}]View in Browser[/link]"
                ]
                self.query_one("#pr_meta").update("\n".join(meta))

                # Update description
                desc = pr.description if pr.description else "*No description provided*"
                self.query_one("#pr_description").update(desc)

            self.app.call_from_thread(update_display)

        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify,
                    f"Error loading PR details: {str(e)}",
                    severity="error"
                )

    def action_back_to_list(self) -> None:
        """Return to PR list"""
        self.app.pop_screen()

    def action_view_diff(self) -> None:
        """View PR diff"""
        if self.state.current_pr:
            self.app.push_screen("pr_diff")

    def action_back(self) -> None:
        """Go back to previous screen"""
        self.app.pop_screen()

    def action_open_browser(self) -> None:
        """Open PR in web browser"""
        import webbrowser
        pr = self.state.current_pr
        if pr and pr.web_url:
            webbrowser.open(pr.web_url, new=2)
            self.notify("Opening PR in browser...")
        else:
            self.notify("Unable to open PR in browser", severity="error")

    def action_approve(self) -> None:
        """Approve the PR (not implemented)"""
        self.notify("PR approval not implemented yet", severity="warning")

    def action_comment(self) -> None:
        """Add a comment to the PR (not implemented)"""
        self.notify("PR commenting not implemented yet", severity="warning")
