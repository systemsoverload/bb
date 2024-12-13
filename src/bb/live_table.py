from dataclasses import dataclass

from readchar import key, readkey
from rich.console import Console
from rich.live import Live
from rich.style import Style
from rich.table import Table

SELECTED = Style(color="blue", bgcolor="white", bold=True)


@dataclass
class SelectableRow:
    data: list
    selected: bool

    def __getitem__(self, key):
        self.data[key]

    def __setitem__(self, key, val):
        self.data[key] = val

    def insert(self, idx, val):
        self.data.insert(idx, val)


def generate_table(console, title, headers, rows: list[SelectableRow], cur) -> Table:
    table = Table(title=title)

    table.add_column("selected")
    for h in headers:
        table.add_column(h)

    size = console.height - 4
    if len(rows) + 3 > size:
        if cur < size / 2:
            rows = rows[:size]
        elif cur + size / 2 > len(rows):
            rows = rows[-size:]
            cur -= len(rows) - size
        else:
            rows = rows[cur - size // 2 : cur + size // 2]
            cur -= cur - size // 2

    for i, row in enumerate(rows):
        if row.data[0] not in ["[ ]", "[X]"]:
            row.data.insert(0, "[ ]")
        if row.selected:
            row.data[0] = "[X]"
        else:
            row.data[0] = "[ ]"

        table.add_row(*row.data, style=SELECTED if i == cur else None)

    return table


def generate_live_table(title, headers, rows: list[SelectableRow]) -> list:
    # XXX - This is as generic as possible, but not particularly extensible at this point and pretty specific
    # to displaying PR reviewers in a selectable table.

    # XXX - This is a minimum working UI. It will _probably_ make sense to bring in a full Textual inline
    # app with buttons and various widgets, but this works fine for now.
    console = Console()
    cur = 0
    with Live(
        generate_table(console, title, headers, rows, cur),
        auto_refresh=False,
        transient=True,
    ) as live:
        while True:
            ch = readkey()

            if ch == key.UP or ch == "k":
                cur = max(0, cur - 1)
            if ch == key.DOWN or ch == "j":
                cur = min(len(rows) - 1, cur + 1)
            if ch == key.SPACE:
                rows[cur].selected = not rows[cur].selected
            if ch == key.ENTER:
                live.stop()
                break
            live.update(
                generate_table(console, title, headers, rows, cur), refresh=True
            )

    # Return "selected" rows, minus the selection state column
    return [i.data[1:] for i in rows if i.selected]
