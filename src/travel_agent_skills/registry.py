from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml



@dataclass(frozen=True)
class SkillRegistryEntry:
    path: str
    version: str
    owners: list[str]
    status: str
    tags: list[str] = field(default_factory=list)
    distribution: list[str] = field(default_factory=lambda: ["org-provisioned", "zip", "project-local"])

    def to_dict(self) -> dict[str, Any]:
        """Return a YAML-serializable registry entry."""
        return {
            "path": self.path,
            "version": self.version,
            "owners": self.owners,
            "status": self.status,
            "tags": self.tags,
            "distribution": self.distribution,
        }


def load_registry(registry_path: Path) -> dict[str, Any]:
    """Load registry.yaml, falling back to an empty registry when missing."""
    if not registry_path.exists():
        return {"skills": {}}

    content = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not content:
        return {"skills": {}}
    if "skills" not in content or content["skills"] is None:
        content["skills"] = {}
    return content


def save_registry(registry_path: Path, registry: dict[str, Any]) -> None:
    """Write registry metadata to disk in a stable YAML format."""
    registry_path.write_text(
        yaml.safe_dump(registry, sort_keys=True, allow_unicode=False),
        encoding="utf-8",
    )


def upsert_skill_entry(registry_path: Path, name: str, entry: SkillRegistryEntry) -> None:
    """Insert or replace one skill entry in registry.yaml."""
    registry = load_registry(registry_path)
    registry["skills"][name] = entry.to_dict()
    save_registry(registry_path, registry)


def list_skill_entries(registry_path: Path) -> dict[str, dict[str, Any]]:
    """Return all skill entries from registry.yaml."""
    registry = load_registry(registry_path)
    return registry.get("skills", {})


def get_skill_entry(registry_path: Path, name: str) -> dict[str, Any] | None:
    """Return one skill entry from registry.yaml by name."""
    return list_skill_entries(registry_path).get(name)


def delete_skill_entry(registry_path: Path, name: str) -> bool:
    """Remove one skill entry from registry.yaml. Returns True if it existed."""
    registry = load_registry(registry_path)
    if name not in registry["skills"]:
        return False
    del registry["skills"][name]
    save_registry(registry_path, registry)
    return True
