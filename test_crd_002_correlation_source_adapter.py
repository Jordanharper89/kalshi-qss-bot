
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_source_adapter import (
    CorrelationSourceAdapter,
    build_correlation_source_snapshot,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.22,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.04,
        "related_return": -0.02,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.71,
        "baseline_correlation": -0.68,
        "recent_correlation": -0.70,
        "lag": 1,
        "window": "30d",
        "sample_size": 110,
        "primary_return": 0.03,
        "related_return": -0.03,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_correlation_source_adapter_snapshot():
    adapter = CorrelationSourceAdapter(source_name="correlation.test")
    assert adapter.assert_read_only() is True

    snap1 = adapter.snapshot(RAW, observed_at="2026-07-09T00:00:00+00:00")
    snap2 = adapter.snapshot(list(reversed(RAW)), observed_at="2026-07-09T00:00:00+00:00")

    assert snap1.schema_version == "CRD-002"
    assert snap1.engine_id == "oracle.discovery.correlation.source_adapter"
    assert snap1.status == "ok"
    assert snap1.record_count == 2
    assert snap1.read_only is True
    assert snap1.snapshot_hash == snap2.snapshot_hash
    assert snap1.records[0].record_hash
    assert snap1.records[0].correlation_change == snap1.records[0].recent_correlation - snap1.records[0].baseline_correlation


def test_correlation_source_adapter_empty():
    snap = build_correlation_source_snapshot([], source_name="correlation.empty")

    assert snap.status == "empty"
    assert snap.record_count == 0
    assert snap.read_only is True
    assert snap.snapshot_hash


def test_correlation_source_adapter_accepts_aliases():
    snap = build_correlation_source_snapshot(
        [
            {
                "market_a": "A",
                "market_b": "B",
                "exchange": "demo",
                "corr": 0.5,
                "baseline": 0.7,
                "recent": 0.1,
                "lead_lag": 2,
                "lookback": "7d",
                "n": 20,
                "return_a": 0.03,
                "return_b": -0.01,
                "timestamp": "2026-07-09T00:00:00+00:00",
            }
        ],
        source_name="correlation.alias",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    record = snap.records[0]
    assert record.primary_market_id == "A"
    assert record.related_market_id == "B"
    assert record.venue == "demo"
    assert record.correlation == 0.5
    assert record.baseline_correlation == 0.7
    assert record.recent_correlation == 0.1
    assert round(record.correlation_change, 6) == -0.6
    assert record.lag == 2
    assert record.window == "7d"
    assert record.sample_size == 20


if __name__ == "__main__":
    test_correlation_source_adapter_snapshot()
    test_correlation_source_adapter_empty()
    test_correlation_source_adapter_accepts_aliases()

    snap = build_correlation_source_snapshot([], source_name="correlation.empty")

    print("[PASS] CRD-002 Correlation Source Adapter")
    print(
        {
            "schema_version": snap.schema_version,
            "engine_id": snap.engine_id,
            "status": snap.status,
            "records": snap.record_count,
            "read_only": snap.read_only,
        }
    )
