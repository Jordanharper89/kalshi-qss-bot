from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
    KalshiLiveReadReadinessRecord,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowServiceRunner,
    OracleLiveShadowServiceRunnerCompatibilityError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_readiness_recovery_runner_compatibility_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    OracleReadinessRecoveryRunnerCompatibilityGateContractError,
    OracleReadinessRecoveryRunnerCompatibilityGateFailure,
    evaluate_oracle_readiness_recovery_runner_compatibility,
)


PROVIDER_MODULE_NAME = (
    "qseries_v2.oracle_intelligence."
    "live_acquisition_model."
    "oracle_first_real_shadow_corpus_launch_command"
)


def build_canonical_readiness_record(
    *,
    checked_at: datetime,
    evaluated_at: datetime,
    readiness_id: str,
    readiness_attempt_number: int,
) -> KalshiLiveReadReadinessRecord:
    return KalshiLiveReadReadinessRecord(
        schema_version="OLA-018",
        engine_id="OLA-018",
        readiness_id=readiness_id,
        readiness_status="passed",
        adapter_id="kalshi.public.markets.read_only",
        source_id="kalshi.public.markets",
        source_base_url=(
            "https://api.elections.kalshi.com/"
            "trade-api/v2"
        ),
        source_endpoint="/markets",
        http_method="GET",
        checked_at=checked_at,
        evaluated_at=evaluated_at,
        public_endpoint=True,
        authentication_used=False,
        live_get_request_count=1,
        source_contract_valid=True,
        source_probe_health_status="healthy",
        source_reachable=True,
        source_latency_ms=1,
        source_health_evidence_hash=(
            f"{readiness_attempt_number:064x}"
        ),
        rate_control_evidence_hash=(
            f"{readiness_attempt_number + 10:064x}"
        ),
        source_control_decision_hash=(
            f"{readiness_attempt_number + 20:064x}"
        ),
        source_control_reason_codes=(
            "acquisition_allowed",
            "source_reachable",
        ),
        health_policy_evidence_present=True,
        rate_policy_evidence_present=True,
        source_control_acquisition_allowed=True,
        shadow_mode=True,
        alerts_allowed=False,
        qseries_intake_allowed=False,
        live_shadow_cycle_entry_ready=True,
        continuous_polling_started=False,
        acquisition_performed=False,
        canonical_observation_created=False,
        persistence_invoked=False,
        alert_created=False,
        qseries_intake_record_created=False,
        reason_codes=(
            "live_shadow_cycle_entry_ready",
            "read_only",
            "execution_disabled",
        ),
        readiness_metadata=(
            (
                "readiness_attempt_number",
                readiness_attempt_number,
            ),
            (
                "test_fixture",
                "ola078.canonical_ola018_record",
            ),
        ),
        readiness_hash=(
            f"{readiness_attempt_number + 30:064x}"
        ),
        immutable=True,
        replayable=True,
        auditable=True,
        explainable=True,
        read_only=True,
        execution_allowed=False,
        execution_adapter_resolved=False,
        execution_adapter_invoked=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
    )


class RecoveringReadinessGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(
        self,
        **kwargs,
    ) -> KalshiLiveReadReadinessRecord:
        call = dict(kwargs)

        self.calls.append(
            call
        )

        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure(
                "temporary readiness failure"
            )

        return build_canonical_readiness_record(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
            readiness_id=(
                "readiness.ola078.recovered"
            ),
            readiness_attempt_number=len(
                self.calls
            ),
        )


class StaleTimestampReadinessProvider:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self,
        *,
        iteration_number: int,
        consecutive_failures: int,
        checked_at: datetime,
        evaluated_at: datetime,
    ) -> KalshiLiveReadReadinessRecord:
        self.calls += 1

        replacement_checked_at = (
            checked_at
            + timedelta(seconds=5)
        )

        replacement_evaluated_at = (
            replacement_checked_at
            + timedelta(microseconds=1)
        )

        return build_canonical_readiness_record(
            checked_at=replacement_checked_at,
            evaluated_at=replacement_evaluated_at,
            readiness_id=(
                "readiness.ola078.stale"
            ),
            readiness_attempt_number=self.calls,
        )


def construct_production_provider(
    provider_class,
    *,
    gate,
    sleeper,
    clock,
):
    provider = provider_class.__new__(
        provider_class
    )

    provider._gate = gate
    provider._retry_base_seconds = 5.0
    provider._retry_max_seconds = 60.0
    provider._sleeper = sleeper
    provider._clock = clock
    provider._calls = 0
    provider._readiness_attempts = 0
    provider._transient_failure_count = 0
    provider._last_transient_failure = None

    return provider


