import yaml

from travel_agent_skills.registry import get_skill_entry, list_skill_entries


def test_list_skill_entries(tmp_path) -> None:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/flight-search",
                        "version": "0.1.0",
                        "owners": ["travel-platform"],
                        "status": "draft",
                        "tags": ["travel"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    entries = list_skill_entries(registry_path)

    assert "flight-search" in entries
    assert entries["flight-search"]["version"] == "0.1.0"


def test_get_skill_entry_returns_none_for_missing_skill(tmp_path) -> None:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("skills: {}\n", encoding="utf-8")

    assert get_skill_entry(registry_path, "missing-skill") is None

