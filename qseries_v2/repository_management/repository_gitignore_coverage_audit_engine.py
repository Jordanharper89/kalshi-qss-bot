from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-016"
ENGINE_NAME = "Repository Gitignore Coverage Audit Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class GitignoreCoverageRecord:
    pattern: str
    present: bool
    severity: str
    recommendation: str


@dataclass(frozen=True)
class GitignoreCoverageAuditResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    required_count: int
    present_count: int
    missing_count: int
    records: List[GitignoreCoverageRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "required_count": self.required_count,
            "present_count": self.present_count,
            "missing_count": self.missing_count,
            "records": [asdict(r) for r in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryGitignoreCoverageAuditEngine:
    def audit(self, root: str | Path = ".") -> GitignoreCoverageAuditResult:
        root_path = Path(root).resolve()
        gitignore = root_path / ".gitignore"

        required = [
            ".env",
            "*.env",
            "venv/",
            ".venv/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            "runtime/",
            "*.log",
            "*.tmp",
            "*.cache",
            "*.csv",
            "*.bak*",
            "*_backup*",
            "oracle_*.json",
            "*_log.csv",
            "qseries_v2/data/",
            "*.sqlite3",
            "*.db",
        ]

        text = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""

        records: List[GitignoreCoverageRecord] = []
        for pattern in required:
            present = pattern in text
            records.append(
                GitignoreCoverageRecord(
                    pattern=pattern,
                    present=present,
                    severity="ok" if present else "warning",
                    recommendation=(
                        "Pattern present."
                        if present
                        else f"Add '{pattern}' to .gitignore before future commits if generated locally."
                    ),
                )
            )

        present_count = sum(1 for r in records if r.present)
        missing_count = len(records) - present_count
        status = "ok" if missing_count == 0 else "warning"

        return GitignoreCoverageAuditResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            required_count=len(required),
            present_count=present_count,
            missing_count=missing_count,
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
                "gitignore_path": str(gitignore),
            },
            explanation=(
                f"Audited .gitignore coverage for {len(required)} required pattern(s). "
                f"Present={present_count}, missing={missing_count}. No files were modified."
            ),
        )


def audit_repository_gitignore_coverage(root: str | Path = ".") -> GitignoreCoverageAuditResult:
    return RepositoryGitignoreCoverageAuditEngine().audit(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "GitignoreCoverageRecord",
    "GitignoreCoverageAuditResult",
    "RepositoryGitignoreCoverageAuditEngine",
    "audit_repository_gitignore_coverage",
]
