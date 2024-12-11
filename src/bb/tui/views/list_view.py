from rich.layout import Layout
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

from . import BaseView
from ..state import AppState


class ListView(BaseView):
    """Pull request list view"""

    HELP_TEXT = {
        'j/↓': 'Next PR',
        'k/↑': 'Previous PR',
        'v': 'View details',
        'D': 'View diff',
        'r': 'Refresh',
        '/': 'Search',
        'q': 'Quit'
    }

    def generate(self) -> Layout:
        """Generate the PR list view"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Header
        header_text = Text(f"\n Pull Requests for {self.state.repo_slug}", style="bold blue")
        header_text.append(f"\n {self.state.status_message}", style="italic")
        layout["header"].update(Align.center(header_text))

        # PR Table
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=6)
        table.add_column("Title", width=40)
        table.add_column("Author", width=20)
        table.add_column("Status", width=10)
        table.add_column("Approvals", width=10)
        table.add_column("Branch", width=20)

        for idx, pr in enumerate(self.state.prs):
            row_style = "reverse" if idx == self.state.current_pr_index else ""
            status_style = "green" if pr.status == "Approved" else "yellow"

            table.add_row(
                str(pr.id),
                pr.title,
                pr.author,
                Text(pr.status, style=status_style),
                str(len(pr.approvals)),
                pr.branch,
                style=row_style
            )

        layout["body"].update(table)

        # Footer with keybindings
        help_text = " | ".join(f"{k}: {v}" for k, v in self.HELP_TEXT.items())
        layout["footer"].update(Panel(help_text, style="dim"))

        return layout
