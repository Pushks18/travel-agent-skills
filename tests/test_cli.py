from pathlib import Path

import yaml
from typer.testing import CliRunner

from travel_agent_skills.cli import app
from travel_agent_skills.commands.create import RESOURCE_DIR_GUIDANCE, create_skill, selected_resource_dirs

runner = CliRunner()

MINIMAL_TEMPLATE = """\
---
name: {{ name }}
description: {{ description }}
license: {{ license }}
metadata:
  author: {{ author }}
  version: "{{ version }}"
---

# {{ title }}
"""


def make_template(project_root: Path) -> None:
    template_dir = project_root / "templates" / "basic-skill"
    template_dir.mkdir(parents=True)
    template_dir.joinpath("SKILL.md.j2").write_text(MINIMAL_TEMPLATE, encoding="utf-8")


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "travel-agent-skills 0.1.0" in result.output


def test_create_skill(tmp_path) -> None:
    make_template(tmp_path)

    skill_dir = create_skill(
        name="flight-search",
        owners=["travel-platform"],
        project_root=tmp_path,
    )

    skill_file = skill_dir / "SKILL.md"
    skill_content = skill_file.read_text(encoding="utf-8")
    assert skill_file.exists()
    assert "name: flight-search" in skill_content
    assert "license: Apache-2.0" in skill_content
    assert "author: travel-platform" in skill_content
    assert not (skill_dir / "references").exists()
    assert not (skill_dir / "scripts").exists()
    assert not (skill_dir / "assets").exists()

    registry = yaml.safe_load(tmp_path.joinpath("registry.yaml").read_text(encoding="utf-8"))
    assert registry["skills"]["flight-search"]["version"] == "0.1.0"
    assert registry["skills"]["flight-search"]["owners"] == ["travel-platform"]
    assert registry["skills"]["flight-search"]["status"] == "draft"


def test_create_skill_with_custom_tags(tmp_path) -> None:
    make_template(tmp_path)

    create_skill(
        name="flight-search",
        owners=["travel-platform"],
        tags=["airfare", "booking"],
        project_root=tmp_path,
    )

    registry = yaml.safe_load(tmp_path.joinpath("registry.yaml").read_text(encoding="utf-8"))
    assert registry["skills"]["flight-search"]["tags"] == ["airfare", "booking"]


def test_create_skill_with_optional_folders(tmp_path) -> None:
    make_template(tmp_path)

    skill_dir = create_skill(
        name="hotel-search",
        owners=["travel-platform"],
        resource_dirs=["references", "assets"],
        project_root=tmp_path,
    )

    assert (skill_dir / "references" / ".gitkeep").exists()
    assert (skill_dir / "assets" / ".gitkeep").exists()
    assert not (skill_dir / "scripts").exists()


def test_selected_resource_dirs_with_all() -> None:
    assert selected_resource_dirs(with_all=True) == ["scripts", "references", "assets"]


def test_resource_dir_guidance_mentions_all_optional_dirs() -> None:
    assert set(RESOURCE_DIR_GUIDANCE) == {"scripts", "references", "assets"}


def test_create_skill_rejects_invalid_name(tmp_path) -> None:
    result = runner.invoke(
        app,
        ["create", "Flight Search", "--owner", "travel-platform"],
        catch_exceptions=False,
    )

    assert result.exit_code != 0


def test_create_skill_fails_when_skill_already_exists(tmp_path) -> None:
    make_template(tmp_path)
    create_skill(name="flight-search", owners=["travel-platform"], project_root=tmp_path)

    try:
        create_skill(name="flight-search", owners=["travel-platform"], project_root=tmp_path)
        assert False, "Expected BadParameter for duplicate skill"
    except Exception as exc:
        assert "already exists" in str(exc)


def test_create_skill_force_overwrites_existing_skill(tmp_path) -> None:
    make_template(tmp_path)
    create_skill(name="flight-search", owners=["travel-platform"], project_root=tmp_path)

    skill_dir = create_skill(
        name="flight-search",
        owners=["travel-platform"],
        force=True,
        project_root=tmp_path,
    )

    assert (skill_dir / "SKILL.md").exists()


def test_create_skill_uses_custom_description(tmp_path) -> None:
    make_template(tmp_path)
    custom = "Book and compare hotels worldwide. Use when users ask for accommodation."

    skill_dir = create_skill(
        name="hotel-search",
        owners=["travel-platform"],
        description=custom,
        project_root=tmp_path,
    )

    content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert custom in content
