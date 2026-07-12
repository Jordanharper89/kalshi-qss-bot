from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    ComparisonScoringPolicy,
    CrossVenueOpportunityCandidate,
    OpportunityAlertContractError,
    OpportunityAlertSelectionError,
    OracleCanonicalCrossVenueOpportunityComparisonEngine,
    OracleCanonicalOpportunityAlertRecordEngine,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    23,
    0,
    0,
    tzinfo=timezone.utc,
)

VALID_FROM = datetime(
    2026,
    7,
    11,
    23,
    0,
    5,
    tzinfo=timezone.utc,
)

COMPARED_AT = datetime(
    2026,
    7,
    11,
    23,
    1,
    0,
    tzinfo=timezone.utc,
)

ALERT_CREATED_AT = datetime(
    2026,
    7,
    11,
    23,
    1,
    5,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    11,
    23,
    10,
    0,
    tzinfo=timezone.utc,
)


def build_policy():
    return ComparisonScoringPolicy.create(
        policy_id="oracle.cross_venue.alert.test.v1",
        component_weights={
            "expected_edge": Decimal("0.40"),
            "liquidity_quality": Decimal("0.20"),
            "thesis_alignment": Decimal("0.25"),
            "time_fit": Decimal("0.15"),
        },
    )


def build_kalshi_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.kalshi.btc.alert.001",
        thesis_id="thesis.btc.bearish.alert.001",
        comparability_group_id=(
            "comparison.btc.bearish.alert"
        ),
        canonical_market_id="market.kalshi.btc.alert.001",
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.31",
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="record.kalshi.alert.001",
        validity_evidence_hash="validity.kalshi.alert.001",
        normalized_components={
            "expected_edge": "0.95",
            "liquidity_quality": "0.79",
            "thesis_alignment": "0.97",
            "time_fit": "0.91",
        },
        metadata={
            "share_side": "yes",
            "market_title": (
                "Bitcoin below 116000 by 5 PM"
            ),
        },
    )


def build_coinbase_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.coinbase.btc.alert.001",
        thesis_id="thesis.btc.bearish.alert.001",
        comparability_group_id=(
            "comparison.btc.bearish.alert"
        ),
        canonical_market_id="market.coinbase.btc.alert.001",
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell_or_short_thesis",
        direction="bearish",
        reference_price="117420",
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="record.coinbase.alert.001",
        validity_evidence_hash=(
            "validity.coinbase.alert.001"
        ),
        normalized_components={
            "expected_edge": "0.69",
            "liquidity_quality": "0.99",
            "thesis_alignment": "0.84",
            "time_fit": "0.73",
        },
        metadata={
            "asset": "BTC",
            "quote_asset": "USD",
        },
    )


def build_comparison():
    engine = (
        OracleCanonicalCrossVenueOpportunityComparisonEngine(
            scoring_policy=build_policy()
        )
    )

    return engine.compare(
        candidates=(
            build_kalshi_candidate(),
            build_coinbase_candidate(),
        ),
        compared_at=COMPARED_AT,
        replay_metadata={
            "replay_source": "ola_007_test",
        },
        audit_metadata={
            "request_id": "audit-ola-007-comparison",
        },
    )


