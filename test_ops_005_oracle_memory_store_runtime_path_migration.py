
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import (
    OraclePersistentMemoryStore,
    create_oracle_persistent_memory_store,
    oracle_persistent_memory_store,
)


def test_ops_005_oracle_memory_store_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        store = create_oracle_persistent_memory_store()

        assert isinstance(store, OraclePersistentMemoryStore)
        assert oracle_persistent_memory_store is create_oracle_persistent_memory_store
        assert store.db_path == RuntimePaths.oracle_memory_db()
        assert "qseries_v2/data" not in str(store.db_path).replace("\\", "/")

        rec1 = store.upsert(
            namespace="signals",
            key="market:test",
            value={"edge": 0.14, "grade": "A"},
        )

        assert rec1.key == "market:test"
        assert rec1.namespace == "signals"
        assert rec1.value["grade"] == "A"

        loaded = store.get(namespace="signals", key="market:test")
        assert loaded is not None
        assert loaded.value["edge"] == 0.14

        rec2 = store.upsert(
            namespace="signals",
            key="market:test",
            value={"edge": 0.19, "grade": "A+"},
        )

        assert rec2.created_at == rec1.created_at
        assert rec2.updated_at >= rec1.updated_at

        loaded2 = store.get(namespace="signals", key="market:test")
        assert loaded2 is not None
        assert loaded2.value["grade"] == "A+"

        store.upsert(namespace="runtime", key="heartbeat", value={"ok": True})

        assert store.count() == 2
        assert store.count("signals") == 1
        assert store.namespaces() == ["runtime", "signals"]

        listed = store.list_namespace("signals")
        assert len(listed) == 1
        assert listed[0].key == "market:test"

        health = store.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["record_count"] == 2

        assert store.delete(namespace="signals", key="market:test") is True
        assert store.get(namespace="signals", key="market:test") is None
        assert store.count() == 1

        print("[PASS] OPS-005 Oracle Memory Store Runtime Path Migration")
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
    test_ops_005_oracle_memory_store_runtime_path_migration()
