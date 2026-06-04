from __future__ import annotations

import typer
from rich.console import Console

from travel_agent_skills import __version__
from travel_agent_skills.commands import create as create_command
from travel_agent_skills.commands import delete as delete_command
from travel_agent_skills.commands import generate as generate_command
from travel_agent_skills.commands import inspect as inspect_command
from travel_agent_skills.commands import package as package_command
from travel_agent_skills.commands import validate as validate_command

console = Console()

app = typer.Typer(
    no_args_is_help=True,
    help="Create, validate, release, and consume shared travel agent skills.",
)

create_command.register(app)
delete_command.register(app)
generate_command.register(app)
inspect_command.register(app)
package_command.register(app)
validate_command.register(app)


@app.command()
def version() -> None:
    """Show the CLI version."""
    console.print(f"travel-agent-skills {__version__}")


if __name__ == "__main__":
    app()