def run_primary_alert_test():
    comparison = build_comparison()

    assert comparison.best_venue_id == "venue.kalshi"

    engine = OracleCanonicalOpportunityAlertRecordEngine()

    first = engine.create_alert(
        comparison=comparison,
        alert_created_at=ALERT_CREATED_AT,
        display_metadata={
            "display_timezone": "America/Chicago",
            "display_timezone_label": "CT",
            "date_required": True,
            "time_required": True,
            "venue_next_to_price_required": True,
        },
        replay_metadata={
            "replay_source": "canonical_alert_record",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-007",
            "operator": "automated_runtime",
        },
    )

    second = (
        OracleCanonicalOpportunityAlertRecordEngine()
        .create_alert(
            comparison=build_comparison(),
            alert_created_at=ALERT_CREATED_AT,
            display_metadata={
                "display_timezone": "America/Chicago",
                "display_timezone_label": "CT",
                "date_required": True,
                "time_required": True,
                "venue_next_to_price_required": True,
            },
            replay_metadata={
                "replay_source": "canonical_alert_record",
                "replay_version": 1,
            },
            audit_metadata={
                "request_id": "audit-ola-007",
                "operator": "automated_runtime",
            },
        )
    )

    assert first == second

    assert first.schema_version == "OLA-007"
    assert first.engine_id == "OLA-007"

    assert first.alert_id.startswith("alert.")

    assert first.opportunity_id == (
        "opportunity.kalshi.btc.alert.001"
    )

    assert first.thesis_id == (
        "thesis.btc.bearish.alert.001"
    )

    assert first.venue_id == "venue.kalshi"
    assert first.venue_name == "Kalshi"
    assert first.venue_type == "prediction_market"

    assert first.instrument_type == (
        "prediction_contract"
    )

    assert first.opportunity_type == (
        "prediction_market"
    )

    assert first.expression_type == "buy_yes"
    assert first.direction == "bearish"

    assert first.reference_price == "0.31"
    assert first.price_unit == "USD_PER_SHARE"

    assert first.source_expires_at == EXPIRES_AT

    assert first.alert_created_at == ALERT_CREATED_AT

    assert first.alert_date_utc == "2026-07-11"
    assert first.expiration_date_utc == "2026-07-11"

    assert first.seconds_until_expiration == 535

    assert first.alert_status == "active"
    assert first.freshness_status == "fresh"

    assert (
        "explicit_venue_identity_preserved"
        in first.reason_codes
    )

    assert (
        "venue_specific_price_preserved"
        in first.reason_codes
    )

    assert (
        "expiration_evidence_preserved"
        in first.reason_codes
    )

    assert first.alert_hash == second.alert_hash

    assert first.immutable is True
    assert first.replayable is True
    assert first.auditable is True
    assert first.explainable is True

    assert first.read_only is True
    assert first.execution_allowed is False

    assert first.execution_adapter_resolved is False
    assert first.execution_adapter_invoked is False

    assert (
        first.trade_authorization_allowed
        is False
    )

    assert first.order_placement_allowed is False
    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    try:
        first.venue_id = "venue.coinbase"

        raise AssertionError(
            "canonical alert record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return first


def run_expired_selection_fail_closed_test():
    comparison = build_comparison()

    try:
        (
            OracleCanonicalOpportunityAlertRecordEngine()
            .create_alert(
                comparison=comparison,
                alert_created_at=EXPIRES_AT,
                display_metadata={},
                replay_metadata={},
                audit_metadata={},
            )
        )

        raise AssertionError(
            "expired selection must fail closed"
        )

    except OpportunityAlertSelectionError:
        pass


def run_precomparison_timestamp_fail_closed_test():
    comparison = build_comparison()

    try:
        (
            OracleCanonicalOpportunityAlertRecordEngine()
            .create_alert(
                comparison=comparison,
                alert_created_at=OBSERVED_AT,
                display_metadata={},
                replay_metadata={},
                audit_metadata={},
            )
        )

        raise AssertionError(
            "alert before comparison must fail closed"
        )

    except OpportunityAlertContractError:
        pass


def run_no_winner_fail_closed_test():
    expired_kalshi = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.expired.alert.001",
        thesis_id="thesis.expired.alert.001",
        comparability_group_id=(
            "comparison.expired.alert"
        ),
        canonical_market_id="market.expired.alert.001",
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        instrument_type="prediction_contract",
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.31",
        price_unit="USD_PER_SHARE",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=COMPARED_AT,
        validity_status="expired",
        venue_verified=True,
        source_record_hash="record.expired",
        validity_evidence_hash="validity.expired",
        normalized_components={
            "expected_edge": "1.0",
            "liquidity_quality": "1.0",
            "thesis_alignment": "1.0",
            "time_fit": "1.0",
        },
        metadata={},
    )

    comparison = (
        OracleCanonicalCrossVenueOpportunityComparisonEngine(
            scoring_policy=build_policy()
        )
        .compare(
            candidates=(expired_kalshi,),
            compared_at=COMPARED_AT,
            replay_metadata={},
            audit_metadata={},
        )
    )

    assert comparison.best_opportunity_id is None

    try:
        (
            OracleCanonicalOpportunityAlertRecordEngine()
            .create_alert(
                comparison=comparison,
                alert_created_at=ALERT_CREATED_AT,
                display_metadata={},
                replay_metadata={},
                audit_metadata={},
            )
        )

        raise AssertionError(
            "comparison without winner must fail closed"
        )

    except OpportunityAlertSelectionError:
        pass


