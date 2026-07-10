
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
