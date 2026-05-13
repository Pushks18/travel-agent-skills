from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from travel_agent_skills.registry import get_skill_entry, list_skill_entries

console = Console()


def format_list(value: Any) -> str:
    """Format registry list values for compact terminal output."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "")


def build_skills_table(entries: dict[str, dict[str, Any]]) -> Table:
    """Build a table for skill registry entries."""
    table = Table(title="Skills")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Owners")
    table.add_column("Tags")
    table.add_column("Path")

    for name, entry in sorted(entries.items()):
        table.add_row(
            name,
            str(entry.get("version", "")),
            str(entry.get("status", "")),
            format_list(entry.get("owners", [])),
            format_list(entry.get("tags", [])),
            str(entry.get("path", "")),
        )
    return table


def print_skill_info(name: str, entry: dict[str, Any]) -> None:
    """Print detailed information for one skill."""
    console.print(f"[bold]{name}[/bold]")
    console.print(f"Version: {entry.get('version', '')}")
    console.print(f"Status: {entry.get('status', '')}")
    console.print(f"Owners: {format_list(entry.get('owners', []))}")
    console.print(f"Tags: {format_list(entry.get('tags', []))}")
    console.print(f"Path: {entry.get('path', '')}")
    console.print(f"Distribution: {format_list(entry.get('distribution', []))}")


def register(app: typer.Typer) -> None:
    """Register list and info CLI commands on the Typer app."""
    @app.command("list")
    def list_skills() -> None:
        """List skills from registry.yaml."""
        entries = list_skill_entries(Path.cwd() / "registry.yaml")
        console.print(build_skills_table(entries))

    @app.command()
    def info(name: str = typer.Argument(..., help="Skill name to inspect.")) -> None:
        """Show registry details for one skill."""
        entry = get_skill_entry(Path.cwd() / "registry.yaml", name)
        if entry is None:
            raise typer.BadParameter(f"Skill not found in registry.yaml: {name}")
        print_skill_info(name, entry)

