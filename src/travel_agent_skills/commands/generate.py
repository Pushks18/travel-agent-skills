from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console

from travel_agent_skills.commands.create import (
    validate_skill_name,
    validate_status,
    title_from_name,
    create_resource_dirs,
)
from travel_agent_skills.registry import SkillRegistryEntry, upsert_skill_entry

console = Console()

_GENERATE_PROMPT = """\
You are writing a SKILL.md body for a travel agent AI system.
The skill name is "{name}". The author describes it as:

  {description}

Write ONLY the markdown body (no YAML frontmatter). Use exactly these sections:

# {title}

## Workflow

Numbered steps. Step 1 must always be: "**Confirm required inputs.** Ask for any missing required fields before proceeding."
Each step must be a concrete agent action. Use **bold** for step labels.

## Required Inputs

A markdown table with columns: Input | Notes

## Optional Inputs

A markdown table with columns: Input | Default

## Output

A short paragraph or bullet list describing the structured response format the agent must produce.

## Edge Cases and Quality Checks

A bullet list of failure cases, guard rails, and quality rules the agent must follow.

Rules:
- Every step, input, and check must be specific to "{name}". Do not use generic placeholder text.
- Never tell the agent to fabricate data, invent results, or guess missing inputs.
- Keep the body under 500 lines.
- Do not include any YAML frontmatter or markdown code fences in your response.
"""


def _call_llm(prompt: str, model: str) -> str:
    try:
        import openai
    except ImportError as exc:
        raise typer.BadParameter(
            "openai package is required for 'skills generate'. "
            "Install it: pip install openai"
        ) from exc

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise typer.BadParameter(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Set it before running 'skills generate'."
        )

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    msg = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.choices[0].message.content.strip()


def _build_frontmatter(name: str, description: str, author: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "license: Apache-2.0\n"
        "metadata:\n"
        f"  author: {author}\n"
        '  version: "0.1.0"\n'
        "---\n"
    )


def generate_skill(
    *,
    name: str,
    description: str,
    owners: list[str],
    model: str = "google/gemini-2.5-flash",
    status: str = "draft",
    tags: list[str] | None = None,
    force: bool = False,
    project_root: Path | None = None,
) -> Path:
    """Draft a SKILL.md via LLM, scaffold the dir, register in registry.yaml."""
    validate_skill_name(name)
    validate_status(status)

    root = project_root or Path.cwd()
    skill_dir = root / "skills" / name

    if skill_dir.exists() and not force:
        raise typer.BadParameter(
            f"Skill already exists: {skill_dir}. Use --force to overwrite."
        )

    prompt = _GENERATE_PROMPT.format(
        name=name,
        title=title_from_name(name),
        description=description,
    )

    console.print(f"[dim]Generating {name} body via {model}…[/dim]")
    body = _call_llm(prompt, model)

    frontmatter = _build_frontmatter(name, description, owners[0])
    skill_content = f"{frontmatter}\n{body}\n"

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists() and not force:
        raise typer.BadParameter(f"SKILL.md already exists: {skill_file}")
    skill_file.write_text(skill_content, encoding="utf-8")

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
    @app.command()
    def generate(
        name: str = typer.Argument(..., help="Skill name in lowercase hyphen-case."),
        description: str = typer.Option(..., "--description", "-d", help="Plain-English description of what the skill does and when to use it."),
        owner: list[str] = typer.Option(..., "--owner", "-o", help="Owning team. Can be repeated."),
        model: str = typer.Option("google/gemini-2.5-flash", help="OpenRouter model string to use for drafting."),
        status: str = typer.Option("draft", help="Skill lifecycle status."),
        tag: list[str] = typer.Option(None, "--tag", "-t", help="Discovery tag. Can be repeated."),
        force: bool = typer.Option(False, "--force", help="Overwrite an existing skill."),
    ) -> None:
        """Draft a new skill using an LLM. Requires ANTHROPIC_API_KEY."""
        skill_dir = generate_skill(
            name=name,
            description=description,
            owners=owner,
            model=model,
            status=status,
            tags=tag or None,
            force=force,
        )
        console.print(f"[green]Generated skill:[/green] {skill_dir}")
        console.print("[dim]Review SKILL.md before opening a PR — the eval gate will run on merge.[/dim]")
