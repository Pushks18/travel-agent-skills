from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from travel_agent_skills.registry import load_registry
from travel_agent_skills.standards import VALID_SKILL_NAME, VALID_STATUSES

FRONTMATTER_PATTERN = re.compile(r"^---\n(?P<yaml>.*?)\n---\n(?P<body>.*)$", re.DOTALL)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<path>[^)#:]+(?:#[^)]+)?)\)")


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def passed(self) -> bool:
        """Return whether validation completed without errors."""
        return not self.errors


def parse_skill_file(skill_file: Path) -> tuple[dict[str, Any], str, list[str]]:
    """Parse SKILL.md frontmatter and body."""
    if not skill_file.exists():
        return {}, "", [f"Missing SKILL.md: {skill_file}"]

    content = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, "", ["SKILL.md must start with YAML frontmatter delimited by ---"]

    try:
        frontmatter = yaml.safe_load(match.group("yaml")) or {}
    except yaml.YAMLError as exc:
        return {}, "", [f"Invalid YAML frontmatter: {exc}"]

    if not isinstance(frontmatter, dict):
        return {}, "", ["SKILL.md frontmatter must be a YAML mapping"]

    return frontmatter, match.group("body"), []


def validate_frontmatter(skill_dir: Path, frontmatter: dict[str, Any]) -> list[str]:
    """Validate open Agent Skills frontmatter constraints."""
    errors = []
    name = frontmatter.get("name")
    description = frontmatter.get("description")

    if not isinstance(name, str) or not name:
        errors.append("frontmatter.name is required")
    elif len(name) > 64 or not VALID_SKILL_NAME.match(name):
        errors.append("frontmatter.name must be 1-64 characters using lowercase letters, numbers, and hyphens")
    elif name != skill_dir.name:
        errors.append(f"frontmatter.name must match folder name: expected {skill_dir.name}, found {name}")

    if not isinstance(description, str) or not description:
        errors.append("frontmatter.description is required")
    elif len(description) > 1024:
        errors.append("frontmatter.description must be 1024 characters or fewer")

    return errors


def validate_registry_entry(project_root: Path, skill_dir: Path, skill_name: str) -> list[str]:
    """Validate registry.yaml contains required metadata for a skill."""
    registry = load_registry(project_root / "registry.yaml")
    entry = registry.get("skills", {}).get(skill_name)
    if not entry:
        return [f"registry.yaml is missing an entry for {skill_name}"]

    errors = []
    expected_path = str(skill_dir.relative_to(project_root))
    if entry.get("path") != expected_path:
        errors.append(f"registry path must be {expected_path}")

    if not entry.get("version"):
        errors.append("registry version is required")
    if not entry.get("owners"):
        errors.append("registry owners are required")
    if entry.get("status") not in VALID_STATUSES:
        allowed = ", ".join(sorted(VALID_STATUSES))
        errors.append(f"registry status must be one of: {allowed}")
    if not isinstance(entry.get("tags", []), list):
        errors.append("registry tags must be a list")

    return errors


def validate_referenced_files(skill_dir: Path, body: str) -> list[str]:
    """Validate local Markdown links in SKILL.md point to existing files."""
    errors = []
    for match in MARKDOWN_LINK_PATTERN.finditer(body):
        link_path = match.group("path")
        if "://" in link_path or link_path.startswith("#"):
            continue
        target = skill_dir / link_path.split("#", 1)[0]
        if not target.exists():
            errors.append(f"Referenced file does not exist: {link_path}")
    return errors


def validate_skill(skill_dir: Path, project_root: Path | None = None) -> ValidationResult:
    """Validate one skill directory against spec and project registry rules."""
    root = (project_root or Path.cwd()).resolve()
    skill_dir = skill_dir if skill_dir.is_absolute() else root / skill_dir
    skill_dir = skill_dir.resolve()
    skill_file = skill_dir / "SKILL.md"
    frontmatter, body, parse_errors = parse_skill_file(skill_file)
    errors = list(parse_errors)

    if not parse_errors:
        errors.extend(validate_frontmatter(skill_dir, frontmatter))
        skill_name = frontmatter.get("name", skill_dir.name)
        if isinstance(skill_name, str):
            errors.extend(validate_registry_entry(root, skill_dir, skill_name))
        errors.extend(validate_referenced_files(skill_dir, body))

    return ValidationResult(errors=errors, warnings=[])


def discover_skills(project_root: Path) -> list[Path]:
    """Return skill directories under the project skills folder.

    A top-level directory with SKILL.md is a skill. A top-level directory
    WITHOUT one is a suite (e.g. skills/disruption-skill/): each of its
    sub-directories containing SKILL.md is a skill in its own right.
    Directories with neither are skipped.
    """
    skills_dir = project_root / "skills"
    if not skills_dir.exists():
        return []
    discovered: list[Path] = []
    for path in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        if (path / "SKILL.md").exists():
            discovered.append(path)
        else:
            discovered.extend(
                sub for sub in sorted(path.iterdir())
                if sub.is_dir() and (sub / "SKILL.md").exists()
            )
    return discovered
