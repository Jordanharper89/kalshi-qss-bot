
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_source_adapter import (
    VolatilitySourceAdapter,
    build_volatility_source_snapshot,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.38,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXVOL-CALM",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.12,
        "implied_volatility": 0.14,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_source_adapter_snapshot():
    adapter = VolatilitySourceAdapter(source_name="volatility.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(RAW, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(RAW)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "VLD-002"
    assert snap1.engine_id == "oracle.discovery.volatility.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert snap1.records[0].volatility_ratio > 0.0


def test_volatility_source_adapter_empty():
    snap = build_volatility_source_snapshot([], source_name="volatility.empty")

    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


def test_volatility_source_adapter_accepts_aliases():
    snap = build_volatility_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "rv": 0.30,
                "iv": 0.35,
                "baseline": 0.15,
                "return": 0.05,
                "vol": 1000,
                "lookback": "4h",
                "timestamp": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="volatility.alias",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    record = snap.records[0]
    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "TEST"
    assert record.realized_volatility == 0.30
    assert record.implied_volatility == 0.35
    assert record.baseline_volatility == 0.15
    assert record.volatility_change == 0.15
    assert record.volatility_ratio == 2.0
    assert record.window == "4h"


if __name__ == "__main__":
    test_volatility_source_adapter_snapshot()
    test_volatility_source_adapter_empty()
    test_volatility_source_adapter_accepts_aliases()

    snap = build_volatility_source_snapshot([], source_name="volatility.empty")

    print("[PASS] VLD-002 Volatility Source Adapter")
    print(
        {
            "schema_version": snap.schema_version,
            "engine_id": snap.engine_id,
            "status": snap.status,
            "records": snap.record_count,
            "read_only": snap.read_only,
        }
    )
