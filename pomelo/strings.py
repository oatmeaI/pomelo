from rich.console import Console
from rich.prompt import Prompt, Confirm


console = Console()


def error(str, **kwargs):
    console.print(f" [bold red]!! {str}[/bold red]", **kwargs)


def warn(str, **kwargs):
    console.print(f" [bold yellow]!! {str}[/bold yellow]", **kwargs)


def header(str, **kwargs):
    console.print(f" ==>> {str} <<==", **kwargs)


def log(str, **kwargs):
    console.print(f" ->> {str}", **kwargs)


def ask(prompt, **kwargs):
    return Prompt.ask(f" =>> {prompt}", **kwargs)


def confirm(str, **kwargs):
    return Confirm.ask(f" {str}", **kwargs)
