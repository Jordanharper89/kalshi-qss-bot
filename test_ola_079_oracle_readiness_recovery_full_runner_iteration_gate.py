from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
    KalshiLiveReadReadinessRecord,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_readiness_recovery_full_runner_iteration_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    evaluate_oracle_readiness_recovery_full_runner_iteration,
)
from test_ola_023_oracle_live_shadow_service_runner import (
    build_components,
    initial_state,
    scheduler_kwargs_factory,
)

PROVIDER_MODULE_NAME = (
    "qseries_v2.oracle_intelligence.live_acquisition_model."
    "oracle_first_real_shadow_corpus_launch_command"
)


def build_canonical_readiness_record(*, checked_at, evaluated_at, attempt):
    return KalshiLiveReadReadinessRecord(
        schema_version="OLA-018",
        engine_id="OLA-018",
        readiness_id=f"readiness.ola079.recovered.{attempt}",
        readiness_status="passed",
        adapter_id="adapter.oracle.kalshi.public_markets.shadow",
        source_id="source.kalshi.market_data",
        source_base_url="https://api.elections.kalshi.com/trade-api/v2",
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
        source_health_evidence_hash=f"{attempt:064x}",
        rate_control_evidence_hash=f"{attempt + 10:064x}",
        source_control_decision_hash=f"{attempt + 20:064x}",
        source_control_reason_codes=("acquisition_allowed", "source_reachable"),
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
        reason_codes=("live_shadow_cycle_entry_ready", "read_only"),
        readiness_metadata=(("readiness_attempt_number", attempt),),
        readiness_hash=f"{attempt + 30:064x}",
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
    def __init__(self):
        self.calls = []

    def evaluate(self, **kwargs):
        self.calls.append(dict(kwargs))
        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure("temporary readiness failure")
        return build_canonical_readiness_record(
            checked_at=kwargs["checked_at"],
            evaluated_at=kwargs["evaluated_at"],
            attempt=len(self.calls),
        )


def construct_production_provider(provider_class, gate, retry_delays):
    provider = provider_class.__new__(provider_class)
    provider._gate = gate
    provider._retry_base_seconds = 5.0
    provider._retry_max_seconds = 60.0
    provider._sleeper = retry_delays.append
    provider._clock = lambda: (_ for _ in ()).throw(
        AssertionError("retry path created a replacement timestamp")
    )
    provider._calls = 0
    provider._readiness_attempts = 0
    provider._transient_failure_count = 0
    provider._last_transient_failure = None
    return provider


def readiness_kwargs_factory(iteration_number, polling_state, checked_at, evaluated_at):
    return {
        "iteration_number": iteration_number,
        "consecutive_failures": polling_state.consecutive_failures,
        "checked_at": checked_at,
        "evaluated_at": evaluated_at,
    }


def main() -> int:
    print("========================================")
    print(" OLA-079 FULL RUNNER RECOVERY GATE")
    print(" ONE BOUNDED OLA-023 ITERATION")
    print(" CONTINUOUS SERVICE NOT STARTED")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-079"
    assert ENGINE_ID == "OLA-079"
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False

    provider_module = import_module(PROVIDER_MODULE_NAME)
    provider_class = getattr(provider_module, "_ProductionLiveReadinessProvider")

    retry_delays = []
    recovering_gate = RecoveringReadinessGate()
    production_provider = construct_production_provider(
        provider_class,
        recovering_gate,
        retry_delays,
    )

    components = build_components(readiness_callable=production_provider)

    print("[TEST] Real production provider through complete OLA-023 iteration")

    record = evaluate_oracle_readiness_recovery_full_runner_iteration(
        runner=components["runner"],
        initial_polling_state=initial_state(),
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        readiness_attempt_count_callable=lambda: production_provider.readiness_attempts,
        transient_failure_count_callable=lambda: production_provider.transient_failure_count,
        retry_delay_count_callable=lambda: len(retry_delays),
        service_metadata={
            "test_id": "ola079.real_provider.full_runner_iteration",
            "bounded": True,
            "real_service_started": False,
        },
    )

    assert len(recovering_gate.calls) == 2
    assert retry_delays == [5.0]
    assert record.gate_status == "passed"
    assert record.service_run_status == "completed"
    assert record.iteration_count == 1
    assert record.completed_iteration_count == 1
    assert record.readiness_attempt_count == 2
    assert record.transient_failure_count == 1
    assert record.retry_delay_count == 1
    assert record.checked_at_preserved is True
    assert record.evaluated_at_preserved is True
    assert record.service_run_hash_verified is True
    assert record.iteration_hash_verified is True
    assert record.final_state_hash_verified is True
    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    first_call, second_call = recovering_gate.calls
    assert first_call["checked_at"] == second_call["checked_at"]
    assert first_call["evaluated_at"] == second_call["evaluated_at"]
    assert first_call["rate_window_observation"].checked_at == first_call["checked_at"]
    assert second_call["rate_window_observation"].checked_at == second_call["checked_at"]

    print("[PASS] OLA-079 recovered readiness completed one exact OLA-023 iteration")
    print("[PASS] Canonical timestamp lineage preserved across recovery")
    print("[PASS] OLA-023 run, iteration, and final-state hashes verified")
    print("[PASS] Oracle remained read-only; execution authority remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
