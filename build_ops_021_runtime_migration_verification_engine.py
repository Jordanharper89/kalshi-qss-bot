from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "runtime_migration_verification_engine.py"
TEST = ROOT / "test_ops_021_runtime_migration_verification_engine.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
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
'''

test_code = r'''
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.runtime_migration_verification_engine import (
    RuntimeMigrationVerificationEngine,
    run_runtime_migration_verification,
)


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"sqlite-placeholder")


def install_clean_repo(root: Path):
    files = [
        root / "qseries_v2" / "ops" / "runtime_paths.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
        root / "qseries_v2" / "ops" / "historical_data_store.py",
        root / "qseries_v2" / "ops" / "qseries_runtime.py",
    ]

    for file in files:
        write_text(file, "from qseries_v2.ops.runtime_paths import RuntimePaths\n")


def test_ops_021_runtime_migration_verification_engine():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = Path(tmp_obj.name)

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(tmp / "runtime")

    try:
        repo = tmp / "repo"
        install_clean_repo(repo)

        write_db(RuntimePaths.oracle_data_db())
        write_db(RuntimePaths.oracle_memory_db())
        write_db(RuntimePaths.oracle_runtime_state_db())
        write_db(RuntimePaths.qseries_history_db())

        result = run_runtime_migration_verification(repo_root=repo)

        assert result.status == "ok"
        assert result.ok is True
        assert all(result.required_directories.values())
        assert all(result.required_databases.values())
        assert result.audit_finding_count == 0
        assert Path(result.report_path).exists()

        bad_repo = tmp / "bad_repo"
        install_clean_repo(bad_repo)
        write_text(
            bad_repo / "qseries_v2" / "oracle_intelligence" / "bad_engine.py",
            'DB = "qseries_v2/data/qseries_history.sqlite3"\n',
        )

        bad = RuntimeMigrationVerificationEngine(repo_root=bad_repo).verify()
        assert bad.status == "error"
        assert bad.audit_finding_count >= 1

        print("[PASS] OPS-021 Runtime Migration Verification Engine")
        print(result.to_dict())

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_021_runtime_migration_verification_engine()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "ops" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .runtime_migration_verification_engine import "
    "RuntimeMigrationVerificationResult, RuntimeMigrationVerificationEngine, "
    "run_runtime_migration_verification\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-021 INSTALLER")
print(" Runtime Migration Verification Engine")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-021 installed")
print("")
print("Run:")
print("py test_ops_021_runtime_migration_verification_engine.py")