from __future__ import annotations

import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ENGINE_ID = "RMS-017"
ENGINE_NAME = "Repository Tracked Artifact Audit Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class TrackedArtifactRecord:
    path: str
    artifact_type: str
    severity: str
    recommendation: str


@dataclass(frozen=True)
class TrackedArtifactAuditResult:
    engine_id: str
    engine_name: str
    engine_version: str
    status: str
    tracked_file_count: int
    artifact_count: int
    warning_count: int
    critical_count: int
    records: List[TrackedArtifactRecord]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "tracked_file_count": self.tracked_file_count,
            "artifact_count": self.artifact_count,
            "warning_count": self.warning_count,
            "critical_count": self.critical_count,
            "records": [asdict(r) for r in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class RepositoryTrackedArtifactAuditEngine:
    def audit(self, root: str | Path = ".") -> TrackedArtifactAuditResult:
        root_path = Path(root).resolve()
        tracked_files = self._tracked_files(root_path)

        records: List[TrackedArtifactRecord] = []

        for rel_path in tracked_files:
            artifact_type = self._artifact_type(rel_path)
            if not artifact_type:
                continue

            severity = self._severity(artifact_type)
            records.append(
                TrackedArtifactRecord(
                    path=rel_path,
                    artifact_type=artifact_type,
                    severity=severity,
                    recommendation=self._recommendation(artifact_type),
                )
            )

        warning_count = sum(1 for r in records if r.severity == "warning")
        critical_count = sum(1 for r in records if r.severity == "critical")
        status = "critical" if critical_count else "warning" if warning_count else "ok"

        return TrackedArtifactAuditResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            status=status,
            tracked_file_count=len(tracked_files),
            artifact_count=len(records),
            warning_count=warning_count,
            critical_count=critical_count,
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
                "uses_git_ls_files": True,
            },
            explanation=(
                f"Audited {len(tracked_files)} tracked file(s). Found {len(records)} tracked artifact(s): "
                f"{warning_count} warning(s), {critical_count} critical. No files were modified."
            ),
        )

    def _tracked_files(self, root: Path) -> List[str]:
        try:
            completed = subprocess.run(
                ["git", "ls-files"],
                cwd=str(root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode == 0:
                return [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        except Exception:
            pass

        return [
            str(path.relative_to(root)).replace("\\", "/")
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(root).parts
        ]

    def _artifact_type(self, path: str) -> str:
        lower = path.lower().replace("\\", "/")
        name = lower.rsplit("/", 1)[-1]

        if name == ".env" or name.endswith(".env"):
            return "tracked_environment"
        if name.endswith((".db", ".sqlite", ".sqlite3")):
            return "tracked_database"
        if lower.startswith("qseries_v2/data/"):
            return "tracked_qseries_data_artifact"
        if lower.startswith("oracle/data/"):
            return "tracked_oracle_data_artifact"
        if lower.startswith("runtime/"):
            return "tracked_runtime_artifact"
        if "/raw/" in lower:
            return "tracked_raw_sample"
        if name.endswith(".log"):
            return "tracked_log"
        if name.endswith(".tmp"):
            return "tracked_temp"
        if name.endswith(".csv"):
            return "tracked_csv"
        if name.endswith(".json") and any(token in name for token in ["state", "memory", "cache", "watchlist", "sample", "history"]):
            return "tracked_runtime_json"
        return ""

    def _severity(self, artifact_type: str) -> str:
        if artifact_type == "tracked_raw_sample":
            return "warning"
        if artifact_type in {
            "tracked_environment",
            "tracked_database",
            "tracked_qseries_data_artifact",
            "tracked_oracle_data_artifact",
            "tracked_runtime_artifact",
            "tracked_log",
            "tracked_temp",
        }:
            return "critical"
        return "warning"

    def _recommendation(self, artifact_type: str) -> str:
        if artifact_type == "tracked_environment":
            return "Environment files must not be tracked; remove from Git tracking in a controlled cleanup commit."
        if artifact_type == "tracked_database":
            return "Move database files to runtime/data and remove from Git tracking in a controlled cleanup commit."
        if artifact_type == "tracked_qseries_data_artifact":
            return "Q Series data artifacts must not be tracked unless explicitly approved as fixtures."
        if artifact_type == "tracked_oracle_data_artifact":
            return "Oracle data artifacts must not be tracked unless explicitly approved as fixtures."
        if artifact_type == "tracked_runtime_artifact":
            return "Runtime artifacts must not be tracked; keep runtime output ignored."
        if artifact_type == "tracked_raw_sample":
            return "Review whether raw samples are fixtures; archive intentional fixtures and remove generated samples."
        if artifact_type == "tracked_runtime_json":
            return "Runtime JSON should not be tracked unless it is an intentional fixture."
        if artifact_type == "tracked_csv":
            return "CSV exports should usually be ignored unless they are documented fixtures."
        if artifact_type == "tracked_log":
            return "Logs should be removed from tracking and ignored."
        if artifact_type == "tracked_temp":
            return "Temporary files should be removed from tracking and deleted after verification."
        return "Review tracked artifact before next cleanup commit."


def audit_repository_tracked_artifacts(root: str | Path = ".") -> TrackedArtifactAuditResult:
    return RepositoryTrackedArtifactAuditEngine().audit(root)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "TrackedArtifactRecord",
    "TrackedArtifactAuditResult",
    "RepositoryTrackedArtifactAuditEngine",
    "audit_repository_tracked_artifacts",
]
