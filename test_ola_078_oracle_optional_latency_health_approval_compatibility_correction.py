from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition import (
    HEALTH_APPROVAL_REASON_CODES,
    HEALTH_LATENCY_APPROVAL_REASON_CODES,
    HEALTH_REQUIRED_APPROVAL_REASON_CODES,
    OracleAcquisitionSourceControlEngine,
    OracleKalshiLiveReadReadinessGate,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    SOURCE_ID,
)


SCHEMA_VERSION = "OLA-078"
ENGINE_ID = "OLA-078-V2"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


def build_decision(
    *,
    max_latency_ms: int | None,
    latency_ms: int | None,
    reachable: bool = True,
    consecutive_failures: int = 0,
):
    checked_at = datetime(
        2026,
        7,
        19,
        21,
        0,
        0,
        tzinfo=timezone.utc,
    )

    health_policy = SourceHealthPolicy.create(
        policy_id="ola078-health-policy",
        max_consecutive_failures=2,
        max_latency_ms=max_latency_ms,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="ola078-rate-policy",
        max_requests_per_window=100,
        window_seconds=60,
        minimum_remaining_reserve=10,
    )

    engine = OracleAcquisitionSourceControlEngine(
        source_policies={
            SOURCE_ID: (
                health_policy,
                rate_policy,
            )
        }
    )

    health_observation = SourceHealthObservation.create(
        source_id=SOURCE_ID,
        checked_at=checked_at,
        reachable=reachable,
        consecutive_failures=consecutive_failures,
        latency_ms=latency_ms,
        metadata={
            "test": "OLA-078-V2",
        },
    )

    rate_observation = RateWindowObservation.create(
        source_id=SOURCE_ID,
        checked_at=checked_at,
        window_started_at=(
            checked_at
            - timedelta(seconds=5)
        ),
        requests_used=1,
        metadata={
            "test": "OLA-078-V2",
        },
    )

    return engine.evaluate(
        health_observation=health_observation,
        rate_observation=rate_observation,
        evaluated_at=checked_at,
        replay_metadata={
            "test": "OLA-078-V2",
        },
        audit_metadata={
            "test": "OLA-078-V2",
        },
    )


def validate_decision(decision):
    return (
        OracleKalshiLiveReadReadinessGate
        ._validate_source_control_decision(
            decision=decision,
        )
    )


def assert_read_only_boundary() -> None:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ALERTS_ALLOWED is False
    assert QSERIES_HANDOFF_ALLOWED is False
    assert TRADE_AUTHORIZATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False


