from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import yaml

from travel_agent_skills.registry import get_skill_entry


@dataclass(frozen=True)
class PackageResult:
    skill_name: str
    version: str
    zip_path: Path
    release_path: Path
    checksum: str


def sha256_file(path: Path) -> str:
    """Calculate the SHA-256 checksum for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_skill_zip(skill_dir: Path, zip_path: Path) -> None:
    """Write a Claude-compatible skill ZIP with the skill folder at the root."""
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(skill_dir.parent))


def write_release_metadata(
    *,
    release_path: Path,
    skill_name: str,
    entry: dict,
    zip_path: Path,
    checksum: str,
) -> None:
    """Write release metadata beside the packaged ZIP."""
    release = {
        "name": skill_name,
        "version": entry.get("version"),
        "owners": entry.get("owners", []),
        "status": entry.get("status"),
        "tags": entry.get("tags", []),
        "distribution": entry.get("distribution", []),
        "artifact": zip_path.name,
        "sha256": checksum,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    release_path.write_text(yaml.safe_dump(release, sort_keys=True), encoding="utf-8")


def package_skill(skill_name: str, project_root: Path | None = None) -> PackageResult:
    """Package one registered skill into a ZIP and release metadata file."""
    root = (project_root or Path.cwd()).resolve()
    registry_path = root / "registry.yaml"
    entry = get_skill_entry(registry_path, skill_name)
    if entry is None:
        raise ValueError(f"Skill not found in registry.yaml: {skill_name}")

    skill_dir = root / entry["path"]
    if not skill_dir.exists():
        raise ValueError(f"Skill directory does not exist: {skill_dir}")

    version = str(entry.get("version"))
    release_dir = root / "releases" / skill_name / version
    release_dir.mkdir(parents=True, exist_ok=True)

    zip_path = release_dir / f"{skill_name}.zip"
    release_path = release_dir / "release.yaml"

    write_skill_zip(skill_dir, zip_path)
    checksum = sha256_file(zip_path)
    write_release_metadata(
        release_path=release_path,
        skill_name=skill_name,
        entry=entry,
        zip_path=zip_path,
        checksum=checksum,
    )

    return PackageResult(
        skill_name=skill_name,
        version=version,
        zip_path=zip_path,
        release_path=release_path,
        checksum=checksum,
    )

