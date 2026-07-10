
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_source_adapter import (
    OrderFlowSourceAdapter,
    build_order_flow_source_snapshot,
)


def test_order_flow_source_adapter_snapshot():
    raw = [
        {
            "market_id": "KXTEST-YES",
            "venue": "kalshi",
            "instrument": "binary_event",
            "bid_size": 70,
            "ask_size": 30,
            "bid_price": 0.42,
            "ask_price": 0.45,
            "last_price": 0.43,
            "volume": 1200,
            "open_interest": 5000,
            "observed_at": "2026-07-09T00:00:00+00:00",
        },
        {
            "market_id": "KXTEST-NO",
            "venue": "kalshi",
            "instrument": "binary_event",
            "bid_size": 20,
            "ask_size": 80,
            "bid_price": 0.55,
            "ask_price": 0.58,
            "last_price": 0.56,
            "volume": 900,
            "open_interest": 4500,
            "observed_at": "2026-07-09T00:00:00+00:00",
        },
    ]

    adapter = OrderFlowSourceAdapter(source_name="order_flow.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(raw, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(raw)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "OFD-002"
    assert snap1.engine_id == "oracle.discovery.order_flow.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert round(snap1.records[0].imbalance, 6) in (-0.6, 0.4)


def test_order_flow_source_adapter_empty():
    snap = build_order_flow_source_snapshot([], source_name="order_flow.empty")
    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


if __name__ == "__main__":
    test_order_flow_source_adapter_snapshot()
    test_order_flow_source_adapter_empty()
    snap = build_order_flow_source_snapshot([], source_name="order_flow.empty")
    print("[PASS] OFD-002 Order Flow Source Adapter")
    print(
        {
            "schema_version": snap.schema_version,
            "engine_id": snap.engine_id,
            "status": snap.status,
            "records": snap.record_count,
            "read_only": snap.read_only,
        }
    )
