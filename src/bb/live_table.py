
# pip install readchar
# https://github.com/magmax/python-readchar seems low-overhead and simple
from readchar import key, readkey
from rich.console import Console
from rich.live import Live
from rich.style import Style
from rich.table import Table

SELECTED = Style(color="blue", bgcolor="white", bold=True)


def generate_table(console, title, headers, rows, selected) -> Table:

    table = Table(title=title)

    table.add_column("selected")
    for h in headers:
        table.add_column(h)

    size = console.height - 4
    if len(rows) + 3 > size:
        if selected < size / 2:
            rows = rows[:size]
        elif selected + size / 2 > len(rows):
            rows = rows[-size:]
            selected -= len(rows) - size
        else:
            rows = rows[selected - size // 2 : selected + size // 2]
            selected -= selected - size // 2

    for i, row in enumerate(rows):
        table.add_row(*row, style=SELECTED if i == selected else None)

    return table


def generate_live_table(title, headers, rows):
    console = Console()
    selected = 0
    with Live(
        generate_table(console, title, headers, rows, selected), auto_refresh=False
    ) as live:
        while True:
            ch = readkey()

            if ch == key.UP or ch == "k":
                selected = max(0, selected - 1)
            if ch == key.DOWN or ch == "j":
                selected = min(len(rows) - 1, selected + 1)
            if ch == key.SPACE:
                if rows[selected][0] == '[ ]':
                    rows[selected][0] = '[X]'
                else:
                    rows[selected][0] = '[ ]'
            if ch == key.ENTER:
                live.stop()
                break
            live.update(generate_table(console, title, headers, rows, selected), refresh=True)

    return [i for i in rows if i[0] == "[X]"]
