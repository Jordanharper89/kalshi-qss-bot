
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.physical_runtime_database_migration import (
    PhysicalRuntimeDatabaseMigration,
    run_physical_runtime_database_migration,
)


def write(path: Path, data: bytes = b"db"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def install_clean_repo(root: Path):
    files = [
        root / "qseries_v2" / "ops" / "runtime_paths.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py",
        root / "qseries_v2" / "oracle_intelligence" / "oracle_runtime_state_store.py",
        root / "qseries_v2" / "ops" / "historical_data_store.py",
        root / "qseries_v2" / "ops" / "qseries_runtime.py",
    ]

    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("from qseries_v2.ops.runtime_paths import RuntimePaths\n", encoding="utf-8")


def test_ops_020_physical_runtime_database_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = Path(tmp_obj.name)

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(tmp / "runtime")

    try:
        repo = tmp / "repo"
        install_clean_repo(repo)

        write(repo / "oracle" / "data" / "oracle_data.db")
        write(repo / "qseries_v2" / "data" / "oracle_memory.sqlite3")
        write(repo / "qseries_v2" / "data" / "oracle_runtime_state.sqlite3")
        write(repo / "qseries_v2" / "data" / "qseries_history.sqlite3")
        write(repo / "qseries_v2" / "data" / "test_oracle_memory.sqlite3")

        dry = run_physical_runtime_database_migration(
            repo_root=repo,
            dry_run=True,
            require_gate=True,
        )

        assert dry.status == "planned"
        assert dry.dry_run is True
        assert len(dry.actions) == 5
        assert all(action.status == "planned" for action in dry.actions)

        assert (repo / "oracle" / "data" / "oracle_data.db").exists()
        assert not (RuntimePaths.data_dir() / "oracle_data.db").exists()

        live = PhysicalRuntimeDatabaseMigration(repo_root=repo).run(
            dry_run=False,
            require_gate=True,
        )

        assert live.status == "ok"
        assert any(action.status == "moved" for action in live.actions)

        assert not (repo / "oracle" / "data" / "oracle_data.db").exists()
        assert (RuntimePaths.data_dir() / "oracle_data.db").exists()
        assert (RuntimePaths.data_dir() / "oracle_memory.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "oracle_runtime_state.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "qseries_history.sqlite3").exists()
        assert (RuntimePaths.data_dir() / "test_oracle_memory.sqlite3").exists()

        bad_repo = tmp / "bad_repo"
        install_clean_repo(bad_repo)
        write(bad_repo / "qseries_v2" / "data" / "qseries_history.sqlite3")
        bad_file = bad_repo / "qseries_v2" / "oracle_intelligence" / "bad_engine.py"
        bad_file.parent.mkdir(parents=True, exist_ok=True)
        bad_file.write_text('DB = "qseries_v2/data/qseries_history.sqlite3"\n', encoding="utf-8")

        blocked = run_physical_runtime_database_migration(
            repo_root=bad_repo,
            dry_run=False,
            require_gate=True,
        )

        assert blocked.status == "blocked"
        assert blocked.blocked_reasons
        assert all(action.status == "blocked" for action in blocked.actions)
        assert (bad_repo / "qseries_v2" / "data" / "qseries_history.sqlite3").exists()

        print("[PASS] OPS-020 Physical Runtime Database Migration")
        print({
            "dry_status": dry.status,
            "live_status": live.status,
            "blocked_status": blocked.status,
            "runtime_data_dir": str(RuntimePaths.data_dir()),
        })

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_020_physical_runtime_database_migration()
