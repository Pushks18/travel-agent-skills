from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from travel_agent_skills.commands.generate import generate_skill

MOCK_BODY = """\
# Disruption Handling

## Workflow

1. **Confirm required inputs.** Ask for any missing required fields.
2. **Identify the disruption.** Determine the type: cancellation, delay, or diversion.

## Required Inputs

| Input | Notes |
|---|---|
| Booking reference | PNR or confirmation number |

## Optional Inputs

| Input | Default |
|---|---|
| Preferred rebooking date | Earliest available |

## Output

A rebooking confirmation or compensation summary.

## Edge Cases and Quality Checks

- Do not fabricate rebooking options.
- If no alternatives exist, say so clearly.
"""


def _mock_llm(prompt: str, model: str) -> str:
    return MOCK_BODY


def test_generate_creates_skill_file(tmp_path: Path) -> None:
    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        skill_dir = generate_skill(
            name="disruption-handling",
            description="Handle flight disruptions and rebooking.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )

    skill_file = skill_dir / "SKILL.md"
    assert skill_file.exists()
    content = skill_file.read_text()
    assert "name: disruption-handling" in content
    assert "author: travel-platform" in content
    assert "# Disruption Handling" in content
    assert "## Workflow" in content


def test_generate_registers_in_registry(tmp_path: Path) -> None:
    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        generate_skill(
            name="disruption-handling",
            description="Handle flight disruptions.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )

    registry = yaml.safe_load((tmp_path / "registry.yaml").read_text())
    entry = registry["skills"]["disruption-handling"]
    assert entry["version"] == "0.1.0"
    assert entry["owners"] == ["travel-platform"]
    assert entry["status"] == "draft"
    assert entry["path"] == "skills/disruption-handling"


def test_generate_skill_passes_validation(tmp_path: Path) -> None:
    from travel_agent_skills.validation import validate_skill

    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        skill_dir = generate_skill(
            name="disruption-handling",
            description="Handle flight disruptions and rebooking on cancelled flights.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )

    result = validate_skill(skill_dir, project_root=tmp_path)
    assert result.passed, f"Validation failed: {result.errors}"


def test_generate_rejects_invalid_name(tmp_path: Path) -> None:
    import typer

    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        with pytest.raises((typer.BadParameter, SystemExit)):
            generate_skill(
                name="INVALID_NAME",
                description="Bad name test.",
                owners=["travel-platform"],
                project_root=tmp_path,
            )


def test_generate_fails_when_skill_exists(tmp_path: Path) -> None:
    import typer

    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        generate_skill(
            name="disruption-handling",
            description="First.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )
        with pytest.raises(typer.BadParameter, match="already exists"):
            generate_skill(
                name="disruption-handling",
                description="Second.",
                owners=["travel-platform"],
                project_root=tmp_path,
            )


def test_generate_force_overwrites(tmp_path: Path) -> None:
    with patch("travel_agent_skills.commands.generate._call_llm", side_effect=_mock_llm):
        generate_skill(
            name="disruption-handling",
            description="First version.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )
        skill_dir = generate_skill(
            name="disruption-handling",
            description="Overwritten.",
            owners=["travel-platform"],
            force=True,
            project_root=tmp_path,
        )

    assert (skill_dir / "SKILL.md").exists()


def test_generate_missing_api_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import typer

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(typer.BadParameter, match="ANTHROPIC_API_KEY"):
        generate_skill(
            name="disruption-handling",
            description="No key test.",
            owners=["travel-platform"],
            project_root=tmp_path,
        )