def main() -> int:
    print("========================================")
    print(" OLA-078 RECOVERY/RUNNER COMPATIBILITY")
    print(" PRODUCTION CORRECTION V2")
    print(" CANONICAL OLA-018 READINESS RECORD")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-078"
    assert ENGINE_ID == "OLA-078"
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False

    provider_module = import_module(
        PROVIDER_MODULE_NAME
    )

    provider_class = getattr(
        provider_module,
        "_ProductionLiveReadinessProvider",
    )

    provider_source = Path(
        provider_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    print("[TEST] OLA-077 production correction present")

    assert (
        "OLA-077 canonical retry timestamp-lineage correction"
        in provider_source
    )

    assert (
        "attempt_checked_at = self._fresh_timestamp()"
        not in provider_source
    )

    print("[OK] OLA-077 production correction present")

    checked_at = datetime(
        2026,
        7,
        19,
        14,
        0,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(microseconds=1)
    )

    retry_delays: list[float] = []
    retry_clock_calls: list[str] = []

    def forbidden_retry_clock() -> datetime:
        retry_clock_calls.append(
            "called"
        )

        raise AssertionError(
            "OLA-077 recovery path must not create "
            "replacement canonical timestamps"
        )

    recovering_gate = RecoveringReadinessGate()

    production_provider = (
        construct_production_provider(
            provider_class,
            gate=recovering_gate,
            sleeper=retry_delays.append,
            clock=forbidden_retry_clock,
        )
    )

    runner = OracleLiveShadowServiceRunner.__new__(
        OracleLiveShadowServiceRunner
    )

    print("[TEST] Canonical OLA-018 record construction")

    canonical_fixture = (
        build_canonical_readiness_record(
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            readiness_id=(
                "readiness.ola078.fixture"
            ),
            readiness_attempt_number=1,
        )
    )

    assert isinstance(
        canonical_fixture,
        KalshiLiveReadReadinessRecord,
    )

    assert canonical_fixture.schema_version == "OLA-018"
    assert canonical_fixture.engine_id == "OLA-018"
    assert canonical_fixture.readiness_status == "passed"
    assert canonical_fixture.read_only is True
    assert canonical_fixture.execution_allowed is False

    print("[OK] Canonical OLA-018 record construction")

    print("[TEST] Temporary failure recovery through real provider")

    record = (
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=production_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            iteration_number=1,
            consecutive_failures=0,
            readiness_attempt_count_callable=(
                lambda: production_provider.readiness_attempts
            ),
            transient_failure_count_callable=(
                lambda: (
                    production_provider.transient_failure_count
                )
            ),
            retry_delay_count_callable=(
                lambda: len(retry_delays)
            ),
            retry_clock_call_count_callable=(
                lambda: len(retry_clock_calls)
            ),
            metadata={
                "test_id": (
                    "ola078.real_provider.runner_compatibility"
                ),
                "production_provider_used": True,
                "canonical_ola018_record_used": True,
                "strict_runner_validator_used": True,
            },
        )
    )

    assert len(
        recovering_gate.calls
    ) == 2

    assert retry_delays == [
        5.0
    ]

    assert retry_clock_calls == []

    for call in recovering_gate.calls:
        assert (
            call["checked_at"]
            == checked_at
        )

        assert (
            call["evaluated_at"]
            == evaluated_at
        )

        assert (
            call[
                "rate_window_observation"
            ].checked_at
            == checked_at
        )

    assert (
        recovering_gate.calls[0][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 1
    )

    assert (
        recovering_gate.calls[1][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 2
    )

    assert record.gate_status == "passed"
    assert record.readiness_attempt_count == 2
    assert record.transient_failure_count == 1
    assert record.retry_delay_count == 1

    assert (
        record.provider_checked_at_preserved
        is True
    )

    assert (
        record.provider_evaluated_at_preserved
        is True
    )

    assert (
        record.runner_validation_passed
        is True
    )

    assert (
        record.retry_clock_unused
        is True
    )

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    print("[OK] Recovered readiness passed OLA-023 validation")

    print("[TEST] Strict runner rejects wrong record type")

    class WrongReadinessRecord:
        schema_version = "OLA-018"
        engine_id = "OLA-018"
        readiness_status = "passed"
        live_shadow_cycle_entry_ready = True
        shadow_mode = True
        alerts_allowed = False
        qseries_intake_allowed = False
        read_only = True
        execution_allowed = False

        def __init__(
            self,
            *,
            record_checked_at,
            record_evaluated_at,
        ) -> None:
            self.checked_at = record_checked_at
            self.evaluated_at = record_evaluated_at

    wrong_readiness = WrongReadinessRecord(
        record_checked_at=checked_at,
        record_evaluated_at=evaluated_at,
    )

    try:
        runner._validate_readiness(
            readiness=wrong_readiness,
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
    except (
        OracleLiveShadowServiceRunnerCompatibilityError
    ) as exc:
        assert (
            "returned incompatible record"
            in str(exc)
        )
    else:
        raise AssertionError(
            "strict runner accepted wrong readiness type"
        )

    print("[OK] Strict runner rejects wrong record type")

    print("[TEST] Strict runner rejects stale checked_at")

    stale_provider = (
        StaleTimestampReadinessProvider()
    )

    stale_readiness = stale_provider(
        iteration_number=1,
        consecutive_failures=0,
        checked_at=checked_at,
        evaluated_at=evaluated_at,
    )

    assert isinstance(
        stale_readiness,
        KalshiLiveReadReadinessRecord,
    )

    try:
        runner._validate_readiness(
            readiness=stale_readiness,
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
    except (
        OracleLiveShadowServiceRunnerCompatibilityError
    ) as exc:
        assert (
            "did not preserve checked_at"
            in str(exc)
        )
    else:
        raise AssertionError(
            "strict runner accepted stale checked_at"
        )

    print("[OK] Strict runner still rejects stale checked_at")

    print("[TEST] OLA-078 rejects stale provider")

    try:
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=stale_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            iteration_number=1,
            consecutive_failures=0,
            readiness_attempt_count_callable=(
                lambda: 2
            ),
            transient_failure_count_callable=(
                lambda: 1
            ),
            retry_delay_count_callable=(
                lambda: 1
            ),
            retry_clock_call_count_callable=(
                lambda: 0
            ),
        )
    except (
        OracleReadinessRecoveryRunnerCompatibilityGateFailure
    ) as exc:
        assert (
            "did not preserve checked_at"
            in str(exc)
        )
    else:
        raise AssertionError(
            "OLA-078 accepted stale provider"
        )

    print("[OK] OLA-078 rejects stale provider")

    print("[TEST] Invalid timestamps rejected")

    try:
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=production_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at.replace(
                tzinfo=None
            ),
            evaluated_at=evaluated_at,
            readiness_attempt_count_callable=(
                lambda: 2
            ),
            transient_failure_count_callable=(
                lambda: 1
            ),
            retry_delay_count_callable=(
                lambda: 1
            ),
            retry_clock_call_count_callable=(
                lambda: 0
            ),
        )
    except (
        OracleReadinessRecoveryRunnerCompatibilityGateContractError
    ) as exc:
        assert (
            "checked_at must be timezone-aware"
            in str(exc)
        )
    else:
        raise AssertionError(
            "naive checked_at was accepted"
        )

    print("[OK] Invalid timestamps rejected")

    print("[TEST] Recovery evidence is canonical")

    payload = record.to_canonical_dict()

    assert payload["schema_version"] == "OLA-078"
    assert payload["engine_id"] == "OLA-078"
    assert payload["gate_status"] == "passed"

    assert (
        payload["metadata"][
            "compatibility_boundary"
        ]
        == (
            "OLA-069 recovery provider -> "
            "OLA-023 strict runner validator"
        )
    )

    assert (
        payload["metadata"][
            "canonical_ola018_record_used"
        ]
        is True
    )

    assert (
        payload["metadata"][
            "real_service_started"
        ]
        is False
    )

    assert (
        payload["metadata"][
            "background_loop_started"
        ]
        is False
    )

    print("[OK] Recovery evidence is canonical")

    print("[TEST] No service or execution authority introduced")

    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False
    assert payload["alerts_allowed"] is False
    assert payload["qseries_handoff_allowed"] is False
    assert payload["trade_authorization_allowed"] is False
    assert payload["order_placement_allowed"] is False
    assert payload["funds_moved"] is False
    assert payload["portfolio_mutated"] is False

    print("[OK] Oracle read-only boundary preserved")

    print(
        "[PASS] OLA-078 Oracle Readiness Recovery "
        "Runner Compatibility Gate Correction V2"
    )

    print({
        "schema_version": "OLA-078",
        "engine_id": "OLA-078",
        "status": "passed",
        "ola077_production_correction_present": True,
        "real_production_provider_used": True,
        "canonical_ola018_readiness_record_used": True,
        "wrong_record_type_rejected": True,
        "temporary_readiness_failure_exercised": True,
        "readiness_recovery_exercised": True,
        "ola069_retry_metadata_preserved": True,
        "ola023_strict_runner_validator_used": True,
        "checked_at_preserved_after_retry": True,
        "evaluated_at_preserved_after_retry": True,
        "recovered_readiness_accepted_by_runner": True,
        "stale_checked_at_still_rejected": True,
        "replacement_retry_clock_unused": True,
        "real_service_started": False,
        "background_loop_started": False,
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
