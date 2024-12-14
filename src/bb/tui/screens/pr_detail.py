from typing import Dict

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Markdown, Static
from textual.worker import Worker, get_current_worker

from bb.tui.screens.base import BaseScreen
from bb.tui.widgets import FileDiff


class PRTitleWidget(Static):
    """Widget for displaying PR title"""

    pass


class PRMetaWidget(Static):
    """Widget for displaying PR metadata"""

    pass


class DiffsContainer(ScrollableContainer):
    pass


class PRDetailScreen(BaseScreen):
    """Screen for displaying pull request details"""

    BINDINGS = [
        Binding("a", "approve", "Approve", show=True),
        Binding("c", "comment", "Comment", show=True),
        Binding("q", "back", "Back", show=True),
        Binding("o", "open_browser", "Open in Browser", show=True),
    ]

    CSS_PATH = "../css/pr_detail.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen"""
        yield Header()
        yield Container(
            Horizontal(
                PRTitleWidget(id="pr_title", classes="pr-title"), classes="pr-header"
            ),
            Vertical(
                Horizontal(
                    ScrollableContainer(
                        PRMetaWidget(id="pr_meta", classes="pr-meta"),
                        id="meta_container",
                    ),
                    ScrollableContainer(
                        Markdown(id="pr_description", classes="pr-description"),
                        id="description_container",
                    ),
                ),
                DiffsContainer(id="diffs_container"),
                classes="pr-container",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen with PR data"""
        if not self.state.current_pr:
            self.notify("No PR selected", severity="error", timeout=1)
            self.action_back()
            return

        self.refresh_pr_data()

    def on_screen_resume(self) -> None:
        """Called when screen becomes active"""
        self.refresh_pr_data()

    def refresh_pr_data(self) -> None:
        """Refresh all PR data"""
        if not self.state.current_pr:
            self.notify("No PR selected", severity="error", timeout=1)
            self.action_back()
            return

        # Clear existing content before loading new data
        self.query_one(PRTitleWidget).update("")
        self.query_one(PRMetaWidget).update("")
        self.query_one(DiffsContainer).remove_children()

        self.load_pr_details()
        self.load_pr_diffs()

    @work(thread=True)
    def load_pr_diffs(self) -> None:
        """Load PR diff content in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        if not self.state.current_pr:

            def handle_no_pr():
                self.query_one(DiffsContainer).loading = False
                self.notify("No PR selected", severity="error", timeout=1)

            self.app.call_from_thread(handle_no_pr)
            return

        try:
            # Set loading state
            self.app.call_from_thread(
                setattr, self.query_one(DiffsContainer), "loading", True
            )

            diff_result = self.state.current_pr.get_diff()
            if diff_result.is_err():

                def handle_error():
                    self.query_one(DiffsContainer).loading = False
                    self.notify(
                        f"Error loading diff: {diff_result.unwrap_err()}",
                        severity="error",
                        timeout=10,
                    )

                self.app.call_from_thread(handle_error)
                return

            file_diffs = diff_result.unwrap()

            if not worker.is_cancelled:
                self.state.set_file_diffs(file_diffs)

                def update_display():
                    # Clear existing diffs
                    diffs_container = self.query_one(DiffsContainer)
                    diffs_container.remove_children()

                    # Add collapsible diff widget for each file
                    for diff in file_diffs:
                        diffs_container.mount(
                            FileDiff(
                                filename=diff.filename,
                                lines=diff.lines,
                                additions=diff.stats["additions"],
                                deletions=diff.stats["deletions"],
                            )
                        )

                    self.query_one(DiffsContainer).loading = False

                self.app.call_from_thread(update_display)

        except Exception as e:
            if not worker.is_cancelled:

                def handle_error():
                    self.query_one(DiffsContainer).loading = False
                    self.notify(
                        f"Error loading diffs: {str(e)}", severity="error", timeout=10
                    )

                self.app.call_from_thread(handle_error)

    @work(thread=True)
    def load_pr_details(self) -> None:
        """Load PR details in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        try:
            pr = self.state.current_pr
            if not pr:

                def handle_no_pr():
                    self.notify("No PR selected", severity="error", timeout=10)

                self.app.call_from_thread(handle_no_pr)
                return

            # TODO - `checks` require an extra API call here, but should be merged with restrictions
            merge_restrictions = None
            mr_result = pr.get_merge_restrictions()

            if mr_result.is_ok():
                merge_restrictions = mr_result.unwrap()

            def update_display():
                # Update title ASAP - defer merge-able status until the follow-up request finishes
                title = f"PR #{pr.id}: {pr.title}"
                self.query_one(PRTitleWidget).update(title)

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
                    # f"[link={pr.web_url}]View in Browser[/link]",
                ]

                if merge_restrictions:
                    can_merge = merge_restrictions.get("can_merge", False)
                    title = "✅" if can_merge else "⚠️  " + title
                    self.query_one(PRTitleWidget).update(title)

                    meta.extend([
                        "[bold]Merge Restrictions:[/]"
                    ])

                    # Add each restriction status
                    restrictions = merge_restrictions.get("restrictions", {})
                    for _, restriction in restrictions.items():
                        if restriction.get("label"):  # Only show restrictions with labels
                            meta.append(f"  {format_restriction_status(restriction)}")

                meta.append("")
                meta.append(f"[link={pr.web_url}]View in Browser[/link]")


                self.query_one(PRMetaWidget).update("\n".join(meta))

                # Update description
                desc = pr.description if pr.description else "*No description provided*"
                self.query_one("#pr_description", Markdown).update(desc)

            self.app.call_from_thread(update_display)

        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify, f"Error loading PR details: {str(e)}", severity="error"
                )

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
            self.notify("Opening PR in browser...", timeout=1)
        else:
            self.notify("Unable to open PR in browser", severity="error", timeout=1)

    @work(thread=True)
    def approve_pr(self) -> None:
        """Approve the current PR in a background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            return

        if not self.state.current_pr:
            self.app.call_from_thread(
                self.notify, "No PR selected", severity="error", timeout=10
            )
            return

        try:
            result = self.state.current_pr.approve()
            if result.is_err():

                def handle_error():
                    error = result.unwrap_err()
                    self.notify(
                        f"Error approving PR: {str(error)}", severity="error", timeout=3
                    )

                self.app.call_from_thread(handle_error)
                return

            def handle_success():
                self.notify("PR approved successfully", timeout=2)
                # TODO - Refresh the PR details to show updated approval status
                # Currently we arent showing anything yet so save the reload
                # self.refresh_pr_data()

            self.app.call_from_thread(handle_success)

        except Exception as e:
            if not worker.is_cancelled:

                def handle_error():
                    self.notify(
                        f"Error approving PR: {str(e)}", severity="error", timeout=3
                    )

                self.app.call_from_thread(handle_error)

    def action_approve(self) -> None:
        """Handle the approve action"""
        if self.state.current_pr:
            self.approve_pr()
        else:
            self.notify("No PR selected to approve", severity="error", timeout=1)

    def action_comment(self) -> None:
        """Add a comment to the PR (not implemented)"""
        self.notify("PR commenting not implemented yet", severity="warning", timeout=1)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes"""
        if event.worker.name in ["load_pr_diffs", "load_pr_details"]:
            if event.state == "cancelled":
                self.notify(
                    f"{event.worker.name} cancelled", severity="warning", timeout=1
                )
            elif event.state == "error":
                self.notify(
                    f"Error in {event.worker.name}: {event.worker.error}",
                    severity="error",
                    timeout=1,
                )

def format_restriction_status(restriction: Dict) -> str:
    """Format a restriction's status for display"""
    status = "✅" if restriction["pass"] else "⚠️ "
    name = restriction["name"]
    label = restriction.get("label", "")
    if label:
        return f"{status} {name}: {label}"
    return f"{status} {name}"
