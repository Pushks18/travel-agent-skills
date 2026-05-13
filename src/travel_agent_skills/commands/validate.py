from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from travel_agent_skills.validation import discover_skills, validate_skill

console = Console()


def print_result(skill_dir: Path, errors: list[str]) -> None:
    """Print validation results for one skill directory."""
    if not errors:
        console.print(f"[green]PASS[/green] {skill_dir}")
        return

    console.print(f"[red]FAIL[/red] {skill_dir}")
    for error in errors:
        console.print(f"  - {error}")


def register(app: typer.Typer) -> None:
    """Register validate-related CLI commands on the Typer app."""
    @app.command()
    def validate(
        path: Path | None = typer.Argument(None, help="Skill directory to validate."),
        validate_all: bool = typer.Option(False, "--all", help="Validate every skill in skills/."),
    ) -> None:
        """Validate one skill or all skills."""
        project_root = Path.cwd()
        skill_dirs = discover_skills(project_root) if validate_all else [path]
        if not skill_dirs or any(skill_dir is None for skill_dir in skill_dirs):
            raise typer.BadParameter("Provide a skill path or use --all.")

        failed = False
        for skill_dir in skill_dirs:
            result = validate_skill(skill_dir, project_root=project_root)
            print_result(skill_dir, result.errors)
            failed = failed or not result.passed

        if failed:
            raise typer.Exit(code=1)
