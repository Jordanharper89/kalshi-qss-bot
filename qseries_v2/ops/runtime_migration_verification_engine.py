
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout, validate_runtime_paths
from qseries_v2.ops.runtime_path_integration_audit import run_runtime_path_integration_audit


@dataclass(frozen=True)
class RuntimeMigrationVerificationResult:
    status: str
    generated_at: str
    runtime_root: str
    required_directories: Dict[str, bool]
    required_databases: Dict[str, bool]
    audit_status: str
    audit_finding_count: int
    report_path: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RuntimeMigrationVerificationEngine:
    REQUIRED_DATABASES = {
        "oracle_data_db": RuntimePaths.oracle_data_db,
        "oracle_memory_db": RuntimePaths.oracle_memory_db,
        "oracle_runtime_state_db": RuntimePaths.oracle_runtime_state_db,
        "qseries_history_db": RuntimePaths.qseries_history_db,
    }

    def __init__(self, repo_root: Path | None = None) -> None:
        ensure_runtime_layout()
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.report_path = RuntimePaths.logs_dir() / "runtime_migration_verification_report.json"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def verify(self) -> RuntimeMigrationVerificationResult:
        validation = validate_runtime_paths()
        audit = run_runtime_path_integration_audit(repo_root=self.repo_root)

        required_dirs = {
            name: Path(path).exists() and Path(path).is_dir()
            for name, path in validation.directories.items()
        }

        required_dbs = {
            name: path_factory().exists() and path_factory().is_file()
            for name, path_factory in self.REQUIRED_DATABASES.items()
        }

        status = "ok"

        if not all(required_dirs.values()):
            status = "error"

        if not all(required_dbs.values()):
            status = "error"

        if audit.status != "ok" or audit.findings:
            status = "error"

        result = RuntimeMigrationVerificationResult(
            status=status,
            generated_at=self.now_iso(),
            runtime_root=str(RuntimePaths.runtime_root()),
            required_directories=required_dirs,
            required_databases=required_dbs,
            audit_status=audit.status,
            audit_finding_count=len(audit.findings),
            report_path=str(self.report_path),
        )

        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return result


def run_runtime_migration_verification(repo_root: Path | None = None) -> RuntimeMigrationVerificationResult:
    return RuntimeMigrationVerificationEngine(repo_root=repo_root).verify()


__all__ = [
    "RuntimeMigrationVerificationResult",
    "RuntimeMigrationVerificationEngine",
    "run_runtime_migration_verification",
]
