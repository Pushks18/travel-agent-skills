from __future__ import annotations

import typer
from rich.console import Console

from travel_agent_skills.packaging import package_skill

console = Console()


def register(app: typer.Typer) -> None:
    """Register package-related CLI commands on the Typer app."""
    @app.command()
    def package(name: str = typer.Argument(..., help="Skill name to package.")) -> None:
        """Package a skill into a Claude-compatible ZIP."""
        try:
            result = package_skill(name)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

        console.print(f"Packaged skill: {result.zip_path}")
        console.print(f"Release metadata: {result.release_path}")
        console.print(f"SHA-256: {result.checksum}")

