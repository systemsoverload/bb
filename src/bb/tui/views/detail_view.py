from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.markdown import Markdown

from . import BaseView


class DetailView(BaseView):
    """Pull request detail view"""

    HELP_TEXT = {
        'v': 'Return to list',
        'D': 'View diff',
        'a': 'Approve',
        'c': 'Comment',
        'q': 'Back'
    }

    def generate(self) -> Layout:
        """Generate the PR detail view"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        pr = self.state.current_pr
        if not pr:
            layout["body"].update(Panel("No pull request selected"))
            return layout

        # Header
        header_text = Text(f"\n PR #{pr.id}: {pr.title}", style="bold blue")
        layout["header"].update(Align.center(header_text))

        # Detail content
        details = []
        details.append(f"Author: {pr.author}")
        details.append(f"Branch: {pr.branch}")
        details.append(f"Status: {pr.status}")
        details.append(f"Created: {pr.created}")
        details.append(f"\nReviewers:")
        for reviewer in pr.reviewers:
            details.append(f"  • {reviewer}")
        details.append(f"\nApprovals:")
        for approver in pr.approvals:
            details.append(f"  • {approver}")
        details.append(f"\nDescription:")
        details.append(pr.description)

        layout["body"].update(Panel(
            Markdown("\n".join(details)),
            title="Pull Request Details",
            border_style="blue"
        ))

        # Footer
        help_text = " | ".join(f"{k}: {v}" for k, v in self.HELP_TEXT.items())
        layout["footer"].update(Panel(help_text, style="dim"))

        return layout
