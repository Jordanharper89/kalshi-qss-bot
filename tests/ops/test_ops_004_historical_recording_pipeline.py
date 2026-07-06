"""
Test OPS-004 Historical Recording Pipeline.
"""

import tempfile
from pathlib import Path

from qseries_v2.ops.historical_data_store import build_historical_data_store
from qseries_v2.ops.historical_recording_pipeline import build_historical_recording_pipeline


class FakeMarketCache:
    def __init__(self):
        self.markets = [
            {
                "ticker": "SERIES-EVENT-001",
                "event_ticker": "EVENT",
                "series_ticker": "SERIES",
                "category": "Test",
                "title": "Market 1",
                "status": "open",
                "yes_bid": 44,
                "yes_ask": 46,
                "no_bid": 54,
                "no_ask": 56,
                "last_price": 45,
                "volume": 100,
                "open_interest": 200,
                "liquidity": 300,
            }
        ]

    def get_all_markets(self):
        return [dict(m) for m in self.markets]


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_004():
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "test_pipeline.sqlite3")

    bus = FakeEventBus()
    cache = FakeMarketCache()
    store = build_historical_data_store(db_path=db_path, event_bus=bus)

    pipeline = build_historical_recording_pipeline(
        market_cache=cache,
        historical_store=store,
        event_bus=bus,
        skip_duplicates=True,
    )

    first = pipeline.record_current_snapshot(metadata={"test": 1})
    assert first["status"] == "ok"
    assert first["inserted_count"] == 1

    duplicate = pipeline.record_current_snapshot(metadata={"test": 2})
    assert duplicate["status"] == "skipped_duplicate"

    cache.markets[0]["yes_bid"] = 45
    second = pipeline.record_current_snapshot(metadata={"test": 3})
    assert second["status"] == "ok"
    assert second["inserted_count"] == 1

    diag = pipeline.diagnostics()
    store_diag = store.diagnostics()

    assert diag["record_count"] == 2
    assert diag["market_rows_recorded"] == 2
    assert diag["skipped_duplicates"] == 1
    assert store_diag["observation_count"] == 2
    assert store_diag["snapshot_count"] == 2
    assert len(bus.events) >= 3

    print("[PASS] OPS-004 Historical Recording Pipeline")
    print({
        "pipeline": diag,
        "store": store_diag,
        "events": len(bus.events),
    })


if __name__ == "__main__":
    test_ops_004()
