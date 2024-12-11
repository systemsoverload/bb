from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.syntax import Syntax

from . import BaseView


class DiffView(BaseView):
    """Pull request diff view with file-by-file navigation"""

    HELP_TEXT = {
        'h/←': 'Previous file',
        'l/→': 'Next file',
        'j/↓': 'Scroll down',
        'k/↑': 'Scroll up',
        'f': 'Page down',
        'b': 'Page up',
        'gg': 'Top',
        'G': 'Bottom',
        'v': 'Details',
        'q': 'Back'
    }

    def generate(self) -> Layout:
        """Generate the diff view with file navigation"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="navigator", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        pr = self.state.current_pr
        if not pr:
            layout["body"].update(Panel("No pull request selected"))
            return layout

        # Header
        header_text = Text(f"\n Diff for PR #{pr.id}: {pr.title}", style="bold blue")
        layout["header"].update(Align.center(header_text))

        # File navigation bar
        if self.state.file_diffs:
            nav_table = Table(show_header=False, box=None)
            for idx, file_diff in enumerate(self.state.file_diffs):
                style = "reverse" if idx == self.state.current_file_index else ""
                stats_style = "green" if file_diff.stats["additions"] > 0 else ""
                if file_diff.stats["deletions"] > 0:
                    stats_style = "red" if not stats_style else "yellow"

                nav_table.add_row(
                    Text(f"[{idx + 1}/{len(self.state.file_diffs)}]", style=style),
                    Text(file_diff.filename, style=style),
                    Text(file_diff.stats_text, style=f"{style} {stats_style}".strip()),
                )
            layout["navigator"].update(nav_table)
        else:
            layout["navigator"].update(Text("No changes found"))

        # Diff content
        if self.state.file_diffs and self.state.current_file_index >= 0:
            current_diff = self.state.current_file_diff
            if current_diff:
                # Calculate visible lines
                visible_lines = current_diff.lines[
                    self.state.scroll_position:
                    self.state.scroll_position + self.state.viewport_height
                ]

                # Format diff with syntax highlighting
                diff_text = "\n".join(visible_lines)
                syntax = Syntax(
                    diff_text,
                    "diff",
                    theme="monokai",
                    line_numbers=True,
                    start_line=self.state.scroll_position + 1
                )

                # Add scroll indicators
                scroll_indicator = ""
                if self.state.scroll_position > 0:
                    scroll_indicator += "↑ More above\n"
                if (self.state.scroll_position + self.state.viewport_height
                        < len(current_diff.lines)):
                    scroll_indicator += "\n↓ More below"

                diff_layout = Layout()
                diff_layout.split_column(
                    Layout(syntax),
                    Layout(Align.center(scroll_indicator), size=3)
                )

                layout["body"].update(Panel(
                    diff_layout,
                    title=f"File: {current_diff.filename}",
                    border_style="blue"
                ))
        else:
            layout["body"].update(Panel("No diff content available"))

        # Footer with navigation info and help text
        help_parts = []
        if self.state.file_diffs:
            current_diff = self.state.current_file_diff
            if current_diff:
                file_pos = f"File {self.state.current_file_index + 1}/{len(self.state.file_diffs)}"
                line_pos = f"Line {self.state.scroll_position + 1}/{len(current_diff.lines)}"
                help_parts.extend([file_pos, line_pos])

        help_text = " | ".join(f"{k}: {v}" for k, v in self.HELP_TEXT.items())
        help_parts.append(help_text)

        layout["footer"].update(Panel(" | ".join(help_parts), style="dim"))

        return layout
