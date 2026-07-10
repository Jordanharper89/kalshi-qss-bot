
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.oracle_runtime_state_store import (
    OracleRuntimeStateRecord,
    OracleRuntimeStateStore,
    create_oracle_runtime_state_store,
    oracle_runtime_state_store,
)


def test_ops_006_oracle_runtime_state_store_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        store = create_oracle_runtime_state_store()

        assert isinstance(store, OracleRuntimeStateStore)
        assert oracle_runtime_state_store is create_oracle_runtime_state_store
        assert store.db_path == RuntimePaths.oracle_runtime_state_db()
        assert "qseries_v2/data" not in str(store.db_path).replace("\\", "/")

        rec1 = store.set_state(
            namespace="runtime",
            key="scheduler",
            value={"status": "running", "jobs": 5},
        )

        assert isinstance(rec1, OracleRuntimeStateRecord)
        assert rec1.key == "scheduler"
        assert rec1.namespace == "runtime"
        assert rec1.value["status"] == "running"

        loaded = store.get_state(namespace="runtime", key="scheduler")
        assert loaded is not None
        assert loaded.value["jobs"] == 5

        rec2 = store.upsert(
            namespace="runtime",
            key="scheduler",
            value={"status": "healthy", "jobs": 6},
        )

        assert rec2.created_at == rec1.created_at
        assert rec2.updated_at >= rec1.updated_at

        loaded2 = store.get(namespace="runtime", key="scheduler")
        assert loaded2 is not None
        assert loaded2.value["status"] == "healthy"
        assert loaded2.value["jobs"] == 6

        store.set_state(namespace="oracle", key="last_scan", value={"ok": True})
        store.set_state(namespace="runtime", key="watchdog", value={"checks": 3})

        assert store.count() == 3
        assert store.count("runtime") == 2
        assert store.namespaces() == ["oracle", "runtime"]

        listed = store.list_namespace("runtime")
        listed_keys = sorted([item.key for item in listed])
        assert listed_keys == ["scheduler", "watchdog"]

        health = store.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["record_count"] == 3

        assert store.delete_state(namespace="runtime", key="watchdog") is True
        assert store.get_state(namespace="runtime", key="watchdog") is None
        assert store.count("runtime") == 1

        cleared = store.clear_namespace("runtime")
        assert cleared == 1
        assert store.count("runtime") == 0
        assert store.count() == 1

        print("[PASS] OPS-006 Oracle Runtime State Store Runtime Path Migration")
        print(health)

        del listed
        del loaded
        del loaded2
        del rec1
        del rec2
        del health
        del store
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_006_oracle_runtime_state_store_runtime_path_migration()
