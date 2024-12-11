"""Main TUI application class"""

from typing import Dict, Type
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from readchar import readkey

from bb.core.git import fetch, diff

from bb.tui.state import AppState, ViewState
from bb.tui.models import FileDiff, PullRequest
from bb.tui.views.list_view import ListView
from bb.tui.views.detail_view import DetailView
from bb.tui.views.diff_view import DiffView
from bb.tui.handlers.input import InputHandler


class PRReviewTUI:
    """Main TUI application class for PR review"""

    def __init__(self, repo_slug: str):
        """Initialize the TUI application"""
        self.console = Console()
        self.state = AppState(repo_slug=repo_slug)
        self.input_handler = InputHandler(self.state)

        # Map view states to their corresponding view classes
        self.views: Dict[ViewState, Type] = {
            ViewState.LIST: ListView,
            ViewState.DETAIL: DetailView,
            ViewState.DIFF: DiffView
        }

    def fetch_prs(self):
        """Fetch pull requests from the API"""
        from bb.core.api import get_prs
        try:
            prs_data = get_prs(self.state.repo_slug, _all=True).unwrap()
            self.state.prs = [PullRequest.from_api_response(pr) for pr in prs_data]
            self.state.status_message = f"Loaded {len(self.state.prs)} pull requests"
        except Exception as e:
            self.state.status_message = f"Error loading PRs: {str(e)}"

    def generate_view(self) -> Layout:
        """Generate the appropriate view based on current state"""
        view_class = self.views.get(self.state.view_state)
        if not view_class:
            raise ValueError(f"No view found for state {self.state.view_state}")

        view = view_class(self.state, self.console)
        return view.generate()

    def run(self):
        """Main application loop"""
        try:
            # Initial PR fetch
            self.fetch_prs()

            with Live(auto_refresh=False, screen=True) as live:
                running = True
                while running:
                    # Update viewport height based on console size
                    self.state.update_viewport_height(self.console.height)

                    # Generate and display the current view
                    try:
                        layout = self.generate_view()
                        live.update(layout, refresh=True)
                    except Exception as e:
                        self.state.status_message = f"Error rendering view: {str(e)}"
                        continue

                    # Handle input
                    try:
                        ch = readkey()
                        running = self.input_handler.handle_input(ch)
                    except Exception as e:
                        self.state.status_message = f"Error handling input: {str(e)}"
                        continue

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass
        except Exception as e:
            self.console.print(f"[red]Fatal error: {str(e)}[/]")
        finally:
            # Cleanup if needed
            pass


def review_prs(repo_slug: str):
    """Entry point for the PR review TUI"""
    try:
        tui = PRReviewTUI(repo_slug)
        tui.run()
    except Exception as e:
        Console().print(f"[red]Error: {str(e)}[/]")


if __name__ == "__main__":
    review_prs("bitbucket/core")
