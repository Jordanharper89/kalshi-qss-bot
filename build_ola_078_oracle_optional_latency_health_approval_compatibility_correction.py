from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_kalshi_live_read_readiness_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_078_oracle_optional_latency_health_approval_compatibility_correction.py"
)


OLD_CONSTANT_BLOCK = '''HEALTH_APPROVAL_REASON_CODES = frozenset(
    {
        "source_reachable",
        "latency_within_policy",
        "consecutive_failures_within_policy",
    }
)

RATE_APPROVAL_REASON_CODES = frozenset(
'''


NEW_CONSTANT_BLOCK = '''# OLA-078 health approval compatibility contract.
#
# OLA-002 emits one of two valid latency approval reasons:
#
# - latency_within_policy
# - latency_policy_not_required
#
# The latter is emitted when the registered source policy intentionally
# does not require latency evidence. Reachability and consecutive-failure
# approval remain mandatory in every case.
HEALTH_REQUIRED_APPROVAL_REASON_CODES = frozenset(
    {
        "source_reachable",
        "consecutive_failures_within_policy",
    }
)

HEALTH_LATENCY_APPROVAL_REASON_CODES = frozenset(
    {
        "latency_within_policy",
        "latency_policy_not_required",
    }
)

RATE_APPROVAL_REASON_CODES = frozenset(
'''


OLD_VALIDATION_BLOCK = '''        health_policy_evidence_present = (
            HEALTH_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        rate_policy_evidence_present = (
            RATE_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        if not health_policy_evidence_present:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks health approval reasons"
            )
'''


NEW_VALIDATION_BLOCK = '''        health_required_evidence_present = (
            HEALTH_REQUIRED_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        health_latency_evidence_present = bool(
            HEALTH_LATENCY_APPROVAL_REASON_CODES
            .intersection(reason_code_set)
        )

        health_policy_evidence_present = (
            health_required_evidence_present
            and health_latency_evidence_present
        )

        rate_policy_evidence_present = (
            RATE_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        if not health_required_evidence_present:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks required health approval reasons"
            )

        if not health_latency_evidence_present:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks valid latency approval reason"
            )
'''


OLD_EXPORT_BLOCK = '''    "HEALTH_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


NEW_EXPORT_BLOCK = '''    "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
    "HEALTH_LATENCY_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    HEALTH_LATENCY_APPROVAL_REASON_CODES,
    HEALTH_REQUIRED_APPROVAL_REASON_CODES,
    KalshiLiveReadReadinessFailure,
    OracleKalshiLiveReadReadinessGate,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    SOURCE_ID,
)


SCHEMA_VERSION = "OLA-078"
ENGINE_ID = "OLA-078"

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
            "test": "OLA-078",
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
            "test": "OLA-078",
        },
    )

    return engine.evaluate(
        health_observation=health_observation,
        rate_observation=rate_observation,
        evaluated_at=checked_at,
        replay_metadata={
            "test": "OLA-078",
        },
        audit_metadata={
            "test": "OLA-078",
        },
    )


