
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from oracle.database import db


def test_ops_012_oracle_database_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        db_path = db.get_db_path()

        assert db_path == RuntimePaths.oracle_data_db()
        assert "qseries_v2/data" not in str(db_path).replace("\\", "/")

        created_path = db.init_oracle_database()
        assert created_path == RuntimePaths.oracle_data_db()
        assert created_path.exists()

        db.execute(
            """
            INSERT OR REPLACE INTO oracle_metadata(key, value)
            VALUES (?, ?)
            """,
            ("runtime_paths", "enabled"),
        )

        row = db.fetch_one(
            """
            SELECT key, value
            FROM oracle_metadata
            WHERE key = ?
            """,
            ("runtime_paths",),
        )

        assert row is not None
        assert row["key"] == "runtime_paths"
        assert row["value"] == "enabled"

        rows = db.fetch_all("SELECT key, value FROM oracle_metadata")
        assert len(rows) == 1

        health = db.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["db_path"] == str(RuntimePaths.oracle_data_db())

        print("[PASS] OPS-012 Oracle Database Runtime Path Migration")
        print(health)

        del rows
        del row
        del health
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_012_oracle_database_runtime_path_migration()
