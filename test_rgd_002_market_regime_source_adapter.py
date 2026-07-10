
from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_source_adapter import (
    MarketRegimeSourceAdapter,
    build_market_regime_source_snapshot,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"

RAW = [
    {
        "market_id": "KXTEST",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": "volatility_discovery",
        "signal_type": "volatility_expansion",
        "signal_direction": "expanding",
        "confidence": 0.84,
        "magnitude": 0.72,
        "prior_regime": "stable",
        "candidate_regime": "volatile",
        "transition_type": "stable_to_volatile",
        "source_hash": "volatility-source-hash",
        "sequence": 2,
        "observed_at": OBSERVED_AT,
        "metadata": {
            "realized_volatility": 0.42,
            "baseline_volatility": 0.20,
        },
    },
    {
        "market_id": "KXTEST",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": "liquidity_discovery",
        "signal_type": "thin_depth",
        "direction": "low_liquidity",
        "confidence": 0.76,
        "magnitude": 0.61,
        "previous_regime": "stable",
        "current_regime": "illiquid",
        "transition": "stable_to_illiquid",
        "result_hash": "liquidity-source-hash",
        "sequence": 1,
        "timestamp": OBSERVED_AT,
    },
    {
        "market_id": "KXRELATED",
        "venue": "kalshi",
        "asset": "binary_event",
        "family": "correlation_discovery",
        "signal": "correlation_break",
        "relationship": "relationship_decay",
        "score": 0.71,
        "strength": 0.54,
        "prior_regime": "stable",
        "target_regime": "dislocated",
        "transition_type": "stable_to_dislocated",
        "event_hash": "correlation-source-hash",
        "sequence": 3,
        "time": OBSERVED_AT,
    },
]


def test_market_regime_source_adapter_snapshot():
    adapter = MarketRegimeSourceAdapter(
        source_name="market_regime.test"
    )

    assert adapter.assert_read_only() is True

    snapshot1 = adapter.snapshot(
        RAW,
        observed_at=OBSERVED_AT,
    )

    snapshot2 = adapter.snapshot(
        list(reversed(RAW)),
        observed_at=OBSERVED_AT,
    )

    assert snapshot1.schema_version == "RGD-002"
    assert snapshot1.engine_id == (
        "oracle.discovery.market_regime."
        "source_adapter"
    )
    assert snapshot1.status == "ok"
    assert snapshot1.record_count == 3
    assert snapshot1.family_count == 3
    assert snapshot1.market_count == 2
    assert snapshot1.read_only is True
    assert snapshot1.snapshot_hash
    assert (
        snapshot1.snapshot_hash
        == snapshot2.snapshot_hash
    )
    assert (
        snapshot1.verify_snapshot_hash()
        is True
    )

    for record in snapshot1.records:
        assert record.source_id
        assert record.source_hash
        assert record.record_hash
        assert 0.0 <= record.confidence <= 1.0
        assert 0.0 <= record.magnitude <= 1.0
        assert (
            record.metadata["normalized_by"]
            == (
                "oracle.discovery.market_regime."
                "source_adapter"
            )
        )
        assert record.metadata["raw_hash"]


def test_market_regime_source_adapter_normalizes_aliases():
    snapshot = build_market_regime_source_snapshot(
        [
            {
                "symbol": "TEST",
                "exchange": "demo",
                "instrument": "event_contract",
                "discovery_family": (
                    "order_flow_discovery"
                ),
                "event_type": (
                    "order_flow_imbalance"
                ),
                "direction": "bid_pressure",
                "score": 1.40,
                "severity": -0.60,
                "previous_regime": "stable",
                "regime": "trending",
                "transition": (
                    "stable_to_trending"
                ),
                "record_hash": (
                    "order-flow-source-hash"
                ),
                "index": 4,
                "timestamp": OBSERVED_AT,
            }
        ],
        source_name="market_regime.alias",
        observed_at=OBSERVED_AT,
    )

    record = snapshot.records[0]

    assert record.market_id == "TEST"
    assert record.venue == "demo"
    assert record.asset == "event_contract"
    assert (
        record.source_family
        == "order_flow_discovery"
    )
    assert (
        record.signal_type
        == "order_flow_imbalance"
    )
    assert record.signal_direction == "bid_pressure"
    assert record.confidence == 1.0
    assert record.magnitude == 0.60
    assert record.prior_regime == "stable"
    assert record.candidate_regime == "trending"
    assert (
        record.transition_type
        == "stable_to_trending"
    )
    assert record.sequence == 4
    assert (
        record.source_hash
        == "order-flow-source-hash"
    )


def test_market_regime_source_adapter_generates_source_hash():
    snapshot = build_market_regime_source_snapshot(
        [
            {
                "market_id": "KXHASH",
                "venue": "kalshi",
                "asset": "binary_event",
                "source_family": "news_discovery",
                "signal_type": "event_shock",
                "direction": "event_driven",
                "confidence": 0.80,
                "magnitude": 0.70,
                "candidate_regime": "event_driven",
                "observed_at": OBSERVED_AT,
            }
        ],
        source_name="market_regime.hash",
        observed_at=OBSERVED_AT,
    )

    record = snapshot.records[0]

    assert record.source_id
    assert record.source_hash
    assert record.record_hash


def test_market_regime_source_adapter_empty():
    snapshot = build_market_regime_source_snapshot(
        [],
        source_name="market_regime.empty",
        observed_at=OBSERVED_AT,
    )

    assert snapshot.status == "empty"
    assert snapshot.record_count == 0
    assert snapshot.family_count == 0
    assert snapshot.market_count == 0
    assert snapshot.records == tuple()
    assert snapshot.read_only is True
    assert snapshot.snapshot_hash
    assert (
        snapshot.verify_snapshot_hash()
        is True
    )


def test_market_regime_source_adapter_is_replayable():
    snapshot1 = build_market_regime_source_snapshot(
        RAW,
        source_name="market_regime.replay",
        observed_at=OBSERVED_AT,
    )

    snapshot2 = build_market_regime_source_snapshot(
        RAW,
        source_name="market_regime.replay",
        observed_at=OBSERVED_AT,
    )

    assert (
        snapshot1.snapshot_hash
        == snapshot2.snapshot_hash
    )

    assert [
        record.record_hash
        for record in snapshot1.records
    ] == [
        record.record_hash
        for record in snapshot2.records
    ]


def test_market_regime_source_adapter_rejects_invalid_record():
    adapter = MarketRegimeSourceAdapter()

    try:
        adapter.normalize_record(
            ["not", "a", "mapping"]
        )
    except TypeError as exc:
        assert str(exc) == (
            "raw market regime record "
            "must be a mapping"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid record"
        )


if __name__ == "__main__":
    test_market_regime_source_adapter_snapshot()
    test_market_regime_source_adapter_normalizes_aliases()
    test_market_regime_source_adapter_generates_source_hash()
    test_market_regime_source_adapter_empty()
    test_market_regime_source_adapter_is_replayable()
    test_market_regime_source_adapter_rejects_invalid_record()

    snapshot = build_market_regime_source_snapshot(
        [],
        source_name="market_regime.empty",
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-002 "
        "Market Regime Source Adapter"
    )
    print(
        {
            "schema_version": (
                snapshot.schema_version
            ),
            "engine_id": snapshot.engine_id,
            "status": snapshot.status,
            "records": snapshot.record_count,
            "families": snapshot.family_count,
            "markets": snapshot.market_count,
            "read_only": snapshot.read_only,
        }
    )