def run_tied_winner_fail_closed_test():
    candidate_one = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.tie.one",
        thesis_id="thesis.tie.001",
        comparability_group_id="comparison.tie.001",
        canonical_market_id="market.tie.one",
        venue_id="venue.one",
        venue_name="Venue One",
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
        source_record_hash="record.tie.one",
        validity_evidence_hash="validity.tie.one",
        normalized_components={
            "expected_edge": "0.80",
            "liquidity_quality": "0.80",
            "thesis_alignment": "0.80",
            "time_fit": "0.80",
        },
        metadata={},
    )

    candidate_two = CrossVenueOpportunityCandidate.create(
        opportunity_id="opportunity.tie.two",
        thesis_id="thesis.tie.001",
        comparability_group_id="comparison.tie.001",
        canonical_market_id="market.tie.two",
        venue_id="venue.two",
        venue_name="Venue Two",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell_or_short_thesis",
        direction="bearish",
        reference_price="117400",
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash="record.tie.two",
        validity_evidence_hash="validity.tie.two",
        normalized_components={
            "expected_edge": "0.80",
            "liquidity_quality": "0.80",
            "thesis_alignment": "0.80",
            "time_fit": "0.80",
        },
        metadata={},
    )

    comparison = (
        OracleCanonicalCrossVenueOpportunityComparisonEngine(
            scoring_policy=build_policy()
        )
        .compare(
            candidates=(
                candidate_one,
                candidate_two,
            ),
            compared_at=COMPARED_AT,
            replay_metadata={},
            audit_metadata={},
        )
    )

    assert comparison.tie_for_best is True

    try:
        (
            OracleCanonicalOpportunityAlertRecordEngine()
            .create_alert(
                comparison=comparison,
                alert_created_at=ALERT_CREATED_AT,
                display_metadata={},
                replay_metadata={},
                audit_metadata={},
            )
        )

        raise AssertionError(
            "tied best opportunities must fail closed"
        )

    except OpportunityAlertSelectionError:
        pass


def main():
    alert = run_primary_alert_test()

    run_expired_selection_fail_closed_test()
    run_precomparison_timestamp_fail_closed_test()
    run_no_winner_fail_closed_test()
    run_tied_winner_fail_closed_test()

    result = {
        "schema_version": alert.schema_version,
        "engine_id": alert.engine_id,
        "status": "passed",
        "alert_id": alert.alert_id,
        "opportunity_id": alert.opportunity_id,
        "thesis_id": alert.thesis_id,
        "canonical_market_id": (
            alert.canonical_market_id
        ),
        "venue_id": alert.venue_id,
        "venue_name": alert.venue_name,
        "venue_type": alert.venue_type,
        "instrument_type": alert.instrument_type,
        "opportunity_type": alert.opportunity_type,
        "expression_type": alert.expression_type,
        "direction": alert.direction,
        "reference_price": alert.reference_price,
        "price_unit": alert.price_unit,
        "alert_status": alert.alert_status,
        "freshness_status": alert.freshness_status,
        "explicit_date_time": True,
        "explicit_expiration": True,
        "venue_specific_price_preserved": True,
        "tied_winner_blocked": True,
        "expired_selection_blocked": True,
        "no_winner_blocked": True,
        "read_only": alert.read_only,
        "execution_allowed": alert.execution_allowed,
        "execution_adapter_resolved": (
            alert.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            alert.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            alert.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            alert.order_placement_allowed
        ),
        "funds_moved": alert.funds_moved,
        "portfolio_mutated": alert.portfolio_mutated,
    }

    print(
        "[PASS] OLA-007 Oracle Canonical Opportunity "
        "Alert Record Engine"
    )

    print(result)


if __name__ == "__main__":
    main()
