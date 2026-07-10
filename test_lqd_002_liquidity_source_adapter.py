
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_source_adapter import (
    LiquiditySourceAdapter,
    build_liquidity_source_snapshot,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.42,
        "ask_price": 0.45,
        "bid_depth": 1200,
        "ask_depth": 800,
        "volume_24h": 10000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.55,
        "ask_price": 0.58,
        "bid_depth": 900,
        "ask_depth": 1100,
        "volume_24h": 9000,
        "open_interest": 45000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_liquidity_source_adapter_snapshot():
    adapter = LiquiditySourceAdapter(source_name="liquidity.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(RAW, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(RAW)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "LQD-002"
    assert snap1.engine_id == "oracle.discovery.liquidity.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert snap1.records[0].spread >= 0.0
    assert snap1.records[0].spread_bps > 0.0
    assert snap1.records[0].total_depth == 2000


def test_liquidity_source_adapter_empty():
    snap = build_liquidity_source_snapshot([], source_name="liquidity.empty")

    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


def test_liquidity_source_adapter_accepts_aliases():
    snap = build_liquidity_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "bid": 10,
                "ask": 11,
                "bid_size": 50,
                "ask_size": 25,
                "volume": 1000,
                "oi": 2000,
                "timestamp": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="liquidity.alias",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    record = snap.records[0]
    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "TEST"
    assert record.total_depth == 75
    assert record.spread == 1
    assert record.volume_24h == 1000
    assert record.open_interest == 2000


if __name__ == "__main__":
    test_liquidity_source_adapter_snapshot()
    test_liquidity_source_adapter_empty()
    test_liquidity_source_adapter_accepts_aliases()

    snap = build_liquidity_source_snapshot([], source_name="liquidity.empty")

    print("[PASS] LQD-002 Liquidity Source Adapter")
    print(
        {
            "schema_version": snap.schema_version,
            "engine_id": snap.engine_id,
            "status": snap.status,
            "records": snap.record_count,
            "read_only": snap.read_only,
        }
    )
