import yaml
from typer.testing import CliRunner

from travel_agent_skills.cli import app
from travel_agent_skills.registry import delete_skill_entry

runner = CliRunner()


def make_skill(project_root, name: str) -> None:
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill.\n---\n", encoding="utf-8"
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


def test_delete_removes_skill_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")

    result = runner.invoke(app, ["delete", "flight-search", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / "skills" / "flight-search").exists()


def test_delete_removes_skill_from_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")

    runner.invoke(app, ["delete", "flight-search", "--yes"])

    registry = yaml.safe_load((tmp_path / "registry.yaml").read_text(encoding="utf-8"))
    assert "flight-search" not in registry["skills"]


def test_delete_prints_confirmation(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")

    result = runner.invoke(app, ["delete", "flight-search", "--yes"])

    assert "flight-search" in result.output


def test_delete_fails_for_unregistered_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "registry.yaml").write_text("skills: {}\n", encoding="utf-8")

    result = runner.invoke(app, ["delete", "ghost-skill", "--yes"])

    assert result.exit_code != 0
    assert "ghost-skill" in result.output


def test_delete_aborts_when_not_confirmed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")

    # 'n' as input to the confirmation prompt
    result = runner.invoke(app, ["delete", "flight-search"], input="n\n")

    assert result.exit_code == 0
    assert (tmp_path / "skills" / "flight-search").exists()
    registry = yaml.safe_load((tmp_path / "registry.yaml").read_text(encoding="utf-8"))
    assert "flight-search" in registry["skills"]


def test_delete_succeeds_when_skill_dir_already_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")
    (tmp_path / "skills" / "flight-search").rename(tmp_path / "skills" / "flight-search-backup")

    result = runner.invoke(app, ["delete", "flight-search", "--yes"])

    assert result.exit_code == 0
    registry = yaml.safe_load((tmp_path / "registry.yaml").read_text(encoding="utf-8"))
    assert "flight-search" not in registry["skills"]


def test_delete_entry_returns_false_for_missing_skill(tmp_path) -> None:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("skills: {}\n", encoding="utf-8")

    removed = delete_skill_entry(registry_path, "ghost-skill")

    assert removed is False


def test_delete_leaves_other_skills_intact(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    make_skill(tmp_path, "flight-search")
    make_skill(tmp_path, "hotel-search")

    runner.invoke(app, ["delete", "flight-search", "--yes"])

    registry = yaml.safe_load((tmp_path / "registry.yaml").read_text(encoding="utf-8"))
    assert "hotel-search" in registry["skills"]
    assert (tmp_path / "skills" / "hotel-search").exists()
