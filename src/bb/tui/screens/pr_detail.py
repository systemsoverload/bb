"""Pull request detail screen module"""


from textual import log, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (Container, Horizontal, ScrollableContainer,
                                Vertical)
from textual.widgets import Footer, Header, Markdown, Static
from textual.worker import Worker, get_current_worker

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
            Vertical(
                Horizontal(
                    ScrollableContainer(
                        Static(id="pr_meta", classes="pr-meta"), id="meta_container"
                    ),
                    ScrollableContainer(
                        Markdown(id="pr_description", classes="pr-description"),
                        id="description_container",
                    ),
                ),
                ScrollableContainer(
                    Static(id="pr_diffs", classes="pr-diffs"), id="diffs_container"
                ),
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
        self.query_one("#pr_title").update("")
        self.query_one("#pr_meta").update("")
        self.query_one("#pr_description").update("")
        self.query_one("#pr_diffs").update("")

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
                self.query_one("#diffs_container").loading = False
                self.notify("No PR selected", severity="error", timeout=1)

            self.app.call_from_thread(handle_no_pr)
            return

        try:
            # Set loading state
            self.app.call_from_thread(
                setattr, self.query_one("#diffs_container"), "loading", True
            )

            diff_result = self.state.current_pr.get_diff()
            if diff_result.is_err():

                def handle_error():
                    self.query_one("#diffs_container").loading = False
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
                    # Format and display diff content
                    diff_content = []
                    for diff in file_diffs:
                        # Add file status if available
                        status_str = f" ({diff.status})" if diff.status else ""
                        header = f"[bold]{diff.filename}[/]{status_str} (+{diff.stats['additions']}, -{diff.stats['deletions']})"
                        content = [header, ""]

                        # Add formatted diff lines
                        for line in diff.lines:
                            if line.startswith("+"):
                                content.append(f"[green]{line}[/]")
                            elif line.startswith("-"):
                                content.append(f"[red]{line}[/]")
                            elif line.startswith("@@"):
                                content.append(f"[blue]{line}[/]")
                            else:
                                content.append(line)
                        content.append("")
                        diff_content.extend(content)

                    self.query_one("#pr_diffs").update("\n".join(diff_content))
                    self.query_one("#diffs_container").loading = False

                self.app.call_from_thread(update_display)

        except Exception as e:
            if not worker.is_cancelled:

                def handle_error(e):
                    self.query_one("#diffs_container").loading = False
                    self.notify(
                        f"Error loading diffs: {str(e)}", severity="error", timeout=1
                    )

                self.app.call_from_thread(handle_error, e)

    @work(thread=True)
    def load_pr_details(self) -> None:
        """Load PR details in background thread"""
        worker = get_current_worker()
        if worker.is_cancelled:
            log.debug("Worker cancelled, returning early")
            return

        try:
            log.debug("Loading PR details")
            pr = self.state.current_pr

            if not pr:
                log.error("No PR found in state")
                self.app.call_from_thread(
                    self.notify, "No pull request selected", severity="error", timeout=1
                )
                return

            log.debug(f"PR data loaded: #{pr.id} - {pr.title}")

            def update_display():
                try:
                    log.debug("Updating title")
                    self.query_one("#pr_title").update(f"PR #{pr.id}: {pr.title}")

                    log.debug("Updating metadata")
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
                        f"[link={pr.web_url}]View in Browser[/link]",
                    ]
                    meta_widget = self.query_one("#pr_meta")
                    if meta_widget:
                        meta_widget.update("\n".join(meta))
                    else:
                        log.error("Could not find #pr_meta widget")

                    log.debug("Updating description")
                    desc = (
                        pr.description
                        if pr.description
                        else "*No description provided*"
                    )
                    desc_widget = self.query_one("#pr_description", Markdown)
                    if desc_widget:
                        desc_widget.update(desc)
                    else:
                        log.error("Could not find #pr_description widget")

                except Exception as e:
                    log.error(f"Error in update_display: {str(e)}")
                    raise

            log.debug("Calling update_display from thread")
            self.app.call_from_thread(update_display)

        except Exception as e:
            log.error(f"Error loading PR details: {str(e)}")
            if not worker.is_cancelled:
                self.app.call_from_thread(
                    self.notify, f"Error loading PR details: {str(e)}", severity="error"
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
            self.notify("Opening PR in browser...", timeout=1)
        else:
            self.notify("Unable to open PR in browser", severity="error", timeout=1)

    def action_approve(self) -> None:
        """Approve the PR (not implemented)"""
        self.notify("PR approval not implemented yet", severity="warning", timeout=1)

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
