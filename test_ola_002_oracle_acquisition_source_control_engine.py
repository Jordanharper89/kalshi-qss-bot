from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceControlContractError,
    SourceControlPolicyError,
    SourceHealthObservation,
    SourceHealthPolicy,
)


EVALUATED_AT = datetime(
    2026,
    7,
    11,
    21,
    0,
    0,
    tzinfo=timezone.utc,
)

CHECKED_AT = datetime(
    2026,
    7,
    11,
    20,
    59,
    55,
    tzinfo=timezone.utc,
)

WINDOW_STARTED_AT = datetime(
    2026,
    7,
    11,
    20,
    59,
    0,
    tzinfo=timezone.utc,
)


def build_engine():
    health_policy = SourceHealthPolicy.create(
        policy_id="health.test.market.v1",
        healthy_status="healthy",
        unhealthy_status="unhealthy",
        max_consecutive_failures=0,
        max_latency_ms=250,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="rate.test.market.v1",
        max_requests_per_window=100,
        window_seconds=60,
        minimum_remaining_reserve=5,
    )

    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.test.market": (
                health_policy,
                rate_policy,
            ),
        }
    )


def build_healthy_observation():
    return SourceHealthObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        reachable=True,
        consecutive_failures=0,
        latency_ms=42,
        metadata={
            "probe_id": "probe-test-1",
            "transport": "https",
        },
    )


def build_rate_observation(
    *,
    requests_used=20,
):
    return RateWindowObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        window_started_at=WINDOW_STARTED_AT,
        requests_used=requests_used,
        metadata={
            "counter_id": "counter-test-1",
        },
    )


def run_primary_contract_test():
    engine = build_engine()

    first = engine.evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={
            "replay_source": "source_control",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-002",
            "operator": "automated_runtime",
        },
    )

    second = build_engine().evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={
            "replay_source": "source_control",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-002",
            "operator": "automated_runtime",
        },
    )

    assert first == second
    assert first.decision_hash == second.decision_hash

    assert first.schema_version == "OLA-002"
    assert first.engine_id == "OLA-002"
    assert first.source_id == "source.test.market"

    assert first.acquisition_allowed is True

    assert (
        first.health_evidence.status
        == "healthy"
    )

    assert (
        first.rate_control_evidence.allowed
        is True
    )

    assert (
        first.health_evidence.source_id
        == "source.test.market"
    )

    assert (
        first.rate_control_evidence.source_id
        == "source.test.market"
    )

    assert first.read_only is True
    assert first.execution_allowed is False
    assert first.acquisition_performed is False
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

    assert "acquisition_allowed" in first.reason_codes
    assert "source_reachable" in first.reason_codes
    assert "latency_within_policy" in first.reason_codes
    assert "rate_reserve_preserved" in first.reason_codes

    try:
        first.acquisition_allowed = False
        raise AssertionError(
            "SourceControlDecisionRecord must be immutable"
        )
    except FrozenInstanceError:
        pass

    return first


def run_health_block_test():
    engine = build_engine()

    unhealthy = SourceHealthObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        reachable=False,
        consecutive_failures=1,
        latency_ms=None,
        metadata={},
    )

    result = engine.evaluate(
        health_observation=unhealthy,
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.acquisition_allowed is False
    assert result.health_evidence.status == "unhealthy"
    assert "source_unreachable" in result.reason_codes
    assert "acquisition_blocked" in result.reason_codes


def run_rate_block_test():
    engine = build_engine()

    result = engine.evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(
            requests_used=95
        ),
        evaluated_at=EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.acquisition_allowed is False
    assert result.rate_control_evidence.allowed is False
    assert (
        "rate_reserve_boundary_blocked"
        in result.reason_codes
    )
    assert "acquisition_blocked" in result.reason_codes


def run_fail_closed_tests():
    engine = build_engine()

    mismatched_rate = RateWindowObservation.create(
        source_id="source.other.market",
        checked_at=CHECKED_AT,
        window_started_at=WINDOW_STARTED_AT,
        requests_used=1,
        metadata={},
    )

    try:
        engine.evaluate(
            health_observation=build_healthy_observation(),
            rate_observation=mismatched_rate,
            evaluated_at=EVALUATED_AT,
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "source identity mismatch must fail closed"
        )
    except SourceControlContractError:
        pass

    expired_window = RateWindowObservation.create(
        source_id="source.test.market",
        checked_at=EVALUATED_AT,
        window_started_at=datetime(
            2026,
            7,
            11,
            20,
            58,
            59,
            tzinfo=timezone.utc,
        ),
        requests_used=1,
        metadata={},
    )

    try:
        engine.evaluate(
            health_observation=build_healthy_observation(),
            rate_observation=expired_window,
            evaluated_at=EVALUATED_AT,
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "expired rate windows must fail closed"
        )
    except SourceControlContractError:
        pass

    try:
        SourceHealthPolicy.create(
            policy_id="bad.health.policy",
            healthy_status="same",
            unhealthy_status="same",
        )
        raise AssertionError(
            "identical health statuses must fail closed"
        )
    except SourceControlPolicyError:
        pass

    try:
        RateControlPolicy.create(
            policy_id="bad.rate.policy",
            max_requests_per_window=10,
            window_seconds=60,
            minimum_remaining_reserve=10,
        )
        raise AssertionError(
            "invalid reserve policy must fail closed"
        )
    except SourceControlPolicyError:
        pass

    try:
        SourceHealthObservation.create(
            source_id="source.test.market",
            checked_at=datetime(
                2026,
                7,
                11,
                20,
                0,
                0,
            ),
            reachable=True,
            consecutive_failures=0,
            latency_ms=1,
            metadata={},
        )
        raise AssertionError(
            "naive timestamps must fail closed"
        )
    except SourceControlContractError:
        pass


def main():
    result = run_primary_contract_test()
    run_health_block_test()
    run_rate_block_test()
    run_fail_closed_tests()

    output = {
        "schema_version": result.schema_version,
        "engine_id": result.engine_id,
        "source_id": result.source_id,
        "acquisition_allowed": result.acquisition_allowed,
        "health_status": result.health_evidence.status,
        "rate_allowed": (
            result.rate_control_evidence.allowed
        ),
        "reason_codes": list(result.reason_codes),
        "read_only": result.read_only,
        "execution_allowed": result.execution_allowed,
        "acquisition_performed": (
            result.acquisition_performed
        ),
        "trade_authorization_allowed": (
            result.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            result.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            result.execution_adapter_invocation_allowed
        ),
        "funds_moved": result.funds_moved,
        "portfolio_mutated": result.portfolio_mutated,
    }

    print(
        "[PASS] OLA-002 "
        "Oracle Acquisition Source Control Engine"
    )
    print(output)


if __name__ == "__main__":
    main()
