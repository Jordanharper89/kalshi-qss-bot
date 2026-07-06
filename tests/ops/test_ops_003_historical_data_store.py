"""
Test OPS-003 Persistent Historical Data Store.
"""

import tempfile
from pathlib import Path

from qseries_v2.ops.historical_data_store import build_historical_data_store


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_003():
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "test_history.sqlite3")
    bus = FakeEventBus()

    store = build_historical_data_store(db_path=db_path, event_bus=bus)

    markets = [
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
        },
        {
            "ticker": "SERIES-EVENT-002",
            "event_ticker": "EVENT",
            "series_ticker": "SERIES",
            "category": "Test",
            "title": "Market 2",
            "status": "open",
            "yes_bid": 55,
            "yes_ask": 57,
            "no_bid": 43,
            "no_ask": 45,
            "last_price": 56,
            "volume": 150,
            "open_interest": 250,
            "liquidity": 350,
        },
    ]

    result = store.record_snapshot(markets, source="test_cache", metadata={"test": True})
    assert result["status"] == "ok"
    assert result["inserted_count"] == 2

    single = store.record_market_observation(markets[0])
    assert single["status"] == "ok"

    latest = store.latest_for_ticker("SERIES-EVENT-001", limit=5)
    assert len(latest) == 2
    assert latest[0]["ticker"] == "SERIES-EVENT-001"

    snapshots = store.recent_snapshots(limit=5)
    assert len(snapshots) == 1
    assert snapshots[0]["source"] == "test_cache"

    diag = store.diagnostics()
    assert diag["status"] == "ok"
    assert diag["observation_count"] == 3
    assert diag["snapshot_count"] == 1
    assert len(bus.events) >= 1

    print("[PASS] OPS-003 Persistent Historical Data Store")
    print(diag)


if __name__ == "__main__":
    test_ops_003()
