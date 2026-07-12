from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition import (
    ApprovedVenueRegistration,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    SourceMarketIdentityEvidence,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    22,
    10,
    0,
    tzinfo=timezone.utc,
)

RESOLVED_AT = datetime(
    2026,
    7,
    11,
    22,
    10,
    1,
    tzinfo=timezone.utc,
)


def build_engine():
    kalshi = ApprovedVenueRegistration.create(
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        source_ids=(
            "source.kalshi.market_data",
        ),
        registration_metadata={
            "approved": True,
            "market_identity_required": True,
        },
    )

    coinbase = ApprovedVenueRegistration.create(
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        source_ids=(
            "source.coinbase.market_data",
        ),
        registration_metadata={
            "approved": True,
            "market_identity_required": True,
        },
    )

    return (
        OracleCanonicalMarketIdentityVenueResolutionEngine(
            approved_venues=(
                kalshi,
                coinbase,
            ),
        )
    )


def build_kalshi_evidence():
    return SourceMarketIdentityEvidence.create(
        source_id="source.kalshi.market_data",
        source_market_id="KXBTC-26JUL11-116000",
        source_symbol="KXBTC-26JUL11-116000",
        instrument_type="prediction_contract",
        market_title="Bitcoin below 116000 by 5 PM",
        venue_claim="venue.kalshi",
        identity_metadata={
            "settlement_currency": "USD",
            "contract_sides": ["yes", "no"],
        },
        observed_at=OBSERVED_AT,
    )


def run_verified_resolution_test():
    engine = build_engine()

    evidence = build_kalshi_evidence()

    first = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    second = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    identity = first.canonical_market_identity
    venue = first.venue_resolution

    assert first.schema_version == "OLA-004"
    assert first.engine_id == "OLA-004"

    assert identity.source_id == (
        "source.kalshi.market_data"
    )

    assert identity.source_market_id == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.source_symbol == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.instrument_type == (
        "prediction_contract"
    )

    assert identity.canonical_market_id.startswith(
        "market."
    )

    assert identity.immutable is True
    assert identity.read_only is True

    assert venue.resolution_status == "verified"
    assert venue.venue_verified is True
    assert venue.venue_id == "venue.kalshi"
    assert venue.venue_name == "Kalshi"

    assert venue.default_venue_used is False
    assert venue.fallback_adapter_used is False

    assert (
        venue.execution_adapter_resolved
        is False
    )

    assert first.record_hash == second.record_hash

    assert (
        first.canonical_market_identity.identity_hash
        == second.canonical_market_identity.identity_hash
    )

    assert (
        first.venue_resolution.resolution_hash
        == second.venue_resolution.resolution_hash
    )

    assert first.replayable is True
    assert first.auditable is True
    assert first.explainable is True

    assert first.read_only is True
    assert first.execution_allowed is False

    assert (
        first.trade_authorization_allowed
        is False
    )

    assert first.order_placement_allowed is False

    assert (
        first.execution_adapter_invocation_allowed
        is False
    )

    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    try:
        venue.venue_id = "venue.coinbase"
        raise AssertionError(
            "venue resolution must be immutable"
        )
    except FrozenInstanceError:
        pass

    return first


def run_unresolved_fail_closed_test():
    engine = build_engine()

    evidence = SourceMarketIdentityEvidence.create(
        source_id="source.unknown.market_data",
        source_market_id="UNKNOWN-1",
        source_symbol="UNKNOWN-1",
        instrument_type="prediction_contract",
        market_title="Unknown source market",
        venue_claim="venue.unknown",
        identity_metadata={},
        observed_at=OBSERVED_AT,
    )

    record = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    venue = record.venue_resolution

    assert venue.resolution_status == "unresolved"
    assert venue.venue_verified is False

    assert venue.venue_id is None
    assert venue.venue_name is None
    assert venue.venue_type is None

    assert venue.default_venue_used is False
    assert venue.fallback_adapter_used is False

    assert (
        venue.execution_adapter_resolved
        is False
    )

    assert record.execution_allowed is False

    return record


def run_conflicting_claim_test():
    engine = build_engine()

    evidence = SourceMarketIdentityEvidence.create(
        source_id="source.kalshi.market_data",
        source_market_id="KXBTC-CONFLICT",
        source_symbol="KXBTC-CONFLICT",
        instrument_type="prediction_contract",
        market_title="Conflicting venue claim",
        venue_claim="venue.coinbase",
        identity_metadata={},
        observed_at=OBSERVED_AT,
    )

    record = engine.resolve(
        evidence=evidence,
        resolved_at=RESOLVED_AT,
    )

    venue = record.venue_resolution

    assert venue.resolution_status == "unresolved"
    assert venue.venue_verified is False
    assert venue.venue_id is None

    assert (
        "approved_venue_match_not_found"
        in venue.reason_codes
    )

    return record


def run_timestamp_fail_closed_test():
    engine = build_engine()

    evidence = build_kalshi_evidence()

    try:
        engine.resolve(
            evidence=evidence,
            resolved_at=datetime(
                2026,
                7,
                11,
                22,
                10,
                1,
            ),
        )

        raise AssertionError(
            "naive resolved_at must fail closed"
        )
    except ValueError:
        pass


def main():
    verified = run_verified_resolution_test()
    unresolved = run_unresolved_fail_closed_test()
    conflicting = run_conflicting_claim_test()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": verified.schema_version,
        "engine_id": verified.engine_id,
        "status": "passed",
        "canonical_market_id": (
            verified
            .canonical_market_identity
            .canonical_market_id
        ),
        "venue_resolution_status": (
            verified
            .venue_resolution
            .resolution_status
        ),
        "venue_id": (
            verified
            .venue_resolution
            .venue_id
        ),
        "venue_verified": (
            verified
            .venue_resolution
            .venue_verified
        ),
        "unresolved_market_blocked": (
            unresolved
            .venue_resolution
            .venue_verified
            is False
        ),
        "conflicting_claim_blocked": (
            conflicting
            .venue_resolution
            .venue_verified
            is False
        ),
        "default_venue_used": (
            verified
            .venue_resolution
            .default_venue_used
        ),
        "fallback_adapter_used": (
            verified
            .venue_resolution
            .fallback_adapter_used
        ),
        "execution_adapter_resolved": (
            verified
            .venue_resolution
            .execution_adapter_resolved
        ),
        "read_only": verified.read_only,
        "execution_allowed": (
            verified.execution_allowed
        ),
        "trade_authorization_allowed": (
            verified.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            verified.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            verified
            .execution_adapter_invocation_allowed
        ),
        "funds_moved": verified.funds_moved,
        "portfolio_mutated": verified.portfolio_mutated,
    }

    print(
        "[PASS] OLA-004 Oracle Canonical Market "
        "Identity and Venue Resolution Engine"
    )

    print(result)


if __name__ == "__main__":
    main()
