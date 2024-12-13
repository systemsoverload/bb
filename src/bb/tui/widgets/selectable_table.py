from dataclasses import dataclass
from typing import List

from textual.message import Message
from textual.widgets import DataTable


@dataclass
class SelectableRow:
    """Represents a selectable row in the table"""

    data: list
    selected: bool = False

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, val):
        self.data[key] = val


class SelectableTable(DataTable):
    """An interactive table that supports row selection"""

    class RowSelected(Message):
        """Posted when a row is selected"""

        def __init__(self, row_index: int, row_data: SelectableRow) -> None:
            self.row_index = row_index
            self.row_data = row_data
            super().__init__()

    class SelectionChanged(Message):
        """Posted when selection state changes"""

        def __init__(self, selected_rows: List[SelectableRow]) -> None:
            self.selected_rows = selected_rows
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        self.selected_rows: List[int] = []

    def toggle_row_selection(self, row_index: int) -> None:
        """Toggle selection state of a row"""
        if row_index in self.selected_rows:
            self.selected_rows.remove(row_index)
        else:
            self.selected_rows.append(row_index)
        self.refresh_row(row_index)

        # Post selection changed message
        selected_data = [SelectableRow(self.get_row_at(i)) for i in self.selected_rows]
        self.post_message(self.SelectionChanged(selected_data))

    def on_key_space(self) -> None:
        """Handle space key to toggle row selection"""
        if self.cursor_coordinate:
            self.toggle_row_selection(self.cursor_coordinate.row)

    def on_click(self, event) -> None:
        """Handle mouse clicks for selection"""
        # TODO - mouse clicking is broken...
        coordinate = self.get_cell_coordinate(event.x, event.y)
        if coordinate and coordinate.row is not None:
            self.toggle_row_selection(coordinate.row)

    # def get_cell_style(self, row_index: int, column_index: int) -> str:
    #     """Apply style to selected rows"""
    #     style = super().get_cell_style(row_index, column_index)
    #     if row_index in self.selected_rows:
    #         style = f"{style} reverse"
    #     return style

    def clear_selection(self) -> None:
        """Clear all selected rows"""
        self.selected_rows.clear()
        self.refresh()
        self.post_message(self.SelectionChanged([]))
