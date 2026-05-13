from pathlib import Path

import yaml
from typer.testing import CliRunner

from travel_agent_skills.cli import app

runner = CliRunner()


def make_skill(project_root: Path, name: str) -> Path:
    """Create a minimal valid skill and registry entry."""
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill for {name}.\n---\n",
        encoding="utf-8",
    )
    registry_path = project_root / "registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"skills": {}}
    registry["skills"][name] = {
        "path": f"skills/{name}",
        "version": "0.1.0",
        "owners": ["travel-platform"],
        "status": "draft",
        "tags": ["travel"],
    }
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")
    return skill_dir


def make_invalid_skill(project_root: Path, name: str) -> Path:
    """Create a skill with a registry name mismatch to trigger validation failure."""
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\nname: wrong-name\ndescription: Intentionally broken skill.\n---\n",
        encoding="utf-8",
    )
    registry_path = project_root / "registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {"skills": {}}
    registry["skills"][name] = {
        "path": f"skills/{name}",
        "version": "0.1.0",
        "owners": ["travel-platform"],
        "status": "draft",
        "tags": ["travel"],
    }
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")
    return skill_dir


def test_validate_command_passes_for_valid_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    skill_dir = make_skill(tmp_path, "flight-search")

    result = runner.invoke(app, ["validate", str(skill_dir)])

    assert result.exit_code == 0
    assert "PASS" in result.output


def test_validate_command_fails_for_invalid_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    skill_dir = make_invalid_skill(tmp_path, "flight-search")

    result = runner.invoke(app, ["validate", str(skill_dir)])

    assert result.exit_code == 1
    assert "FAIL" in result.output


def test_validate_command_all_passes_when_all_skills_valid(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")
    make_skill(tmp_path, "hotel-search")

    result = runner.invoke(app, ["validate", "--all"])

    assert result.exit_code == 0
    assert result.output.count("PASS") == 2


def test_validate_command_all_fails_when_any_skill_invalid(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")
    make_invalid_skill(tmp_path, "hotel-search")

    result = runner.invoke(app, ["validate", "--all"])

    assert result.exit_code == 1
    assert "PASS" in result.output
    assert "FAIL" in result.output


def test_validate_command_requires_path_or_all(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["validate"])

    assert result.exit_code != 0
