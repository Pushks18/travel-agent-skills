from pathlib import Path

import yaml

from travel_agent_skills.validation import validate_skill


def write_skill(project_root: Path, name: str, body: str = "") -> Path:
    """Create a minimal skill folder for validation tests."""
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        f"""---
name: {name}
description: Test skill for {name}.
license: Apache-2.0
metadata:
  author: travel-platform
  version: "0.1.0"
---

{body}
""",
        encoding="utf-8",
    )
    return skill_dir


def write_registry(project_root: Path, name: str) -> None:
    """Create a registry entry for validation tests."""
    project_root.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    name: {
                        "path": f"skills/{name}",
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


def test_validate_skill_passes_for_valid_skill(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert result.passed
    assert result.errors == []


def test_validate_skill_rejects_name_mismatch(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    skill_dir.joinpath("SKILL.md").write_text(
        """---
name: hotel-search
description: Test skill.
---
""",
        encoding="utf-8",
    )
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("must match folder name" in error for error in result.errors)


def test_validate_skill_requires_registry_entry(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("registry.yaml is missing" in error for error in result.errors)


def test_validate_skill_checks_referenced_files(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search", body="See [format](references/result-format.md).")
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("Referenced file does not exist" in error for error in result.errors)


def test_validate_skill_passes_with_existing_referenced_file(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search", body="See [format](references/result-format.md).")
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "result-format.md").write_text("# Format", encoding="utf-8")
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert result.passed
    assert result.errors == []


def test_validate_skill_fails_for_missing_skill_file(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("Missing SKILL.md" in error for error in result.errors)


def test_validate_skill_fails_for_invalid_frontmatter_yaml(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text("---\n: : invalid yaml\n---\n", encoding="utf-8")
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("frontmatter" in error.lower() or "yaml" in error.lower() for error in result.errors)


def test_validate_skill_fails_for_missing_name(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\ndescription: A skill without a name.\n---\n", encoding="utf-8"
    )
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("name" in error for error in result.errors)


def test_validate_skill_fails_for_invalid_name_format(tmp_path) -> None:
    for invalid_name in ("Flight-Search", "-flight", "flight-", "flight--search"):
        skill_dir = tmp_path / "skills" / invalid_name
        skill_dir.mkdir(parents=True)
        skill_dir.joinpath("SKILL.md").write_text(
            f"---\nname: {invalid_name}\ndescription: A skill.\n---\n", encoding="utf-8"
        )

        result = validate_skill(skill_dir, project_root=tmp_path)

        assert not result.passed, f"Expected failure for name: {invalid_name}"
        assert any("name" in error for error in result.errors), f"No name error for: {invalid_name}"


def test_validate_skill_fails_for_missing_description(tmp_path) -> None:
    skill_dir = tmp_path / "skills" / "flight-search"
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text(
        "---\nname: flight-search\n---\n", encoding="utf-8"
    )
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("description" in error for error in result.errors)


def test_validate_skill_fails_for_description_too_long(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search", body="")
    skill_dir.joinpath("SKILL.md").write_text(
        f"---\nname: flight-search\ndescription: {'x' * 1025}\n---\n", encoding="utf-8"
    )
    write_registry(tmp_path, "flight-search")

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("description" in error for error in result.errors)


def test_validate_skill_fails_for_registry_path_mismatch(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/wrong-path",
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

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("registry path" in error for error in result.errors)


def test_validate_skill_fails_for_missing_registry_version(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/flight-search",
                        "owners": ["travel-platform"],
                        "status": "draft",
                        "tags": ["travel"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("version" in error for error in result.errors)


def test_validate_skill_fails_for_missing_registry_owners(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/flight-search",
                        "version": "0.1.0",
                        "owners": [],
                        "status": "draft",
                        "tags": ["travel"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("owners" in error for error in result.errors)


def test_validate_skill_fails_for_invalid_registry_status(tmp_path) -> None:
    skill_dir = write_skill(tmp_path, "flight-search")
    tmp_path.joinpath("registry.yaml").write_text(
        yaml.safe_dump(
            {
                "skills": {
                    "flight-search": {
                        "path": "skills/flight-search",
                        "version": "0.1.0",
                        "owners": ["travel-platform"],
                        "status": "unknown-status",
                        "tags": ["travel"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = validate_skill(skill_dir, project_root=tmp_path)

    assert not result.passed
    assert any("status" in error for error in result.errors)


# ── discover_skills: nested suite support ────────────────────────────────────

def _mk_skill(dir_path, name):
    dir_path.mkdir(parents=True)
    (dir_path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: d\n---\n# {name}\n", encoding="utf-8"
    )


def test_discover_skills_flat_and_suite(tmp_path):
    from travel_agent_skills.validation import discover_skills

    _mk_skill(tmp_path / "skills" / "flight-search", "flight-search")
    # suite: parent has no SKILL.md, children do
    _mk_skill(tmp_path / "skills" / "disruption-skill" / "flight-delay-detection",
              "flight-delay-detection")
    _mk_skill(tmp_path / "skills" / "disruption-skill" / "gate-terminal-change",
              "gate-terminal-change")
    # junk dir with neither SKILL.md nor sub-skills is skipped
    (tmp_path / "skills" / "scratch" / "notes").mkdir(parents=True)

    found = {p.name for p in discover_skills(tmp_path)}
    assert found == {"flight-search", "flight-delay-detection", "gate-terminal-change"}


def test_discover_skills_suite_parent_not_returned(tmp_path):
    from travel_agent_skills.validation import discover_skills

    _mk_skill(tmp_path / "skills" / "disruption-skill" / "car-disruption-detection",
              "car-disruption-detection")
    names = [p.name for p in discover_skills(tmp_path)]
    assert "disruption-skill" not in names
