from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    ComparisonScoringPolicy,
    CrossVenueOpportunityCandidate,
    OpportunityComparabilityError,
    OpportunityComparisonContractError,
    OracleCanonicalCrossVenueOpportunityComparisonEngine,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    22,
    45,
    0,
    tzinfo=timezone.utc,
)

VALID_FROM = datetime(
    2026,
    7,
    11,
    22,
    45,
    5,
    tzinfo=timezone.utc,
)

COMPARE_AT = datetime(
    2026,
    7,
    11,
    22,
    46,
    0,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    11,
    22,
    55,
    0,
    tzinfo=timezone.utc,
)

EXPIRED_AT = datetime(
    2026,
    7,
    11,
    22,
    45,
    30,
    tzinfo=timezone.utc,
)


def build_policy():
    return ComparisonScoringPolicy.create(
        policy_id="oracle.cross_venue.btc_bearish.v1",
        component_weights={
            "expected_edge": Decimal("0.35"),
            "liquidity_quality": Decimal("0.20"),
            "thesis_alignment": Decimal("0.25"),
            "time_fit": Decimal("0.10"),
            "venue_quality": Decimal("0.10"),
        },
        higher_score_preferred=True,
    )


def build_kalshi_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.kalshi.btc.001",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.kalshi.btc.001",
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price=Decimal("0.31"),
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="market-venue-record-kalshi",
        validity_evidence_hash="validity-kalshi",
        normalized_components={
            "expected_edge": Decimal("0.94"),
            "liquidity_quality": Decimal("0.75"),
            "thesis_alignment": Decimal("0.96"),
            "time_fit": Decimal("0.92"),
            "venue_quality": Decimal("0.88"),
        },
        metadata={
            "share_side": "yes",
            "market_question": (
                "Bitcoin below 116000 by 5 PM"
            ),
        },
    )


def build_coinbase_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.coinbase.btc.001",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.coinbase.btcusd",
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell_or_short_thesis",
        direction="bearish",
        reference_price=Decimal("117420"),
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="market-venue-record-coinbase",
        validity_evidence_hash="validity-coinbase",
        normalized_components={
            "expected_edge": Decimal("0.68"),
            "liquidity_quality": Decimal("0.98"),
            "thesis_alignment": Decimal("0.84"),
            "time_fit": Decimal("0.74"),
            "venue_quality": Decimal("0.93"),
        },
        metadata={
            "asset": "BTC",
            "quote_asset": "USD",
        },
    )


def build_kraken_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.kraken.btc.001",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.kraken.xbtusd",
        venue_id="venue.kraken",
        venue_name="Kraken",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell_or_short_thesis",
        direction="bearish",
        reference_price=Decimal("117398"),
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="market-venue-record-kraken",
        validity_evidence_hash="validity-kraken",
        normalized_components={
            "expected_edge": Decimal("0.65"),
            "liquidity_quality": Decimal("0.91"),
            "thesis_alignment": Decimal("0.83"),
            "time_fit": Decimal("0.73"),
            "venue_quality": Decimal("0.90"),
        },
        metadata={
            "asset": "XBT",
            "quote_asset": "USD",
        },
    )


def build_expired_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.expired.btc.001",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.expired.btc.001",
        venue_id="venue.expired",
        venue_name="Expired Venue",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price=Decimal("0.10"),
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRED_AT,
        validity_status="expired",
        venue_verified=True,
        source_record_hash="market-venue-record-expired",
        validity_evidence_hash="validity-expired",
        normalized_components={
            "expected_edge": Decimal("1.00"),
            "liquidity_quality": Decimal("1.00"),
            "thesis_alignment": Decimal("1.00"),
            "time_fit": Decimal("1.00"),
            "venue_quality": Decimal("1.00"),
        },
        metadata={},
    )


def build_unverified_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.unverified.btc.001",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.unverified.btc.001",
        venue_id="venue.unverified",
        venue_name="Unverified Venue",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price=Decimal("0.05"),
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=False,
        source_record_hash="market-venue-record-unverified",
        validity_evidence_hash="validity-unverified",
        normalized_components={
            "expected_edge": Decimal("1.00"),
            "liquidity_quality": Decimal("1.00"),
            "thesis_alignment": Decimal("1.00"),
            "time_fit": Decimal("1.00"),
            "venue_quality": Decimal("1.00"),
        },
        metadata={},
    )


def build_engine():
    return (
        OracleCanonicalCrossVenueOpportunityComparisonEngine(
            scoring_policy=build_policy()
        )
    )


