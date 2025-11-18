from rich.console import Console
from rich.prompt import Prompt, Confirm

## Config
no_config_file = "No config file found at [red]{path}[/red], running setup..."
plex_token_explainer = """Pomelo requires a [b]Plex token[/b] to connect to your Plex server.
     To find your Plex token, follow instructions here: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
"""
advanced_settings = "Update advanced settings?"


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
