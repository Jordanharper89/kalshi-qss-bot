from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
import runpy

from qseries_v2.oracle_intelligence.live_acquisition.oracle_readiness_recovery_bounded_repeatability_gate import (
    ALERTS_ALLOWED,
    CONTINUOUS_SERVICE_STARTED,
    ENGINE_ID,
    EXECUTION_ALLOWED,
    FUNDS_MOVED,
    ORDER_PLACEMENT_ALLOWED,
    PORTFOLIO_MUTATED,
    QSERIES_HANDOFF_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    TRADE_AUTHORIZATION_ALLOWED,
    OracleReadinessRecoveryBoundedRepeatabilityContractError,
    OracleReadinessRecoveryBoundedRepeatabilityFailure,
    evaluate_oracle_readiness_recovery_bounded_repeatability,
)


ROOT = Path(__file__).resolve().parent

OLA079_TEST_PATH = (
    ROOT
    / "test_ola_079_oracle_readiness_recovery_full_runner_iteration_gate.py"
)


def run_ola079_gate() -> int:
    namespace = runpy.run_path(
        str(OLA079_TEST_PATH),
        run_name="ola079_bounded_repeatability",
    )

    main_callable = namespace.get(
        "main"
    )

    if not callable(main_callable):
        raise AssertionError(
            "OLA-079 test must expose callable main"
        )

    result = main_callable()

    if result is None:
        return 0

    return result


def main() -> int:
    print("========================================")
    print(" OLA-080 BOUNDED REPEATABILITY GATE")
    print(" COMPLETE OLA-079 RECOVERY/RUNNER GATE")
    print(" CONTINUOUS SERVICE NOT STARTED")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-080"
    assert ENGINE_ID == "OLA-080"
    assert READ_ONLY is True
    assert CONTINUOUS_SERVICE_STARTED is False
    assert EXECUTION_ALLOWED is False
    assert ALERTS_ALLOWED is False
    assert QSERIES_HANDOFF_ALLOWED is False
    assert TRADE_AUTHORIZATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False

    assert OLA079_TEST_PATH.is_file(), (
        "OLA-079 test file is missing"
    )

    production_module = import_module(
        "qseries_v2.oracle_intelligence."
        "live_acquisition."
        "oracle_readiness_recovery_full_runner_iteration_gate"
    )

    assert getattr(
        production_module,
        "SCHEMA_VERSION",
        None,
    ) == "OLA-079"

    checked_at = datetime(
        2026,
        7,
        19,
        15,
        0,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(microseconds=1)
    )

    print(
        "[TEST] Repeat complete OLA-079 bounded gate "
        "three times"
    )

    record = (
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=run_ola079_gate,
            repetition_count=3,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            metadata={
                "gate_role": (
                    "readiness_recovery_bounded_repeatability"
                ),
                "upstream_gate": "OLA-079",
                "continuous_service_requested": False,
            },
        )
    )

    assert record.gate_status == "passed"
    assert record.requested_repetition_count == 3
    assert record.completed_repetition_count == 3
    assert record.successful_repetition_count == 3
    assert record.failed_repetition_count == 0
    assert record.result_codes == (
        0,
        0,
        0,
    )

    assert len(
        record.result_hashes
    ) == 3

    assert len(
        set(record.result_hashes)
    ) == 3

    assert record.complete_ola079_gate_repeated is True
    assert record.bounded_operation_preserved is True
    assert record.continuous_service_started is False

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False
    assert record.execution_adapter_resolved is False
    assert record.execution_adapter_invoked is False
    assert record.trade_authorization_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    assert record.verify_record_hash() is True

    first_canonical = record.to_canonical_dict()
    second_canonical = record.to_canonical_dict()

    assert first_canonical == second_canonical

    print(
        "[PASS] Complete OLA-079 recovery/full-runner "
        "gate repeated three times"
    )
    print(
        "[PASS] Every bounded repetition returned "
        "canonical success"
    )
    print(
        "[PASS] Deterministic repetition evidence "
        "and record hash verified"
    )

    calls = 0

    def failing_gate() -> int:
        nonlocal calls

        calls += 1

        if calls == 2:
            return 1

        return 0

    print(
        "[TEST] Failed bounded repetition rejected"
    )

    try:
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=failing_gate,
            repetition_count=3,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
        )
    except OracleReadinessRecoveryBoundedRepeatabilityFailure:
        pass
    else:
        raise AssertionError(
            "failed OLA-079 repetition was not rejected"
        )

    assert calls == 2

    print(
        "[PASS] Failed bounded repetition rejected"
    )

    print(
        "[TEST] Invalid repetition contract rejected"
    )

    try:
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=run_ola079_gate,
            repetition_count=0,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
        )
    except OracleReadinessRecoveryBoundedRepeatabilityContractError:
        pass
    else:
        raise AssertionError(
            "invalid repetition count was not rejected"
        )

    print(
        "[PASS] Invalid repetition contract rejected"
    )

    print(
        "[PASS] Continuous Oracle service was not started"
    )
    print(
        "[PASS] Oracle remained read-only; execution "
        "authority remained disabled"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