def run_primary_comparison_test():
    candidates = (
        build_kalshi_candidate(),
        build_coinbase_candidate(),
        build_kraken_candidate(),
        build_expired_candidate(),
        build_unverified_candidate(),
    )

    first = build_engine().compare(
        candidates=candidates,
        compared_at=COMPARE_AT,
        replay_metadata={
            "replay_source": "cross_venue_comparison",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-006",
            "operator": "automated_runtime",
        },
    )

    second = build_engine().compare(
        candidates=candidates,
        compared_at=COMPARE_AT,
        replay_metadata={
            "replay_source": "cross_venue_comparison",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-006",
            "operator": "automated_runtime",
        },
    )

    assert first == second

    assert first.schema_version == "OLA-006"
    assert first.engine_id == "OLA-006"

    assert first.thesis_id == (
        "thesis.btc.bearish.001"
    )

    assert first.comparability_group_id == (
        "comparison.btc.bearish.expression"
    )

    assert first.candidate_count == 5
    assert first.eligible_count == 3
    assert first.ineligible_count == 2

    assert len(first.ranked_opportunities) == 3

    assert first.best_opportunity_id == (
        "opportunity.kalshi.btc.001"
    )

    assert first.best_venue_id == "venue.kalshi"
    assert first.best_venue_name == "Kalshi"

    assert first.best_expression_type == "buy_yes"
    assert first.best_direction == "bearish"

    assert first.best_reference_price == "0.31"
    assert first.best_price_unit == "USD_PER_SHARE"

    assert first.best_normalized_score is not None

    assert (
        Decimal(first.best_normalized_score)
        > Decimal(
            first.ranked_opportunities[1]
            .normalized_score
        )
    )

    assert first.tie_for_best is False

    assert first.comparison_status == (
        "best_opportunity_resolved"
    )

    assert (
        "normalized_scoring_used"
        in first.reason_codes
    )

    assert (
        "raw_prices_not_compared_directly"
        in first.reason_codes
    )

    assert (
        "venue_ranked_as_intelligence"
        in first.reason_codes
    )

    assert first.read_only is True
    assert first.execution_allowed is False

    assert (
        first.venue_ranked_as_intelligence
        is True
    )

    assert first.execution_adapter_resolved is False
    assert first.execution_adapter_invoked is False

    assert (
        first.trade_authorization_allowed
        is False
    )

    assert first.order_placement_allowed is False
    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    assert (
        first.comparison_hash
        == second.comparison_hash
    )

    try:
        first.best_venue_id = "venue.coinbase"

        raise AssertionError(
            "comparison result must be immutable"
        )

    except FrozenInstanceError:
        pass

    return first


def run_raw_price_separation_test():
    kalshi = build_kalshi_candidate()
    coinbase = build_coinbase_candidate()

    assert kalshi.reference_price == "0.31"
    assert kalshi.price_unit == "USD_PER_SHARE"

    assert coinbase.reference_price == "117420"
    assert coinbase.price_unit == "USD_PER_BTC"

    result = build_engine().compare(
        candidates=(
            kalshi,
            coinbase,
        ),
        compared_at=COMPARE_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.best_venue_id == "venue.kalshi"

    assert (
        result.best_reference_price
        == "0.31"
    )

    assert (
        result.best_price_unit
        == "USD_PER_SHARE"
    )

    return result


def run_comparability_fail_closed_tests():
    mismatched_thesis = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.other.thesis",
        thesis_id="thesis.eth.bullish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.other",
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="long",
        direction="bullish",
        reference_price="3000",
        price_unit="USD_PER_ETH",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="hash-other",
        validity_evidence_hash="validity-other",
        normalized_components={
            "expected_edge": "0.90",
            "liquidity_quality": "0.90",
            "thesis_alignment": "0.90",
            "time_fit": "0.90",
            "venue_quality": "0.90",
        },
        metadata={},
    )

    try:
        build_engine().compare(
            candidates=(
                build_kalshi_candidate(),
                mismatched_thesis,
            ),
            compared_at=COMPARE_AT,
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "mismatched thesis must fail closed"
        )

    except OpportunityComparabilityError:
        pass

    mismatched_group = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.other.group",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.unrelated.contract"
        ),
        canonical_market_id="market.other.group",
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell",
        direction="bearish",
        reference_price="117000",
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="hash-other-group",
        validity_evidence_hash="validity-other-group",
        normalized_components={
            "expected_edge": "0.90",
            "liquidity_quality": "0.90",
            "thesis_alignment": "0.90",
            "time_fit": "0.90",
            "venue_quality": "0.90",
        },
        metadata={},
    )

    try:
        build_engine().compare(
            candidates=(
                build_kalshi_candidate(),
                mismatched_group,
            ),
            compared_at=COMPARE_AT,
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "mismatched comparability group must fail closed"
        )

    except OpportunityComparabilityError:
        pass