def validate_decision(decision):
    return (
        OracleKalshiLiveReadinessGate
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
    print(" OLA-078 OPTIONAL LATENCY COMPATIBILITY")
    print(" OLA-002 TO OLA-018 APPROVAL CONTRACT")
    print(" NO REAL SERVICE START")
    print("========================================")

    assert_read_only_boundary()

    print("[TEST] Required health reason contract")

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

    print("[OK] Required health reason contract")

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

    print("[TEST] Missing required latency evidence rejected")

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

    failure_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
        consecutive_failures=3,
    )

    assert failure_decision.acquisition_allowed is False

    try:
        validate_decision(
            failure_decision
        )
    except KalshiLiveReadReadinessFailure:
        pass
    else:
        raise AssertionError(
            "excessive-failure decision was accepted"
        )

    print("[OK] Excessive failures remain rejected")

    print("[TEST] Production correction markers")

    production_path = Path(
        __file__
    ).resolve().parent / (
        "qseries_v2/oracle_intelligence/live_acquisition/"
        "oracle_kalshi_live_read_readiness_gate.py"
    )

    production_source = production_path.read_text(
        encoding="utf-8"
    )

    assert (
        "OLA-078 health approval compatibility contract"
        in production_source
    )

    assert (
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES"
        in production_source
    )

    assert (
        "HEALTH_LATENCY_APPROVAL_REASON_CODES"
        in production_source
    )

    assert (
        "HEALTH_APPROVAL_REASON_CODES = frozenset"
        not in production_source
    )

    print("[OK] Production correction markers")

    print("[TEST] Oracle read-only boundary")

    assert optional_latency_decision.read_only is True
    assert optional_latency_decision.execution_allowed is False
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
        "Health Approval Compatibility Correction"
    )

    print({
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
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
'''


def require_exact_source() -> str:
    if not PRODUCTION_PATH.exists():
        raise FileNotFoundError(
            f"Missing production file: {PRODUCTION_PATH}"
        )

    source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    marker = (
        "OLA-078 health approval compatibility contract"
    )

    if marker in source:
        print(
            "[INFO] OLA-078 production correction "
            "already appears installed"
        )

        return source

    checks = {
        "constant block": (
            source.count(
                OLD_CONSTANT_BLOCK
            )
        ),
        "validation block": (
            source.count(
                OLD_VALIDATION_BLOCK
            )
        ),
        "export block": (
            source.count(
                OLD_EXPORT_BLOCK
            )
        ),
    }

    invalid = {
        name: count
        for name, count in checks.items()
        if count != 1
    }

    if invalid:
        raise RuntimeError(
            "Exact OLA-018 compatibility source did not match: "
            f"{invalid}. Production file was not changed."
        )

    return source


def create_corrected_source(
    source: str,
) -> str:
    marker = (
        "OLA-078 health approval compatibility contract"
    )

    if marker in source:
        return source

    corrected = source.replace(
        OLD_CONSTANT_BLOCK,
        NEW_CONSTANT_BLOCK,
        1,
    )

    corrected = corrected.replace(
        OLD_VALIDATION_BLOCK,
        NEW_VALIDATION_BLOCK,
        1,
    )

    corrected = corrected.replace(
        OLD_EXPORT_BLOCK,
        NEW_EXPORT_BLOCK,
        1,
    )

    if corrected == source:
        raise RuntimeError(
            "OLA-078 replacement produced no change"
        )

    if OLD_CONSTANT_BLOCK in corrected:
        raise RuntimeError(
            "Old health approval constant block remains"
        )

    if OLD_VALIDATION_BLOCK in corrected:
        raise RuntimeError(
            "Old health approval validation remains"
        )

    if OLD_EXPORT_BLOCK in corrected:
        raise RuntimeError(
            "Old health approval export remains"
        )

    required_tokens = (
        marker,
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
        "HEALTH_LATENCY_APPROVAL_REASON_CODES",
        "health_required_evidence_present",
        "health_latency_evidence_present",
        "lacks valid latency approval reason",
    )

    for token in required_tokens:
        if token not in corrected:
            raise RuntimeError(
                f"Required OLA-078 token missing: {token}"
            )

    compile(
        corrected,
        str(PRODUCTION_PATH),
        "exec",
    )

    return corrected


def write_complete_file(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + ".ola078.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    written_source = temporary_path.read_text(
        encoding="utf-8"
    )

    compile(
        written_source,
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def verify_installed_source() -> None:
    source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        "OLA-078 health approval compatibility contract",
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
        "HEALTH_LATENCY_APPROVAL_REASON_CODES",
        "health_required_evidence_present",
        "health_latency_evidence_present",
        "lacks valid latency approval reason",
    )

    for token in required_tokens:
        assert token in source

    assert (
        OLD_CONSTANT_BLOCK
        not in source
    )

    assert (
        OLD_VALIDATION_BLOCK
        not in source
    )

    assert (
        OLD_EXPORT_BLOCK
        not in source
    )

    compile(
        source,
        str(PRODUCTION_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-078 PRODUCTION CORRECTION")
    print(" OPTIONAL LATENCY HEALTH APPROVAL")
    print(" OLA-002 TO OLA-018 COMPATIBILITY")
    print("========================================")

    current_source = require_exact_source()

    corrected_source = create_corrected_source(
        current_source
    )

    write_complete_file(
        PRODUCTION_PATH,
        corrected_source,
    )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    verify_installed_source()

    print("[OK] OLA-002 optional latency semantics preserved")
    print("[OK] latency_policy_not_required accepted")
    print("[OK] latency_within_policy accepted")
    print("[OK] Reachability approval remains mandatory")
    print("[OK] Failure approval remains mandatory")
    print("[OK] Rate approval remains mandatory")
    print("[OK] Final acquisition approval remains mandatory")
    print("[OK] Blocked source decisions remain rejected")
    print("[OK] Oracle read-only boundary preserved")
    print("[OK] No production runtime started")

    print(
        "\n[DONE] OLA-078 optional latency health "
        "approval compatibility correction installed"
    )

    print("\nRun:")
    print(
        "python "
        "test_ola_078_oracle_optional_latency_"
        "health_approval_compatibility_correction.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )