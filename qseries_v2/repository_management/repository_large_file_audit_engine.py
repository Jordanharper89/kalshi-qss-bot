from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-013"
ENGINE_NAME = "Repository Large File Audit Engine"
ENGINE_VERSION = "1.0.1"


@dataclass(frozen=True)
class LargeFileRecord:
    path: str
    size_bytes: int
    size_mb: float
    severity: str
    recommendation: str


@dataclass(frozen=True)
class LargeFileAuditResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    scanned_files: int
    large_file_count: int
    warning_count: int
    critical_count: int
    records: List[LargeFileRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "scanned_files": self.scanned_files,
            "large_file_count": self.large_file_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "records": [asdict(record) for record in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryLargeFileAuditEngine:
    def audit(
        self,
        root: str | Path = ".",
        warning_mb: float = 50.0,
        critical_mb: float = 95.0,
    ) -> LargeFileAuditResult:
        root_path = Path(root).resolve()
        warning_bytes = int(warning_mb * 1024 * 1024)
        critical_bytes = int(critical_mb * 1024 * 1024)

        records: List[LargeFileRecord] = []
        scanned = 0

        excluded = {
            ".git",
            "venv",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
        }

        for path in sorted(root_path.rglob("*"), key=lambda p: str(p).lower()):
            if not path.is_file():
                continue

            rel = path.relative_to(root_path)
            if any(part in excluded for part in rel.parts):
                continue

            scanned += 1
            size_bytes = path.stat().st_size
            size_mb = round(size_bytes / (1024 * 1024), 4)

            if size_bytes >= critical_bytes:
                records.append(
                    LargeFileRecord(
                        path=str(rel),
                        size_bytes=size_bytes,
                        size_mb=size_mb,
                        severity="critical",
                        recommendation=(
                            "Remove from Git history or move to external storage before future pushes."
                        ),
                    )
                )
            elif size_bytes >= warning_bytes:
                records.append(
                    LargeFileRecord(
                        path=str(rel),
                        size_bytes=size_bytes,
                        size_mb=size_mb,
                        severity="warning",
                        recommendation=(
                            "Do not keep large generated database files in Git long term; "
                            "move to runtime/data and ignore."
                        ),
                    )
                )

        warning = sum(1 for record in records if record.severity == "warning")
        critical = sum(1 for record in records if record.severity == "critical")
        status = "critical" if critical else "warning" if warning else "ok"

        return LargeFileAuditResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            scanned_files=scanned,
            large_file_count=len(records),
            warning_count=warning,
            critical_count=critical,
            records=records,
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "repository_role": "architecture_support",
                "does_not_modify_files": True,
                "does_not_delete_files": True,
                "does_not_move_files": True,
                "audit_only": True,
                "warning_mb": warning_mb,
                "critical_mb": critical_mb,
                "warning_bytes": warning_bytes,
                "critical_bytes": critical_bytes,
            },
            explanation=(
                f"Scanned {scanned} file(s). Found {len(records)} large file(s): "
                f"{warning} warning, {critical} critical. No files were modified."
            ),
        )


def audit_repository_large_files(
    root: str | Path = ".",
    warning_mb: float = 50.0,
    critical_mb: float = 95.0,
) -> LargeFileAuditResult:
    return RepositoryLargeFileAuditEngine().audit(root, warning_mb, critical_mb)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "LargeFileRecord",
    "LargeFileAuditResult",
    "RepositoryLargeFileAuditEngine",
    "audit_repository_large_files",
]
