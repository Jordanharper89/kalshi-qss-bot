
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_contract import (
    validate_market_regime_discovery_result,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_engine import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeEngineConfig,
    NormalizedRegimeSignal,
    assert_market_regime_engine_read_only,
    discover_market_regimes,
    normalize_regime_signal,
    normalize_regime_signals,
    run_market_regime_discovery,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"


def _source_record(
    signal_id,
    signal_type,
    value,
    reliability=0.90,
    prior_regime="stable",
    market_id="KXTEST",
    source_family="test_family",
):
    return {
        "signal_id": signal_id,
        "market_id": market_id,
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": source_family,
        "signal_type": signal_type,
        "value": value,
        "reliability": reliability,
        "observed_at": OBSERVED_AT,
        "prior_regime": prior_regime,
        "source_hash": (
            f"source-hash-{signal_id}"
        ),
        "details": {
            "test_signal": True,
        },
    }


def _volatile_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "ok",
        "observed_at": OBSERVED_AT,
        "records": (
            _source_record(
                signal_id="signal-volatility",
                signal_type="volatility",
                value=0.95,
                reliability=0.95,
                source_family=(
                    "volatility_discovery"
                ),
            ),
            _source_record(
                signal_id="signal-dispersion",
                signal_type="dispersion",
                value=0.90,
                reliability=0.90,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _source_record(
                signal_id="signal-correlation",
                signal_type=(
                    "correlation_breakdown"
                ),
                value=0.85,
                reliability=0.90,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _source_record(
                signal_id="signal-liquidity",
                signal_type="liquidity",
                value=-0.45,
                reliability=0.80,
                source_family=(
                    "liquidity_discovery"
                ),
            ),
        ),
        "read_only": True,
    }


def test_market_regime_engine_constants():
    assert SCHEMA_VERSION == "RGD-003"
    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "discovery_engine"
    )
    assert READ_ONLY is True


def test_market_regime_engine_normalizes_signal():
    signal = normalize_regime_signal(
        {
            "id": "signal-001",
            "ticker": "KXTEST",
            "exchange": "kalshi",
            "asset_type": "binary_event",
            "family": "volatility_discovery",
            "metric": "volatility_expansion",
            "score": 82.0,
            "confidence": 90.0,
            "timestamp": OBSERVED_AT,
            "previous_regime": "stable",
            "record_hash": (
                "source-record-hash"
            ),
        }
    )

    assert isinstance(
        signal,
        NormalizedRegimeSignal,
    )
    assert signal.signal_id == "signal-001"
    assert signal.market_id == "KXTEST"
    assert signal.venue == "kalshi"
    assert signal.asset == "binary_event"
    assert signal.source_family == (
        "volatility_discovery"
    )
    assert signal.signal_type == "volatility"
    assert signal.value == 0.82
    assert signal.reliability == 0.90
    assert signal.prior_regime == "stable"


def test_market_regime_engine_discovers_transition():
    result = discover_market_regimes(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.schema_version == "RGD-001"
    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.opportunity_count == 1
    assert result.read_only is True
    assert result.result_hash
    assert result.verify_result_hash() is True

    opportunity = result.opportunities[0]

    assert opportunity.market_id == "KXTEST"
    assert opportunity.venue == "kalshi"
    assert opportunity.asset == "binary_event"
    assert opportunity.prior_regime == "stable"
    assert opportunity.current_regime in {
        "volatile",
        "dislocated",
        "transition",
    }
    assert opportunity.current_regime != (
        opportunity.prior_regime
    )
    assert opportunity.confidence >= 0.55
    assert opportunity.magnitude >= 0.15
    assert len(opportunity.evidence) == 4
    assert opportunity.explanation
    assert (
        opportunity.transition_type
        == (
            f"stable_to_"
            f"{opportunity.current_regime}"
        )
    )


def test_market_regime_engine_empty_source():
    result = discover_market_regimes(
        source_result={
            "schema_version": "RGD-002",
            "engine_id": (
                "oracle.discovery.market_regime."
                "source_adapter"
            ),
            "status": "empty",
            "records": tuple(),
            "observed_at": OBSERVED_AT,
            "read_only": True,
        },
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert (
        result.metadata[
            "source_record_count"
        ]
        == 0
    )
    assert (
        result.metadata[
            "accepted_market_count"
        ]
        == 0
    )


def test_market_regime_engine_filters_weak_signal():
    result = discover_market_regimes(
        source_result={
            "schema_version": "RGD-002",
            "status": "ok",
            "records": (
                _source_record(
                    signal_id="weak-volatility",
                    signal_type="volatility",
                    value=0.05,
                    reliability=0.20,
                ),
            ),
            "observed_at": OBSERVED_AT,
        },
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert (
        result.metadata[
            "rejected_market_count"
        ]
        == 1
    )


def test_market_regime_engine_allows_continuation():
    source = {
        "schema_version": "RGD-002",
        "status": "ok",
        "records": (
            _source_record(
                signal_id="trend-001",
                signal_type="trend_strength",
                value=0.95,
                reliability=0.95,
                prior_regime="trending",
            ),
            _source_record(
                signal_id="momentum-001",
                signal_type="momentum",
                value=0.90,
                reliability=0.90,
                prior_regime="trending",
            ),
        ),
        "observed_at": OBSERVED_AT,
    }

    strict_result = discover_market_regimes(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert strict_result.status == "empty"

    continuation_result = (
        discover_market_regimes(
            source_result=source,
            observed_at=OBSERVED_AT,
            config=MarketRegimeEngineConfig(
                confidence_threshold=0.40,
                magnitude_threshold=0.10,
                minimum_signal_count=1,
                require_transition=False,
            ),
        )
    )

    assert continuation_result.status == "ok"
    assert (
        continuation_result.opportunity_count
        == 1
    )

    opportunity = (
        continuation_result
        .opportunities[0]
    )

    assert opportunity.prior_regime == (
        "trending"
    )
    assert opportunity.current_regime == (
        "trending"
    )
    assert opportunity.transition_type == (
        "trending_continuation"
    )


def test_market_regime_engine_is_replayable():
    result1 = run_market_regime_discovery(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    result2 = run_market_regime_discovery(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    assert result1.result_hash == (
        result2.result_hash
    )

    assert (
        result1.opportunities[0]
        .opportunity_id
        == result2.opportunities[0]
        .opportunity_id
    )

    assert (
        result1.opportunities[0]
        .opportunity_hash
        == result2.opportunities[0]
        .opportunity_hash
    )


def test_market_regime_engine_input_order_independent():
    source = _volatile_source()

    reversed_source = dict(source)
    reversed_source["records"] = tuple(
        reversed(source["records"])
    )

    result1 = discover_market_regimes(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    result2 = discover_market_regimes(
        source_result=reversed_source,
        observed_at=OBSERVED_AT,
    )

    assert result1.result_hash == (
        result2.result_hash
    )

    assert result1.opportunities == (
        result2.opportunities
    )


def test_market_regime_engine_multiple_markets():
    records = list(
        _volatile_source()["records"]
    )

    records.extend(
        (
            _source_record(
                signal_id="risk-appetite-002",
                signal_type="risk_appetite",
                value=0.95,
                reliability=0.95,
                prior_regime="risk_off",
                market_id="MARKET-B",
                source_family=(
                    "macro_event_discovery"
                ),
            ),
            _source_record(
                signal_id="momentum-002",
                signal_type="momentum",
                value=0.90,
                reliability=0.90,
                prior_regime="risk_off",
                market_id="MARKET-B",
                source_family=(
                    "order_flow_discovery"
                ),
            ),
            _source_record(
                signal_id="liquidity-002",
                signal_type="liquidity",
                value=0.80,
                reliability=0.85,
                prior_regime="risk_off",
                market_id="MARKET-B",
                source_family=(
                    "liquidity_discovery"
                ),
            ),
        )
    )

    result = discover_market_regimes(
        source_result={
            "schema_version": "RGD-002",
            "status": "ok",
            "records": tuple(records),
            "observed_at": OBSERVED_AT,
        },
        observed_at=OBSERVED_AT,
        config=MarketRegimeEngineConfig(
            confidence_threshold=0.50,
            magnitude_threshold=0.10,
            minimum_signal_count=1,
            require_transition=True,
        ),
    )

    assert result.status == "ok"
    assert result.opportunity_count == 2

    market_ids = [
        item.market_id
        for item in result.opportunities
    ]

    assert market_ids == [
        "KXTEST",
        "MARKET-B",
    ]


def test_market_regime_engine_validates_result():
    result = discover_market_regimes(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_discovery_result(
            result
        )
    )

    assert validation["accepted"] is True
    assert all(
        validation["checks"].values()
    )


def test_market_regime_engine_read_only():
    result = discover_market_regimes(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_engine_read_only(
            result
        )
        is True
    )

    try:
        result.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "result must be immutable"
        )

    signal = normalize_regime_signals(
        _volatile_source()["records"]
    )[0]

    try:
        signal.value = 0.0
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "normalized signal must be "
            "immutable"
        )


def test_market_regime_engine_rejects_bad_config():
    try:
        MarketRegimeEngineConfig(
            confidence_threshold=1.10,
        )
    except ValueError as exc:
        assert str(exc) == (
            "confidence_threshold must be "
            "between 0.0 and 1.0"
        )
    else:
        raise AssertionError(
            "expected invalid configuration"
        )


def test_market_regime_engine_rejects_duplicate_signals():
    record = _source_record(
        signal_id="duplicate-signal",
        signal_type="volatility",
        value=0.90,
    )

    try:
        normalize_regime_signals(
            (record, record)
        )
    except ValueError as exc:
        assert str(exc) == (
            "signal identifiers must be unique"
        )
    else:
        raise AssertionError(
            "expected duplicate rejection"
        )


if __name__ == "__main__":
    test_market_regime_engine_constants()
    test_market_regime_engine_normalizes_signal()
    test_market_regime_engine_discovers_transition()
    test_market_regime_engine_empty_source()
    test_market_regime_engine_filters_weak_signal()
    test_market_regime_engine_allows_continuation()
    test_market_regime_engine_is_replayable()
    test_market_regime_engine_input_order_independent()
    test_market_regime_engine_multiple_markets()
    test_market_regime_engine_validates_result()
    test_market_regime_engine_read_only()
    test_market_regime_engine_rejects_bad_config()
    test_market_regime_engine_rejects_duplicate_signals()

    result = discover_market_regimes(
        source_result=_volatile_source(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-003 "
        "Market Regime Discovery Engine"
    )

    print(
        {
            "schema_version": SCHEMA_VERSION,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": (
                result.opportunity_count
            ),
            "markets": (
                result.metadata[
                    "market_count"
                ]
            ),
            "signals": (
                result.metadata[
                    "normalized_signal_count"
                ]
            ),
            "read_only": result.read_only,
        }
    )
