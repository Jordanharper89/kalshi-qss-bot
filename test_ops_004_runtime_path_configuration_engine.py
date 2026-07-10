
from pathlib import Path
import tempfile
import os

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout, validate_runtime_paths


def test_ops_004_runtime_path_configuration_engine():
    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
        os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

        try:
            result = ensure_runtime_layout()

            assert result.ok
            assert result.status == "ok"
            assert Path(result.runtime_root).exists()

            expected_dirs = {
                "runtime",
                "data",
                "raw",
                "logs",
                "cache",
                "state",
                "test-data",
            }

            assert set(result.directories.keys()) == expected_dirs

            for path in result.directories.values():
                assert Path(path).exists()
                assert Path(path).is_dir()

            dbs = result.databases

            assert dbs["oracle_data_db"].endswith("runtime/data/oracle_data.db") or dbs["oracle_data_db"].endswith("runtime\\data\\oracle_data.db")
            assert dbs["oracle_memory_db"].endswith("runtime/data/oracle_memory.sqlite3") or dbs["oracle_memory_db"].endswith("runtime\\data\\oracle_memory.sqlite3")
            assert dbs["oracle_runtime_state_db"].endswith("runtime/data/oracle_runtime_state.sqlite3") or dbs["oracle_runtime_state_db"].endswith("runtime\\data\\oracle_runtime_state.sqlite3")
            assert dbs["qseries_history_db"].endswith("runtime/data/qseries_history.sqlite3") or dbs["qseries_history_db"].endswith("runtime\\data\\qseries_history.sqlite3")

            second = validate_runtime_paths()
            assert second.ok
            assert second.missing_directories == []

            print("[PASS] OPS-004 Runtime Path Configuration Engine")
            print({
                "status": second.status,
                "runtime_root": second.runtime_root,
                "directories": second.directories,
                "databases": second.databases,
            })

        finally:
            if old is None:
                os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
            else:
                os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old


if __name__ == "__main__":
    test_ops_004_runtime_path_configuration_engine()