def run_component_contract_fail_closed_tests():
    missing_component = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.missing.component",
        thesis_id="thesis.btc.bearish.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id="market.missing.component",
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.40",
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="hash-missing",
        validity_evidence_hash="validity-missing",
        normalized_components={
            "expected_edge": "0.80",
            "liquidity_quality": "0.80",
            "thesis_alignment": "0.80",
            "time_fit": "0.80",
        },
        metadata={},
    )

    try:
        build_engine().compare(
            candidates=(
                missing_component,
            ),
            compared_at=COMPARE_AT,
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "missing score component must fail closed"
        )

    except OpportunityComparisonContractError:
        pass

    try:
        CrossVenueOpportunityCandidate.create(
            opportunity_id="opportunity.bad.score",
            thesis_id="thesis.btc.bearish.001",
            comparability_group_id=(
                "comparison.btc.bearish.expression"
            ),
            canonical_market_id="market.bad.score",
            venue_id="venue.kalshi",
            venue_name="Kalshi",
            venue_type="prediction_market",
            instrument_type="prediction_contract",
            opportunity_type="prediction_market",
            expression_type="buy_yes",
            direction="bearish",
            reference_price="0.40",
            price_unit="USD_PER_SHARE",
            observed_at=OBSERVED_AT,
            valid_from=VALID_FROM,
            expires_at=EXPIRES_AT,
            validity_status="active",
            venue_verified=True,
            source_record_hash="hash-bad-score",
            validity_evidence_hash="validity-bad-score",
            normalized_components={
                "expected_edge": "1.01",
            },
            metadata={},
        )

        raise AssertionError(
            "score above one must fail closed"
        )

    except OpportunityComparisonContractError:
        pass


def run_all_ineligible_test():
    result = build_engine().compare(
        candidates=(
            build_expired_candidate(),
            build_unverified_candidate(),
        ),
        compared_at=COMPARE_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.eligible_count == 0

    assert result.comparison_status == (
        "no_eligible_opportunities"
    )

    assert result.best_opportunity_id is None
    assert result.best_venue_id is None

    assert (
        result.venue_ranked_as_intelligence
        is False
    )

    assert (
        "all_candidates_ineligible"
        in result.reason_codes
    )

    return result


def main():
    result = run_primary_comparison_test()

    run_raw_price_separation_test()
    run_comparability_fail_closed_tests()
    run_component_contract_fail_closed_tests()

    ineligible = run_all_ineligible_test()

    output = {
        "schema_version": result.schema_version,
        "engine_id": result.engine_id,
        "status": "passed",
        "thesis_id": result.thesis_id,
        "comparability_group_id": (
            result.comparability_group_id
        ),
        "candidate_count": result.candidate_count,
        "eligible_count": result.eligible_count,
        "ineligible_count": result.ineligible_count,
        "best_opportunity_id": (
            result.best_opportunity_id
        ),
        "best_venue_id": result.best_venue_id,
        "best_venue_name": result.best_venue_name,
        "best_expression_type": (
            result.best_expression_type
        ),
        "best_direction": result.best_direction,
        "best_reference_price": (
            result.best_reference_price
        ),
        "best_price_unit": result.best_price_unit,
        "comparison_status": (
            result.comparison_status
        ),
        "raw_prices_compared_directly": False,
        "normalized_scoring_used": True,
        "expired_candidate_ineligible": True,
        "unverified_venue_ineligible": True,
        "all_ineligible_best_venue": (
            ineligible.best_venue_id
        ),
        "venue_ranked_as_intelligence": (
            result.venue_ranked_as_intelligence
        ),
        "read_only": result.read_only,
        "execution_allowed": result.execution_allowed,
        "execution_adapter_resolved": (
            result.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            result.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            result.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            result.order_placement_allowed
        ),
        "funds_moved": result.funds_moved,
        "portfolio_mutated": result.portfolio_mutated,
    }

    print(
        "[PASS] OLA-006 Oracle Canonical Cross-Venue "
        "Opportunity Comparison Engine"
    )

    print(output)


if __name__ == "__main__":
    main()
