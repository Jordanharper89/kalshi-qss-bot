from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition import (
    OpportunityValidityContractError,
    OpportunityValidityRequest,
    OracleCanonicalOpportunityValidityExpirationEngine,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    22,
    15,
    0,
    tzinfo=timezone.utc,
)

VALID_FROM = datetime(
    2026,
    7,
    11,
    22,
    15,
    5,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    11,
    22,
    25,
    0,
    tzinfo=timezone.utc,
)

ACTIVE_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    18,
    0,
    tzinfo=timezone.utc,
)

PENDING_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    15,
    1,
    tzinfo=timezone.utc,
)

EXPIRED_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    25,
    0,
    tzinfo=timezone.utc,
)


def build_request():
    return OpportunityValidityRequest.create(
        opportunity_id="opportunity.test.001",
        canonical_market_id=(
            "market."
            "95b13d7489267bf051b0173a27c3e98b"
            "155473362c6ca4e47431a16e623044ab"
        ),
        venue_id="venue.kalshi",
        opportunity_type="prediction_market",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_policy_id=(
            "oracle.validity.prediction_market.v1"
        ),
        source_record_hash="source-record-hash-001",
        metadata={
            "share_side": "yes",
            "reference_price": "0.31",
            "timezone_display_required": True,
        },
    )


def build_engine():
    return (
        OracleCanonicalOpportunityValidityExpirationEngine()
    )


def run_active_test():
    engine = build_engine()
    request = build_request()

    first = engine.evaluate(
        request=request,
        evaluated_at=ACTIVE_EVALUATED_AT,
        replay_metadata={
            "replay_source": "opportunity_validity",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-005",
            "operator": "automated_runtime",
        },
    )

    second = build_engine().evaluate(
        request=build_request(),
        evaluated_at=ACTIVE_EVALUATED_AT,
        replay_metadata={
            "replay_source": "opportunity_validity",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-005",
            "operator": "automated_runtime",
        },
    )

    assert first == second

    assert first.schema_version == "OLA-005"
    assert first.engine_id == "OLA-005"

    assert first.opportunity_id == (
        "opportunity.test.001"
    )

    assert first.venue_id == "venue.kalshi"

    assert first.opportunity_type == (
        "prediction_market"
    )

    assert first.validity_status == "active"
    assert first.freshness_status == "fresh"

    assert first.active is True
    assert first.expired is False
    assert first.future_validity is False

    assert (
        first.seconds_until_expiration
        == 420
    )

    assert (
        "opportunity_active"
        in first.reason_codes
    )

    assert (
        "within_validity_window"
        in first.reason_codes
    )

    assert first.observation_date_utc == "2026-07-11"

    assert (
        first.expiration_date_utc
        == "2026-07-11"
    )

    assert first.immutable is True
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

    assert (
        first.validity_evidence_hash
        == second.validity_evidence_hash
    )

    try:
        first.active = False

        raise AssertionError(
            "validity evidence must be immutable"
        )

    except FrozenInstanceError:
        pass

    return first


def run_pending_test():
    result = build_engine().evaluate(
        request=build_request(),
        evaluated_at=PENDING_EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.validity_status == "pending"

    assert (
        result.freshness_status
        == "not_yet_valid"
    )

    assert result.active is False
    assert result.expired is False
    assert result.future_validity is True

    assert (
        "opportunity_not_yet_valid"
        in result.reason_codes
    )

    return result


def run_expired_test():
    result = build_engine().evaluate(
        request=build_request(),
        evaluated_at=EXPIRED_EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.validity_status == "expired"

    assert result.freshness_status == "expired"

    assert result.active is False
    assert result.expired is True
    assert result.future_validity is False

    assert result.seconds_until_expiration == 0

    assert (
        "expiration_boundary_reached"
        in result.reason_codes
    )

    assert (
        "opportunity_expired"
        in result.reason_codes
    )

    return result


def run_fail_closed_tests():
    try:
        OpportunityValidityRequest.create(
            opportunity_id="bad-opportunity",
            canonical_market_id="market.test",
            venue_id="venue.test",
            opportunity_type="prediction_market",
            observed_at=OBSERVED_AT,
            valid_from=VALID_FROM,
            expires_at=VALID_FROM,
            validity_policy_id="policy.test",
            source_record_hash="hash.test",
            metadata={},
        )

        raise AssertionError(
            "zero-length validity window must fail closed"
        )

    except OpportunityValidityContractError:
        pass

    try:
        OpportunityValidityRequest.create(
            opportunity_id="bad-opportunity",
            canonical_market_id="market.test",
            venue_id="venue.test",
            opportunity_type="prediction_market",
            observed_at=OBSERVED_AT,
            valid_from=datetime(
                2026,
                7,
                11,
                22,
                14,
                59,
                tzinfo=timezone.utc,
            ),
            expires_at=EXPIRES_AT,
            validity_policy_id="policy.test",
            source_record_hash="hash.test",
            metadata={},
        )

        raise AssertionError(
            "valid_from before observed_at must fail closed"
        )

    except OpportunityValidityContractError:
        pass

    try:
        build_engine().evaluate(
            request=build_request(),
            evaluated_at=datetime(
                2026,
                7,
                11,
                22,
                18,
                0,
            ),
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "naive evaluated_at must fail closed"
        )

    except OpportunityValidityContractError:
        pass


def main():
    active = run_active_test()
    pending = run_pending_test()
    expired = run_expired_test()

    run_fail_closed_tests()

    result = {
        "schema_version": active.schema_version,
        "engine_id": active.engine_id,
        "status": "passed",
        "opportunity_id": active.opportunity_id,
        "canonical_market_id": (
            active.canonical_market_id
        ),
        "venue_id": active.venue_id,
        "opportunity_type": active.opportunity_type,
        "active_status": active.validity_status,
        "pending_status": pending.validity_status,
        "expired_status": expired.validity_status,
        "active": active.active,
        "expiration_boundary_expired": (
            expired.expired
        ),
        "explicit_valid_from": (
            active.valid_from.isoformat()
        ),
        "explicit_expires_at": (
            active.expires_at.isoformat()
        ),
        "date_time_evidence_present": True,
        "deterministic_hash": True,
        "read_only": active.read_only,
        "execution_allowed": active.execution_allowed,
        "trade_authorization_allowed": (
            active.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            active.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            active
            .execution_adapter_invocation_allowed
        ),
        "funds_moved": active.funds_moved,
        "portfolio_mutated": active.portfolio_mutated,
    }

    print(
        "[PASS] OLA-005 Oracle Canonical Opportunity "
        "Validity and Expiration Engine"
    )

    print(result)


if __name__ == "__main__":
    main()
