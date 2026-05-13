from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console

from travel_agent_skills.registry import delete_skill_entry, get_skill_entry

console = Console()


def register(app: typer.Typer) -> None:
    """Register delete-related CLI commands on the Typer app."""
    @app.command()
    def delete(
        name: str = typer.Argument(..., help="Skill name to delete."),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
    ) -> None:
        """Delete a skill directory and remove it from registry.yaml."""
        project_root = Path.cwd()
        registry_path = project_root / "registry.yaml"

        entry = get_skill_entry(registry_path, name)
        if entry is None:
            raise typer.BadParameter(f"Skill not found in registry.yaml: {name}")

        skill_dir = project_root / entry["path"]

        if not yes:
            confirmed = typer.confirm(f"Delete skill '{name}' and all its files?", default=False)
            if not confirmed:
                console.print("Aborted.")
                raise typer.Exit()

        delete_skill_entry(registry_path, name)

        if skill_dir.exists():
            shutil.rmtree(skill_dir)

        console.print(f"Deleted skill: {name}")
