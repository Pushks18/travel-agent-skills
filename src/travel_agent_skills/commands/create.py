from __future__ import annotations

from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from rich.console import Console

from travel_agent_skills.registry import SkillRegistryEntry, upsert_skill_entry
from travel_agent_skills.standards import VALID_SKILL_NAME, VALID_STATUSES

OPTIONAL_RESOURCE_DIRS = ("scripts", "references", "assets")
RESOURCE_DIR_GUIDANCE = {
    "scripts": "executable code agents can run",
    "references": "documentation agents can load on demand",
    "assets": "static templates, schemas, lookup files, or media",
}

console = Console()


def title_from_name(name: str) -> str:
    """Convert a hyphen-case skill name into a readable Markdown title."""
    return " ".join(part.capitalize() for part in name.split("-"))


def default_description(name: str) -> str:
    """Create a useful fallback description when the author does not provide one."""
    title = title_from_name(name).lower()
    return f"Guidance for the {title} workflow. Use when agents need to perform, review, or standardize {title} tasks."


def validate_skill_name(name: str) -> None:
    """Ensure the skill name follows the open Agent Skills naming rules."""
    if len(name) > 64 or not VALID_SKILL_NAME.match(name):
        raise typer.BadParameter(
            "Skill names must be 1-64 characters and use lowercase letters, numbers, and single hyphens."
        )


def validate_status(status: str) -> None:
    """Ensure the registry lifecycle status is one of the supported values."""
    if status not in VALID_STATUSES:
        allowed = ", ".join(sorted(VALID_STATUSES))
        raise typer.BadParameter(f"Status must be one of: {allowed}.")


def selected_resource_dirs(
    *,
    with_scripts: bool = False,
    with_references: bool = False,
    with_assets: bool = False,
    with_all: bool = False,
) -> list[str]:
    """Build the list of optional skill resource folders to create."""
    if with_all:
        return list(OPTIONAL_RESOURCE_DIRS)

    selected = []
    if with_scripts:
        selected.append("scripts")
    if with_references:
        selected.append("references")
    if with_assets:
        selected.append("assets")
    return selected


def create_resource_dirs(skill_dir: Path, resource_dirs: list[str]) -> None:
    """Create selected optional resource folders with placeholders."""
    for resource_dir in resource_dirs:
        directory = skill_dir / resource_dir
        directory.mkdir(exist_ok=True)
        directory.joinpath(".gitkeep").touch()


def prompt_for_resource_dirs() -> list[str]:
    """Ask the author which optional Agent Skills folders to create."""
    selected = []
    for resource_dir in OPTIONAL_RESOURCE_DIRS:
        guidance = RESOURCE_DIR_GUIDANCE[resource_dir]
        if typer.confirm(f"Create {resource_dir}/ for {guidance}?", default=False):
            selected.append(resource_dir)
    return selected


def create_skill(
    *,
    name: str,
    owners: list[str],
    status: str = "draft",
    tags: list[str] | None = None,
    template: str = "basic-skill",
    description: str | None = None,
    resource_dirs: list[str] | None = None,
    force: bool = False,
    project_root: Path | None = None,
) -> Path:
    """Create a skill folder from a template and register it in registry.yaml."""
    validate_skill_name(name)
    validate_status(status)

    root = project_root or Path.cwd()
    template_dir = root / "templates" / template
    template_file = template_dir / "SKILL.md.j2"
    skill_dir = root / "skills" / name

    if not template_file.exists():
        raise typer.BadParameter(f"Template not found: {template}")

    if skill_dir.exists() and not force:
        raise typer.BadParameter(f"Skill already exists: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=True)
    create_resource_dirs(skill_dir, resource_dirs or [])

    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    rendered = env.get_template("SKILL.md.j2").render(
        name=name,
        title=title_from_name(name),
        description=description or default_description(name),
        license="Apache-2.0",
        author=owners[0],
        version="0.1.0",
    )

    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists() and not force:
        raise typer.BadParameter(f"Skill file already exists: {skill_file}")
    skill_file.write_text(rendered, encoding="utf-8")

    upsert_skill_entry(
        root / "registry.yaml",
        name,
        SkillRegistryEntry(
            path=f"skills/{name}",
            version="0.1.0",
            owners=owners,
            status=status,
            tags=tags or ["travel", *name.split("-")],
        ),
    )

    return skill_dir


def register(app: typer.Typer) -> None:
    """Register create-related CLI commands on the Typer app."""
    @app.command()
    def create(
        name: str = typer.Argument(..., help="Skill name in lowercase hyphen-case."),
        owner: list[str] = typer.Option(..., "--owner", "-o", help="Owning team. Can be repeated."),
        status: str = typer.Option("draft", help="Skill lifecycle status."),
        tag: list[str] = typer.Option(None, "--tag", "-t", help="Discovery tag. Can be repeated."),
        template: str = typer.Option("basic-skill", help="Template name from templates/."),
        description: str | None = typer.Option(None, help="Skill description for SKILL.md frontmatter."),
        with_scripts: bool = typer.Option(False, "--with-scripts", help="Create scripts/ for executable helper code."),
        with_references: bool = typer.Option(False, "--with-references", help="Create references/ for on-demand documentation."),
        with_assets: bool = typer.Option(False, "--with-assets", help="Create assets/ for templates, schemas, and static files."),
        with_all: bool = typer.Option(False, "--with-all", help="Create scripts/, references/, and assets/."),
        interactive: bool = typer.Option(False, "--interactive", help="Ask which optional resource folders to create."),
        force: bool = typer.Option(False, "--force", help="Overwrite an existing skill file."),
    ) -> None:
        """Create a new skill from a template."""
        resource_dirs = (
            prompt_for_resource_dirs()
            if interactive
            else selected_resource_dirs(
                with_scripts=with_scripts,
                with_references=with_references,
                with_assets=with_assets,
                with_all=with_all,
            )
        )
        skill_dir = create_skill(
            name=name,
            owners=owner,
            status=status,
            tags=tag,
            template=template,
            description=description,
            resource_dirs=resource_dirs,
            force=force,
        )
        console.print(f"Created skill: {skill_dir}")
        if resource_dirs:
            console.print("Created optional folders:")
            for resource_dir in resource_dirs:
                console.print(f"- {resource_dir}/: {RESOURCE_DIR_GUIDANCE[resource_dir]}")
