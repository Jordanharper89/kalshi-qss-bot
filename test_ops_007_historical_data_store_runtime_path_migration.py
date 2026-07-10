
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.historical_data_store import (
    HistoricalDataRecord,
    HistoricalDataStore,
    create_historical_data_store,
    historical_data_store,
)


def test_ops_007_historical_data_store_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        store = create_historical_data_store()

        assert isinstance(store, HistoricalDataStore)
        assert historical_data_store is create_historical_data_store
        assert store.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(store.db_path).replace("\\", "/")

        rec1 = store.append_event(
            source="oracle",
            market_id="KXTEST-001",
            event_type="snapshot",
            payload={"price": 42, "liquidity": 1000},
        )

        assert isinstance(rec1, HistoricalDataRecord)
        assert rec1.source == "oracle"
        assert rec1.market_id == "KXTEST-001"
        assert rec1.event_type == "snapshot"
        assert rec1.payload["price"] == 42

        rec2 = store.record(
            source="adapter",
            market_id="KXTEST-001",
            event_type="book_update",
            payload={"bid": 41, "ask": 43},
        )

        assert rec2.source == "adapter"
        assert rec2.event_type == "book_update"

        store.append_event(
            source="oracle",
            market_id="KXTEST-002",
            event_type="snapshot",
            payload={"price": 55},
        )

        assert store.count() == 3
        assert store.count(market_id="KXTEST-001") == 2
        assert store.count(source="oracle") == 2
        assert store.count(event_type="snapshot") == 2

        market_events = store.list_events(market_id="KXTEST-001", limit=10)
        assert len(market_events) == 2

        latest = store.latest_for_market("KXTEST-001")
        assert latest is not None
        assert latest.market_id == "KXTEST-001"

        assert store.sources() == ["adapter", "oracle"]
        assert store.event_types() == ["book_update", "snapshot"]

        health = store.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["record_count"] == 3

        cleared = store.clear()
        assert cleared == 3
        assert store.count() == 0

        print("[PASS] OPS-007 Historical Data Store Runtime Path Migration")
        print(health)

        del market_events
        del latest
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
    test_ops_007_historical_data_store_runtime_path_migration()
