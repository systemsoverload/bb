from dataclasses import dataclass
from typing import List, Optional

from rich.style import Style
from rich.table import Table
from textual.widgets import Static


@dataclass
class LiveRow:
    """A row in the live table"""

    data: list
    style: Optional[Style] = None


class LiveTable(Static):
    """A table that supports live updates"""

    DEFAULT_CSS = """
    LiveTable {
        height: auto;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        title: str = "",
        *args,
        headers: List[str] = [],
        zebra_stripes: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.title = title
        self.headers = headers or []
        self.rows: List[LiveRow] = []
        self.zebra_stripes = zebra_stripes
        self._table: Optional[Table] = None

    def _create_table(self) -> Table:
        """Create a new Rich Table instance"""
        table = Table(
            title=self.title,
            show_header=bool(self.headers),
            show_lines=True,
        )

        # Add columns
        for header in self.headers:
            table.add_column(header)

        # Add rows with optional zebra striping
        for idx, row in enumerate(self.rows):
            style = row.style
            if self.zebra_stripes and not style:
                style = Style(bgcolor="rgb(20,20,20)") if idx % 2 else None
            table.add_row(*row.data, style=style)

        return table

    def add_row(self, *values, style: Optional[Style] = None) -> None:
        """Add a new row to the table"""
        self.rows.append(LiveRow(list(values), style))
        self.refresh()

    def clear(self) -> None:
        """Clear all rows from the table"""
        self.rows.clear()
        self.refresh()

    def remove_row(self, index: int) -> None:
        """Remove a row by index"""
        if 0 <= index < len(self.rows):
            self.rows.pop(index)
            self.refresh()

    def update_row(self, index: int, *values, style: Optional[Style] = None) -> None:
        """Update a row's values and style"""
        if 0 <= index < len(self.rows):
            self.rows[index] = LiveRow(list(values), style)
            self.refresh()

    def render(self) -> Table:
        """Render the current table state"""
        self._table = self._create_table()
        return self._table