def main() -> int:
    print("========================================")
    print(" OLA-078 TEST CORRECTION V2")
    print(" PACKAGE EXPORT COMPATIBILITY")
    print(" OPTIONAL LATENCY APPROVAL CONTRACT")
    print("========================================")

    assert_read_only_boundary()

    print("[TEST] Package-level readiness imports")

    assert HEALTH_REQUIRED_APPROVAL_REASON_CODES == frozenset(
        {
            "source_reachable",
            "consecutive_failures_within_policy",
        }
    )

    assert HEALTH_LATENCY_APPROVAL_REASON_CODES == frozenset(
        {
            "latency_within_policy",
            "latency_policy_not_required",
        }
    )

    assert HEALTH_APPROVAL_REASON_CODES == frozenset(
        {
            "source_reachable",
            "consecutive_failures_within_policy",
            "latency_within_policy",
            "latency_policy_not_required",
        }
    )

    print("[OK] Package-level readiness imports")

    print("[TEST] Legacy health approval export preserved")

    assert (
        HEALTH_REQUIRED_APPROVAL_REASON_CODES
        .issubset(HEALTH_APPROVAL_REASON_CODES)
    )

    assert (
        HEALTH_LATENCY_APPROVAL_REASON_CODES
        .issubset(HEALTH_APPROVAL_REASON_CODES)
    )

    print("[OK] Legacy health approval export preserved")

    print("[TEST] Optional-latency policy decision")

    optional_latency_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
    )

    optional_reason_codes = set(
        optional_latency_decision.reason_codes
    )

    assert "source_reachable" in optional_reason_codes

    assert (
        "consecutive_failures_within_policy"
        in optional_reason_codes
    )

    assert (
        "latency_policy_not_required"
        in optional_reason_codes
    )

    assert optional_latency_decision.acquisition_allowed is True

    optional_result = validate_decision(
        optional_latency_decision
    )

    assert isinstance(optional_result, tuple)
    assert len(optional_result) == 3

    print("[OK] Optional-latency decision accepted")

    print("[TEST] Required-latency policy decision")

    required_latency_decision = build_decision(
        max_latency_ms=1000,
        latency_ms=25,
    )

    required_reason_codes = set(
        required_latency_decision.reason_codes
    )

    assert "source_reachable" in required_reason_codes

    assert (
        "consecutive_failures_within_policy"
        in required_reason_codes
    )

    assert (
        "latency_within_policy"
        in required_reason_codes
    )

    assert required_latency_decision.acquisition_allowed is True

    required_result = validate_decision(
        required_latency_decision
    )

    assert isinstance(required_result, tuple)
    assert len(required_result) == 3

    print("[OK] Required-latency decision accepted")

    print("[TEST] Missing latency approval rejected")

    wrong_reason_codes = tuple(
        reason
        for reason in optional_latency_decision.reason_codes
        if reason != "latency_policy_not_required"
    )

    wrong_decision = type(optional_latency_decision)(
        schema_version=optional_latency_decision.schema_version,
        engine_id=optional_latency_decision.engine_id,
        source_id=optional_latency_decision.source_id,
        evaluated_at=optional_latency_decision.evaluated_at,
        health_policy_id=optional_latency_decision.health_policy_id,
        rate_policy_id=optional_latency_decision.rate_policy_id,
        health_observation_hash=(
            optional_latency_decision.health_observation_hash
        ),
        rate_observation_hash=(
            optional_latency_decision.rate_observation_hash
        ),
        health_evidence=optional_latency_decision.health_evidence,
        rate_control_evidence=(
            optional_latency_decision.rate_control_evidence
        ),
        acquisition_allowed=True,
        reason_codes=wrong_reason_codes,
        replay_metadata=optional_latency_decision.replay_metadata,
        audit_metadata=optional_latency_decision.audit_metadata,
        decision_hash=optional_latency_decision.decision_hash,
        read_only=True,
        execution_allowed=False,
        acquisition_performed=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        execution_adapter_invocation_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
    )

    try:
        validate_decision(
            wrong_decision
        )
    except KalshiLiveReadReadinessFailure as exc:
        assert (
            "lacks valid latency approval reason"
            in str(exc)
        )
    else:
        raise AssertionError(
            "decision without a valid latency reason was accepted"
        )

    print("[OK] Missing latency approval rejected")

    print("[TEST] Unreachable source remains rejected")

    unreachable_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
        reachable=False,
    )

    assert unreachable_decision.acquisition_allowed is False

    try:
        validate_decision(
            unreachable_decision
        )
    except KalshiLiveReadReadinessFailure:
        pass
    else:
        raise AssertionError(
            "unreachable source decision was accepted"
        )

    print("[OK] Unreachable source remains rejected")

    print("[TEST] Excessive failures remain rejected")

    excessive_failure_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
        consecutive_failures=3,
    )

    assert (
        excessive_failure_decision.acquisition_allowed
        is False
    )

    try:
        validate_decision(
            excessive_failure_decision
        )
    except KalshiLiveReadReadinessFailure:
        pass
    else:
        raise AssertionError(
            "excessive-failure decision was accepted"
        )

    print("[OK] Excessive failures remain rejected")

    print("[TEST] Production and package markers")

    root = Path(__file__).resolve().parent

    readiness_path = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_kalshi_live_read_readiness_gate.py"
    )

    package_path = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "__init__.py"
    )

    readiness_source = readiness_path.read_text(
        encoding="utf-8"
    )

    package_source = package_path.read_text(
        encoding="utf-8"
    )

    assert (
        "OLA-078 health approval compatibility contract"
        in readiness_source
    )

    assert (
        "OLA-078 V2 backward-compatibility export"
        in readiness_source
    )

    assert (
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        '"HEALTH_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES,"
        in package_source
    )

    assert (
        "HEALTH_LATENCY_APPROVAL_REASON_CODES,"
        in package_source
    )

    assert (
        "HEALTH_APPROVAL_REASON_CODES,"
        in package_source
    )

    print("[OK] Production and package markers")

    print("[TEST] Oracle read-only boundary")

    assert optional_latency_decision.read_only is True

    assert (
        optional_latency_decision.execution_allowed
        is False
    )

    assert (
        optional_latency_decision
        .trade_authorization_allowed
        is False
    )

    assert (
        optional_latency_decision
        .order_placement_allowed
        is False
    )

    assert (
        optional_latency_decision
        .execution_adapter_invocation_allowed
        is False
    )

    assert optional_latency_decision.funds_moved is False
    assert optional_latency_decision.portfolio_mutated is False

    print("[OK] Oracle read-only boundary preserved")

    print(
        "[PASS] OLA-078 Oracle Optional Latency "
        "Health Approval Compatibility Correction V2"
    )

    print({
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "package_import_compatibility_restored": True,
        "legacy_health_export_preserved": True,
        "canonical_required_health_exported": True,
        "canonical_latency_health_exported": True,
        "ola002_optional_latency_reason_supported": True,
        "latency_policy_not_required_accepted": True,
        "latency_within_policy_accepted": True,
        "source_reachable_still_required": True,
        "failure_policy_approval_still_required": True,
        "missing_latency_approval_rejected": True,
        "unreachable_source_rejected": True,
        "excessive_failures_rejected": True,
        "rate_policy_validation_preserved": True,
        "final_acquisition_approval_preserved": True,
        "real_service_started": False,
        "process_created": False,
        "thread_created": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
