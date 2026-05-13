from zipfile import ZipFile

import yaml
from typer.testing import CliRunner

from travel_agent_skills.cli import app
from travel_agent_skills.packaging import package_skill

runner = CliRunner()


def test_package_skill_creates_zip_and_release_metadata(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        """---
name: flight-search
description: Search flights.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---
""",
        encoding="utf-8",
    )
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/flight-search",
                        "version": "0.1.0",
                        "owners": ["travel-platform"],
                        "status": "draft",
                        "tags": ["travel"],
                        "distribution": ["zip"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = package_skill("flight-search", project_root=tmp_path)

    assert result.zip_path.exists()
    assert result.release_path.exists()
    with ZipFile(result.zip_path) as archive:
        assert "flight-search/SKILL.md" in archive.namelist()

    release = yaml.safe_load(result.release_path.read_text(encoding="utf-8"))
    assert release["name"] == "flight-search"
    assert release["version"] == "0.1.0"
    assert release["artifact"] == "flight-search.zip"
    assert release["sha256"] == result.checksum


def _make_registry(tmp_path, name: str, extra: dict | None = None) -> None:
    entry = {
        "path": f"skills/{name}",
        "version": "0.1.0",
        "owners": ["travel-platform"],
        "status": "draft",
        "tags": ["travel"],
        "distribution": ["zip"],
    }
    if extra:
        entry.update(extra)
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump({"skills": {name: entry}}), encoding="utf-8"
    )


def test_package_skill_zip_includes_subdirectory_files(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text("---\nname: flight-search\n---\n", encoding="utf-8")
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    refs_dir.joinpath("result-format.md").write_text("# Format", encoding="utf-8")
    _make_registry(tmp_path, "flight-search")

    result = package_skill("flight-search", project_root=tmp_path)

    with ZipFile(result.zip_path) as archive:
        names = archive.namelist()
    assert "flight-search/SKILL.md" in names
    assert "flight-search/references/result-format.md" in names


def test_package_skill_fails_for_unregistered_skill(tmp_path) -> None:
    tmp_path.joinpath("registry.yaml").write_text("skills: {}\n", encoding="utf-8")

    try:
        package_skill("ghost-skill", project_root=tmp_path)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "ghost-skill" in str(exc)


def test_package_skill_fails_when_skill_directory_missing(tmp_path) -> None:
    _make_registry(tmp_path, "flight-search")

    try:
        package_skill("flight-search", project_root=tmp_path)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "flight-search" in str(exc)


def test_package_command_outputs_zip_path_and_checksum(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("COLUMNS", "200")
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\nname: flight-search\ndescription: Search flights.\n---\n", encoding="utf-8"
    )
    _make_registry(tmp_path, "flight-search")

    result = runner.invoke(app, ["package", "flight-search"])

    assert result.exit_code == 0
    assert "flight-search.zip" in result.output
    assert "SHA-256" in result.output


def test_package_command_fails_for_unregistered_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("registry.yaml").write_text("skills: {}\n", encoding="utf-8")

    result = runner.invoke(app, ["package", "ghost-skill"])

    assert result.exit_code != 0
