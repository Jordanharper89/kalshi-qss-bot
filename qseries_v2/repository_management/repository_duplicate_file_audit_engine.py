from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-014"
ENGINE_NAME = "Repository Duplicate File Audit Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class DuplicateFileGroup:
    content_hash: str
    file_count: int
    size_bytes: int
    paths: List[str]
    severity: str
    recommendation: str


@dataclass(frozen=True)
class DuplicateFileAuditResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    scanned_files: int
    duplicate_group_count: int
    duplicate_file_count: int
    duplicate_bytes: int
    groups: List[DuplicateFileGroup]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "scanned_files": self.scanned_files,
            "duplicate_group_count": self.duplicate_group_count,
            "duplicate_file_count": self.duplicate_file_count,
            "duplicate_bytes": self.duplicate_bytes,
            "groups": [asdict(group) for group in self.groups],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryDuplicateFileAuditEngine:
    def audit(self, root: str | Path = ".", include_empty: bool = False) -> DuplicateFileAuditResult:
        root_path = Path(root).resolve()
        excluded = {
            ".git",
            "venv",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        scanned = 0
        buckets: Dict[str, List[Path]] = {}

        for path in sorted(root_path.rglob("*"), key=lambda p: str(p).lower()):
            if not path.is_file():
                continue

            rel = path.relative_to(root_path)
            if any(part in excluded for part in rel.parts):
                continue

            size = path.stat().st_size
            if size == 0 and not include_empty:
                continue

            scanned += 1
            digest = self._sha256(path)
            buckets.setdefault(digest, []).append(path)

        groups: List[DuplicateFileGroup] = []
        duplicate_file_count = 0
        duplicate_bytes = 0

        for digest, paths in buckets.items():
            if len(paths) <= 1:
                continue

            size_bytes = paths[0].stat().st_size
            rel_paths = [str(path.relative_to(root_path)) for path in paths]
            duplicate_file_count += len(paths)
            duplicate_bytes += size_bytes * (len(paths) - 1)

            severity = "warning" if size_bytes >= 1024 * 1024 else "info"
            recommendation = (
                "Review duplicate large files and keep only the canonical copy."
                if severity == "warning"
                else "Review duplicates during cleanup; do not delete automatically."
            )

            groups.append(
                DuplicateFileGroup(
                    content_hash=digest,
                    file_count=len(paths),
                    size_bytes=size_bytes,
                    paths=rel_paths,
                    severity=severity,
                    recommendation=recommendation,
                )
            )

        groups.sort(key=lambda g: (-g.size_bytes, g.paths[0]))
        status = "warning" if any(g.severity == "warning" for g in groups) else "info" if groups else "ok"

        return DuplicateFileAuditResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            scanned_files=scanned,
            duplicate_group_count=len(groups),
            duplicate_file_count=duplicate_file_count,
            duplicate_bytes=duplicate_bytes,
            groups=groups,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "audit_only": True,
                "hash_algorithm": "sha256",
                "include_empty": include_empty,
            },
            explanation=(
                f"Scanned {scanned} file(s). Found {len(groups)} duplicate group(s), "
                f"{duplicate_file_count} duplicate file reference(s), and "
                f"{duplicate_bytes} duplicate byte(s). No files were modified."
            ),
        )

    def _sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()


def audit_repository_duplicate_files(root: str | Path = ".", include_empty: bool = False) -> DuplicateFileAuditResult:
    return RepositoryDuplicateFileAuditEngine().audit(root, include_empty)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "DuplicateFileGroup",
    "DuplicateFileAuditResult",
    "RepositoryDuplicateFileAuditEngine",
    "audit_repository_duplicate_files",
]
