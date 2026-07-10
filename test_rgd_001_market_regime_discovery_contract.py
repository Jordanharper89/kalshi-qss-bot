
from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_contract import (
    ALLOWED_REGIMES,
    MarketRegimeDiscoveryResult,
    MarketRegimeEvidence,
    MarketRegimeOpportunity,
    assert_market_regime_contract_read_only,
    build_market_regime_discovery_result,
    empty_market_regime_discovery_result,
    validate_market_regime_discovery_result,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"


def _build_evidence():
    return MarketRegimeEvidence(
        evidence_id="evidence-volatility-001",
        source_family="volatility_discovery",
        signal_type="volatility_expansion",
        contribution=0.80,
        source_hash="source-hash-volatility-001",
        details={
            "realized_volatility": 0.42,
            "baseline_volatility": 0.20,
        },
    )


def _build_opportunity():
    return MarketRegimeOpportunity(
        opportunity_id="regime-opportunity-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="volatile",
        transition_type=(
            "stable_to_volatile"
        ),
        confidence=0.84,
        magnitude=0.71,
        observed_at=OBSERVED_AT,
        explanation=(
            "Volatility expansion and liquidity "
            "deterioration indicate a regime transition."
        ),
        evidence=(
            _build_evidence(),
        ),
    )


def test_market_regime_contract_empty_result():
    result = (
        empty_market_regime_discovery_result(
            observed_at=OBSERVED_AT,
        )
    )

    assert result.schema_version == "RGD-001"
    assert result.engine_id == (
        "oracle.discovery.market_regime.empty"
    )
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert result.verify_result_hash() is True
    assert (
        assert_market_regime_contract_read_only(
            result
        )
        is True
    )


def test_market_regime_contract_builds_valid_result():
    opportunity = _build_opportunity()

    result = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "scenario": (
                    "volatility_transition"
                ),
            },
        )
    )

    assert result.status == "ok"
    assert result.opportunity_count == 1
    assert result.read_only is True
    assert result.result_hash
    assert result.verify_result_hash() is True
    assert (
        result.opportunities[0]
        .opportunity_hash
    )
    assert (
        result.opportunities[0]
        .evidence[0]
        .evidence_hash
    )


def test_market_regime_contract_is_replayable():
    opportunity = _build_opportunity()

    result1 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "source": "deterministic",
            },
        )
    )

    result2 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "source": "deterministic",
            },
        )
    )

    assert (
        result1.result_hash
        == result2.result_hash
    )
    assert (
        result1.opportunities[0]
        .opportunity_hash
        == result2.opportunities[0]
        .opportunity_hash
    )


def test_market_regime_contract_orders_opportunities():
    first = MarketRegimeOpportunity(
        opportunity_id="opportunity-b",
        market_id="MARKET-B",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="trending",
        transition_type="trend_emergence",
        confidence=0.70,
        magnitude=0.50,
        observed_at=OBSERVED_AT,
        explanation="Trend regime detected.",
        evidence=tuple(),
    )

    second = MarketRegimeOpportunity(
        opportunity_id="opportunity-a",
        market_id="MARKET-A",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="volatile",
        transition_type=(
            "volatility_expansion"
        ),
        confidence=0.75,
        magnitude=0.60,
        observed_at=OBSERVED_AT,
        explanation=(
            "Volatile regime detected."
        ),
        evidence=tuple(),
    )

    result1 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.order_test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(first, second),
        )
    )

    result2 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.order_test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(second, first),
        )
    )

    assert [
        item.market_id
        for item in result1.opportunities
    ] == [
        "MARKET-A",
        "MARKET-B",
    ]

    assert (
        result1.result_hash
        == result2.result_hash
    )


def test_market_regime_contract_validation():
    result = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.validation"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(
                _build_opportunity(),
            ),
        )
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
    assert (
        validation["opportunity_count"]
        == 1
    )
    assert validation["read_only"] is True


def test_market_regime_contract_rejects_invalid_regime():
    try:
        MarketRegimeOpportunity(
            opportunity_id="invalid-regime",
            market_id="KXTEST",
            venue="kalshi",
            asset="binary_event",
            prior_regime="stable",
            current_regime="unsupported_regime",
            transition_type="invalid",
            confidence=0.50,
            magnitude=0.50,
            observed_at=OBSERVED_AT,
            explanation="Invalid test.",
            evidence=tuple(),
        )
    except ValueError as exc:
        assert str(exc) == (
            "current_regime is not supported"
        )
    else:
        raise AssertionError(
            "expected invalid regime rejection"
        )


def test_market_regime_contract_rejects_mutable_result():
    try:
        MarketRegimeDiscoveryResult(
            schema_version="RGD-001",
            engine_id=(
                "oracle.discovery."
                "market_regime.invalid"
            ),
            status="empty",
            observed_at=OBSERVED_AT,
            opportunities=tuple(),
            metadata={},
            read_only=False,
            result_hash="",
        )
    except ValueError as exc:
        assert str(exc) == (
            "market regime results "
            "must be read-only"
        )
    else:
        raise AssertionError(
            "expected mutable result rejection"
        )


def test_market_regime_contract_allowed_regimes():
    required = {
        "unknown",
        "stable",
        "trending",
        "mean_reverting",
        "volatile",
        "illiquid",
        "dislocated",
        "event_driven",
        "risk_on",
        "risk_off",
        "transition",
    }

    assert required == set(
        ALLOWED_REGIMES
    )


if __name__ == "__main__":
    test_market_regime_contract_empty_result()
    test_market_regime_contract_builds_valid_result()
    test_market_regime_contract_is_replayable()
    test_market_regime_contract_orders_opportunities()
    test_market_regime_contract_validation()
    test_market_regime_contract_rejects_invalid_regime()
    test_market_regime_contract_rejects_mutable_result()
    test_market_regime_contract_allowed_regimes()

    result = (
        empty_market_regime_discovery_result(
            observed_at=OBSERVED_AT,
        )
    )

    print(
        "[PASS] RGD-001 "
        "Market Regime Discovery Contract"
    )
    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": (
                result.opportunity_count
            ),
            "read_only": result.read_only,
        }
    )
