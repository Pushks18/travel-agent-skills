import yaml
from typer.testing import CliRunner

from travel_agent_skills.cli import app

runner = CliRunner()


def write_registry(tmp_path, entries: dict) -> None:
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump({"skills": entries}), encoding="utf-8"
    )


def test_list_shows_registered_skills(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("COLUMNS", "200")
    write_registry(tmp_path, {
        "flight-search": {
            "path": "skills/flight-search",
            "version": "0.1.0",
            "owners": ["travel-platform"],
            "status": "draft",
            "tags": ["travel", "flight"],
        }
    })

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "flight-search" in result.output
    assert "0.1.0" in result.output
    assert "draft" in result.output


def test_list_shows_multiple_skills(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_registry(tmp_path, {
        "flight-search": {
            "path": "skills/flight-search",
            "version": "0.1.0",
            "owners": ["travel-platform"],
            "status": "draft",
            "tags": ["travel"],
        },
        "hotel-search": {
            "path": "skills/hotel-search",
            "version": "0.2.0",
            "owners": ["travel-platform"],
            "status": "stable",
            "tags": ["travel"],
        },
    })

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "flight-search" in result.output
    assert "hotel-search" in result.output
    assert "stable" in result.output


def test_list_with_empty_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_registry(tmp_path, {})

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0


def test_info_shows_skill_details(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_registry(tmp_path, {
        "flight-search": {
            "path": "skills/flight-search",
            "version": "0.1.0",
            "owners": ["travel-platform"],
            "status": "draft",
            "tags": ["travel", "flight"],
            "distribution": ["zip", "org-provisioned"],
        }
    })

    result = runner.invoke(app, ["info", "flight-search"])

    assert result.exit_code == 0
    assert "flight-search" in result.output
    assert "0.1.0" in result.output
    assert "travel-platform" in result.output
    assert "draft" in result.output
    assert "zip" in result.output


def test_info_fails_for_unknown_skill(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    write_registry(tmp_path, {})

    result = runner.invoke(app, ["info", "does-not-exist"])

    assert result.exit_code != 0
