from rich import print
import click


@click.group()
def cli():
    pass


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        print(f"Hello, [bold magenta]{name}[/bold magenta]!", ":vampire:")


def main():
    cli()


cli.add_command(hello)
