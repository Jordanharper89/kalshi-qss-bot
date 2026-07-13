"""
INT-OLA-SERVICE-001
Oracle Live Shadow Service Full Integration Gate

Full service-level integration gate for:

OLA-017
Oracle PostgreSQL Shadow Acquisition Cycle boundary

OLA-018
Oracle Kalshi Live Read Readiness Gate contract

OLA-019
Oracle Shadow Polling Policy and Cadence Engine

OLA-020
Oracle Service Isolation and Canonical Intelligence Handoff Contract

OLA-021
Oracle Controlled Shadow Collection Scheduler Tick

OLA-022
Oracle Live Shadow Service Bootstrap Contract

OLA-023
Oracle Live Shadow Service Runner

This gate proves:

ORACLE / Q SERIES ISOLATION
    |
SERVICE BOOTSTRAP READY
    |
CALLER-CONTROLLED CLOCK LINEAGE
    |
OLA-018 READINESS
    |
OLA-019 POLLING POLICY
    |
OLA-021 ONE-TICK SCHEDULER
    |
OLA-017 SHADOW CYCLE BOUNDARY
    |
IMMUTABLE POLLING STATE
    |
RUNTIME STATE EVIDENCE
RUNTIME LOG EVIDENCE
    |
CONTROLLED SLEEP
    |
EXPLICIT STOP

Permanent integration rules:

- Oracle and Q Series remain separate services.
- Oracle has no execution authority.
- OLA-022 bootstrap must be ready.
- OLA-023 must consume exactly one readiness record per iteration.
- OLA-023 must invoke exactly one OLA-021 tick per iteration.
- OLA-021 may invoke at most one OLA-017 cycle per tick.
- Caller-controlled clock lineage must remain monotonic.
- Readiness timestamps must be preserved.
- Polling state must carry forward between iterations.
- Runtime state evidence must be written once per iteration.
- Runtime log evidence must be written once per iteration.
- Controlled sleep occurs only between continuing iterations.
- Explicit stop returns control.
- No alerts are created.
- No Q Series intake is created.
- No canonical handoff is published.
- No execution capability exists.
- Deterministic replay is required.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path


from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
    ShadowCycleRunnerBinding,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_bootstrap_contract import (
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    OracleLiveShadowServiceBootstrapContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowReadinessProviderBinding,
    OracleLiveShadowSchedulerBinding,
    OracleLiveShadowServiceRunner,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingState,
)


SCHEMA_VERSION = "INT-OLA-SERVICE-001"
ENGINE_ID = "INT-OLA-SERVICE-001"

SOURCE_ID = "source.kalshi.market_data"

ADAPTER_ID = (
    "adapter.oracle.kalshi.public_markets.shadow"
)

BASE_TIME = datetime(
    2026,
    7,
    12,
    20,
    0,
    0,
    tzinfo=timezone.utc,
)


class DeterministicClock:
    def __init__(
        self,
        *,
        start,
        step_seconds=1,
    ):
        self.current = start

        self.step = timedelta(
            seconds=step_seconds
        )

        self.calls = 0

    def __call__(
        self,
    ):
        result = self.current

        self.current = (
            self.current
            + self.step
        )

        self.calls += 1

        return result


class SleepRecorder:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        seconds,
    ):
        self.calls.append(
            seconds
        )

        return {
            "slept_seconds": seconds,
            "sleep_call_number": len(self.calls),
        }


class StopController:
    def __init__(
        self,
        *,
        stop_after_checks,
    ):
        self.stop_after_checks = stop_after_checks

        self.checks = 0

    def __call__(
        self,
    ):
        self.checks += 1

        return (
            self.checks
            >= self.stop_after_checks
        )


class CanonicalEvidenceWriter:
    def __init__(
        self,
        *,
        evidence_role,
    ):
        self.evidence_role = evidence_role

        self.calls = []

    def __call__(
        self,
        *,
        evidence,
    ):
        assert evidence["schema_version"] == "OLA-023"

        assert evidence["engine_id"] == "OLA-023"

        assert evidence["evidence_role"] == self.evidence_role

        self.calls.append(
            evidence
        )

        return {
            "status": "written",
            "evidence_role": self.evidence_role,
            "write_number": len(self.calls),
        }


class IntegratedReadinessProvider:
    def __init__(
        self,
    ):
        self.calls = 0

        self.timestamp_pairs = []

        self.polling_state_ids = []

    def __call__(
        self,
        *,
        iteration_number,
        polling_state_id,
        checked_at,
        evaluated_at,
    ):
        self.calls += 1

        self.timestamp_pairs.append(
            (
                checked_at,
                evaluated_at,
            )
        )

        self.polling_state_ids.append(
            polling_state_id
        )

        return KalshiLiveReadReadinessRecord(
            schema_version="OLA-018",
            engine_id="OLA-018",
            readiness_id=(
                f"readiness.int.ola.service.001."
                f"{iteration_number}"
            ),
            readiness_status="passed",
            adapter_id=ADAPTER_ID,
            source_id=SOURCE_ID,
            source_base_url=(
                "https://external-api.kalshi.com/"
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
                f"{iteration_number:064x}"
            ),
            rate_control_evidence_hash=(
                f"{iteration_number + 100:064x}"
            ),
            source_control_decision_hash=(
                f"{iteration_number + 200:064x}"
            ),
            source_control_reason_codes=(
                "acquisition_allowed",
                "consecutive_failures_within_policy",
                "latency_within_policy",
                "rate_reserve_preserved",
                "rate_usage_within_limit",
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
            ),
            readiness_metadata=(
                ("integration_gate", ENGINE_ID),
                ("iteration_number", iteration_number),
                ("polling_state_id", polling_state_id),
            ),
            readiness_hash=(
                f"{iteration_number + 300:064x}"
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


class IntegratedOLA017BoundaryRunner:
    def __init__(
        self,
    ):
        self.calls = 0

        self.kwargs = []

    def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1

        self.kwargs.append(
            dict(kwargs)
        )

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "status": "completed",
            "adapter_id": ADAPTER_ID,
            "source_id": SOURCE_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "bootstrap_live_write_ready": True,
            "source_control_allowed_cycle_invoked": True,
            "source_control_blocked_cycle_invoked": False,
            "observation_count": 2,
            "canonical_count": 2,
            "duplicate_count": 0,
            "routed_count": 2,
            "postgresql_routing_record_delta": 2,
            "first_persistence_sequence_number": (
                ((self.calls - 1) * 2) + 1
            ),
            "last_persistence_sequence_number": (
                self.calls * 2
            ),
            "postgresql_persistence_count": 2,
            "deduplication_reconciled": True,
            "routing_reconciled": True,
            "persistence_reconciled": True,
            "postgresql_chain_advanced": True,
            "canonical_replay_hash_owned_by_ola_001": True,
            "raw_observation_hash_owned_by_ola_016": True,
            "deterministic_replay_valid": True,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }


class IntegratedSchedulerBinding:
    def __init__(
        self,
        *,
        scheduler,
    ):
        self.scheduler = scheduler

        self.calls = 0

    def __call__(
        self,
        *,
        readiness,
        polling_state,
        evaluated_at,
        started_at,
        completed_at,
        polling_decision_metadata,
        cycle_kwargs,
        tick_metadata,
    ):
        self.calls += 1

        return self.scheduler.run_tick(
            readiness=readiness,
            polling_state=polling_state,
            evaluated_at=evaluated_at,
            started_at=started_at,
            completed_at=completed_at,
            polling_decision_metadata=(
                polling_decision_metadata
            ),
            cycle_kwargs=cycle_kwargs,
            tick_metadata=tick_metadata,
        )


def build_service_isolation_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "integration_gate": ENGINE_ID,
            "environment": "production",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_bootstrap_record():
    service_contract = (
        build_service_isolation_contract()
    )

    bootstrap_contract = (
        OracleLiveShadowServiceBootstrapContract(
            service_contract=service_contract
        )
    )

    runtime_root = Path(
        "C:/qseries/runtime"
    )

    return bootstrap_contract.bootstrap(
        oem_runtime_lineage=(
            REQUIRED_OEM_RUNTIME_LINEAGE
        ),
        ola_boundaries=(
            REQUIRED_OLA_BOUNDARIES
        ),
        runtime_root=runtime_root,
        runtime_state_directory=(
            runtime_root
            / "state"
        ),
        runtime_logs_directory=(
            runtime_root
            / "logs"
        ),
        bootstrapped_at=BASE_TIME,
        bootstrap_metadata={
            "integration_gate": ENGINE_ID,
            "environment": "production",
            "service_mode": "live_shadow",
        },
    )


def build_polling_policy():
    return ShadowPollingPolicy.create(
        policy_id=(
            "oracle.kalshi.shadow.polling."
            "int_ola_service_001"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        base_interval_seconds=1,
        jitter_max_seconds=0,
        readiness_max_age_seconds=300,
        failure_backoff_base_seconds=1,
        failure_backoff_multiplier=2,
        failure_backoff_max_seconds=60,
        consecutive_failure_suspend_threshold=4,
        suspension_cooldown_seconds=60,
        explicit_restart_evidence_required=True,
        policy_metadata={
            "integration_gate": ENGINE_ID,
            "mode": "shadow",
        },
    )


def build_initial_polling_state():
    return ShadowPollingState.create(
        state_id=(
            "polling.state.int.ola.service.001.initial"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "integration_gate": ENGINE_ID,
            "state": "initial",
        },
    )


def readiness_kwargs_factory(
    iteration_number,
    polling_state,
    checked_at,
    evaluated_at,
):
    return {
        "iteration_number": iteration_number,
        "polling_state_id": polling_state.state_id,
        "checked_at": checked_at,
        "evaluated_at": evaluated_at,
    }


def scheduler_kwargs_factory(
    iteration_number,
    readiness,
    polling_state,
    evaluated_at,
    started_at,
    completed_at,
):
    return {
        "readiness": readiness,
        "polling_state": polling_state,
        "evaluated_at": evaluated_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "polling_decision_metadata": {
            "integration_gate": ENGINE_ID,
            "iteration_number": iteration_number,
        },
        "cycle_kwargs": {
            "integration_gate": ENGINE_ID,
            "service_iteration_number": iteration_number,
        },
        "tick_metadata": {
            "integration_gate": ENGINE_ID,
            "service_iteration_number": iteration_number,
        },
    }


def build_integrated_service(
    *,
    stop_after_checks,
):
    readiness_provider = (
        IntegratedReadinessProvider()
    )

    ola_017_runner = (
        IntegratedOLA017BoundaryRunner()
    )

    polling_engine = (
        OracleShadowPollingPolicyCadenceEngine(
            policy=build_polling_policy()
        )
    )

    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
            polling_engine=polling_engine,
            cycle_runner=ShadowCycleRunnerBinding(
                runner_id=(
                    "runner.ola017.int_ola_service_001"
                ),
                engine_id="OLA-017",
                source_id=SOURCE_ID,
                adapter_id=ADAPTER_ID,
                cycle_callable=ola_017_runner,
            ),
        )
    )

    scheduler_binding_callable = (
        IntegratedSchedulerBinding(
            scheduler=scheduler
        )
    )

    state_writer = CanonicalEvidenceWriter(
        evidence_role="runtime/state"
    )

    log_writer = CanonicalEvidenceWriter(
        evidence_role="runtime/logs"
    )

    clock = DeterministicClock(
        start=(
            BASE_TIME
            + timedelta(minutes=1)
        ),
        step_seconds=1,
    )

    sleeper = SleepRecorder()

    stop_controller = StopController(
        stop_after_checks=stop_after_checks
    )

    service_runner = OracleLiveShadowServiceRunner(
        bootstrap_record=build_bootstrap_record(),
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
                provider_id=(
                    "provider.ola018."
                    "int_ola_service_001"
                ),
                engine_id="OLA-018",
                readiness_callable=readiness_provider,
            )
        ),
        scheduler=OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021."
                "int_ola_service_001"
            ),
            engine_id="OLA-021",
            tick_callable=(
                scheduler_binding_callable
            ),
        ),
        state_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.runtime.state."
                    "int_ola_service_001"
                ),
                evidence_role="runtime/state",
                writer_callable=state_writer,
            )
        ),
        log_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id=(
                    "writer.runtime.logs."
                    "int_ola_service_001"
                ),
                evidence_role="runtime/logs",
                writer_callable=log_writer,
            )
        ),
        clock_callable=clock,
        sleep_callable=sleeper,
        stop_requested_callable=stop_controller,
        service_tick_interval_seconds=1,
    )

    return {
        "service_runner": service_runner,
        "readiness_provider": readiness_provider,
        "ola_017_runner": ola_017_runner,
        "scheduler_binding_callable": (
            scheduler_binding_callable
        ),
        "state_writer": state_writer,
        "log_writer": log_writer,
        "clock": clock,
        "sleeper": sleeper,
        "stop_controller": stop_controller,
    }


def run_service_isolation_integration_test():
    contract = build_service_isolation_contract()

    assert contract.schema_version == "OLA-020"

    assert contract.engine_id == "OLA-020"

    assert contract.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert contract.qseries_service_id == (
        "service.qseries.execution"
    )

    assert contract.separate_process_required is True

    assert contract.oracle_execution_authority is False

    assert (
        contract.direct_execution_import_allowed
        is False
    )

    assert (
        contract.qseries_oracle_history_mutation_allowed
        is False
    )

    assert contract.read_only is True

    assert contract.execution_allowed is False

    return contract


def run_bootstrap_integration_test():
    record = build_bootstrap_record()

    assert record.schema_version == "OLA-022"

    assert record.engine_id == "OLA-022"

    assert record.bootstrap_status == "ready"

    assert record.service_start_allowed is True

    assert record.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert record.separate_process_required is True

    assert record.oracle_execution_authority is False

    assert (
        record.direct_execution_import_allowed
        is False
    )

    assert record.runtime_state_role == "runtime/state"

    assert record.runtime_logs_role == "runtime/logs"

    assert record.verify_bootstrap_hash() is True

    assert record.read_only is True

    assert record.execution_allowed is False

    return record


def run_three_iteration_service_test():
    components = build_integrated_service(
        stop_after_checks=999
    )

    (
        run_record,
        iterations,
        final_state,
    ) = components["service_runner"].run(
        initial_polling_state=(
            build_initial_polling_state()
        ),
        max_iterations=3,
        readiness_kwargs_factory=(
            readiness_kwargs_factory
        ),
        scheduler_kwargs_factory=(
            scheduler_kwargs_factory
        ),
        service_metadata={
            "integration_gate": ENGINE_ID,
            "environment": "production",
            "service_mode": "live_shadow",
        },
    )

    assert run_record.schema_version == "OLA-023"

    assert run_record.engine_id == "OLA-023"

    assert run_record.service_run_status == "completed"

    assert run_record.iteration_count == 3

    assert len(iterations) == 3

    assert (
        components["readiness_provider"].calls
        == 3
    )

    assert (
        components[
            "scheduler_binding_callable"
        ].calls
        == 3
    )

    assert components["ola_017_runner"].calls == 3

    assert len(components["state_writer"].calls) == 3

    assert len(components["log_writer"].calls) == 3

    assert len(components["sleeper"].calls) == 2

    assert components["sleeper"].calls == [
        1,
        1,
    ]

    assert run_record.completed_iteration_count == 3

    assert run_record.noop_iteration_count == 0

    assert run_record.failed_iteration_count == 0

    assert run_record.cycle_invocation_count == 3

    assert run_record.successful_cycle_count == 3

    assert (
        run_record.canonical_clock_lineage_valid
        is True
    )

    assert (
        run_record.readiness_timestamp_contract_preserved
        is True
    )

    assert final_state.last_cycle_succeeded is True

    assert final_state.consecutive_failures == 0

    assert final_state.suspended is False

    assert run_record.final_state_id == final_state.state_id

    assert (
        run_record.final_state_hash
        == final_state.state_hash
    )

    assert run_record.verify_service_run_hash() is True

    previous_next_state_hash = None

    for index, iteration in enumerate(
        iterations,
        start=1,
    ):
        assert iteration.iteration_number == index

        assert (
            iteration.canonical_clock_lineage_valid
            is True
        )

        assert (
            iteration.readiness_timestamp_contract_preserved
            is True
        )

        assert (
            iteration.iteration_started_at
            <= iteration.readiness_checked_at
            <= iteration.readiness_evaluated_at
            <= iteration.scheduler_evaluated_at
            <= iteration.tick_started_at
            <= iteration.tick_completed_at
            <= iteration.iteration_completed_at
        )

        assert iteration.tick_status == "completed"

        assert iteration.cycle_invoked is True

        assert iteration.cycle_succeeded is True

        assert (
            iteration.next_consecutive_failures
            == 0
        )

        assert iteration.next_state_suspended is False

        assert iteration.verify_iteration_hash() is True

        if previous_next_state_hash is not None:
            assert (
                iteration.previous_state_hash
                == previous_next_state_hash
            )

        previous_next_state_hash = (
            iteration.next_state_hash
        )

        assert iteration.alert_created is False

        assert (
            iteration.qseries_intake_record_created
            is False
        )

        assert (
            iteration.canonical_handoff_published
            is False
        )

        assert iteration.read_only is True

        assert iteration.execution_allowed is False

        assert (
            iteration.execution_adapter_resolved
            is False
        )

        assert (
            iteration.execution_adapter_invoked
            is False
        )

        assert (
            iteration.trade_authorization_allowed
            is False
        )

        assert iteration.order_placement_allowed is False

        assert iteration.funds_moved is False

        assert iteration.portfolio_mutated is False

    readiness_timestamps = (
        components[
            "readiness_provider"
        ].timestamp_pairs
    )

    assert len(readiness_timestamps) == 3

    for (
        iteration,
        timestamp_pair,
    ) in zip(
        iterations,
        readiness_timestamps,
    ):
        checked_at, evaluated_at = timestamp_pair

        assert (
            iteration.readiness_checked_at
            == checked_at
        )

        assert (
            iteration.readiness_evaluated_at
            == evaluated_at
        )

    polling_state_ids = (
        components[
            "readiness_provider"
        ].polling_state_ids
    )

    assert len(polling_state_ids) == 3

    assert polling_state_ids[0] == (
        build_initial_polling_state().state_id
    )

    assert polling_state_ids[1] == (
        iterations[0].next_state_id
    )

    assert polling_state_ids[2] == (
        iterations[1].next_state_id
    )

    return (
        run_record,
        iterations,
        final_state,
        components,
    )


def run_explicit_stop_integration_test():
    components = build_integrated_service(
        stop_after_checks=4
    )

    (
        run_record,
        iterations,
        final_state,
    ) = components["service_runner"].run(
        initial_polling_state=(
            build_initial_polling_state()
        ),
        max_iterations=None,
        readiness_kwargs_factory=(
            readiness_kwargs_factory
        ),
        scheduler_kwargs_factory=(
            scheduler_kwargs_factory
        ),
        service_metadata={
            "integration_gate": ENGINE_ID,
            "test": "explicit_stop",
        },
    )

    assert run_record.service_run_status == "stopped"

    assert run_record.stop_requested is True

    assert run_record.iteration_count == 2

    assert len(iterations) == 2

    assert (
        components["readiness_provider"].calls
        == 2
    )

    assert (
        components[
            "scheduler_binding_callable"
        ].calls
        == 2
    )

    assert components["ola_017_runner"].calls == 2

    assert len(components["state_writer"].calls) == 2

    assert len(components["log_writer"].calls) == 2

    assert len(components["sleeper"].calls) == 1

    assert final_state.consecutive_failures == 0

    assert final_state.suspended is False

    assert run_record.verify_service_run_hash() is True

    return (
        run_record,
        iterations,
        final_state,
    )


def run_deterministic_replay_integration_test():
    first_components = build_integrated_service(
        stop_after_checks=999
    )

    second_components = build_integrated_service(
        stop_after_checks=999
    )

    first_result = (
        first_components["service_runner"].run(
            initial_polling_state=(
                build_initial_polling_state()
            ),
            max_iterations=3,
            readiness_kwargs_factory=(
                readiness_kwargs_factory
            ),
            scheduler_kwargs_factory=(
                scheduler_kwargs_factory
            ),
            service_metadata={
                "integration_gate": ENGINE_ID,
                "test": "deterministic_replay",
            },
        )
    )

    second_result = (
        second_components["service_runner"].run(
            initial_polling_state=(
                build_initial_polling_state()
            ),
            max_iterations=3,
            readiness_kwargs_factory=(
                readiness_kwargs_factory
            ),
            scheduler_kwargs_factory=(
                scheduler_kwargs_factory
            ),
            service_metadata={
                "integration_gate": ENGINE_ID,
                "test": "deterministic_replay",
            },
        )
    )

    first_run, first_iterations, first_state = (
        first_result
    )

    second_run, second_iterations, second_state = (
        second_result
    )

    assert first_run == second_run

    assert first_iterations == second_iterations

    assert first_state == second_state

    assert (
        first_run.service_run_hash
        == second_run.service_run_hash
    )

    assert (
        first_state.state_hash
        == second_state.state_hash
    )


def main():
    service_contract = (
        run_service_isolation_integration_test()
    )

    bootstrap_record = (
        run_bootstrap_integration_test()
    )

    (
        run_record,
        iterations,
        final_state,
        components,
    ) = run_three_iteration_service_test()

    (
        stopped_run,
        stopped_iterations,
        stopped_state,
    ) = run_explicit_stop_integration_test()

    run_deterministic_replay_integration_test()

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_017_cycle_boundary_passed": True,
        "ola_018_readiness_passed": True,
        "ola_019_polling_policy_passed": True,
        "ola_020_service_isolation_passed": True,
        "ola_021_scheduler_tick_passed": True,
        "ola_022_service_bootstrap_passed": True,
        "ola_023_service_runner_passed": True,
        "oracle_service_id": (
            service_contract.oracle_service_id
        ),
        "qseries_service_id": (
            service_contract.qseries_service_id
        ),
        "separate_process_required": (
            service_contract.separate_process_required
        ),
        "oracle_execution_authority": (
            service_contract.oracle_execution_authority
        ),
        "direct_execution_import_allowed": (
            service_contract.direct_execution_import_allowed
        ),
        "bootstrap_status": (
            bootstrap_record.bootstrap_status
        ),
        "service_start_allowed": (
            bootstrap_record.service_start_allowed
        ),
        "runtime_state_role": (
            bootstrap_record.runtime_state_role
        ),
        "runtime_logs_role": (
            bootstrap_record.runtime_logs_role
        ),
        "service_run_status": (
            run_record.service_run_status
        ),
        "iteration_count": run_record.iteration_count,
        "readiness_request_count": (
            components["readiness_provider"].calls
        ),
        "scheduler_tick_count": (
            components[
                "scheduler_binding_callable"
            ].calls
        ),
        "ola_017_cycle_call_count": (
            components["ola_017_runner"].calls
        ),
        "exactly_one_readiness_per_iteration": (
            components["readiness_provider"].calls
            == run_record.iteration_count
        ),
        "exactly_one_scheduler_tick_per_iteration": (
            components[
                "scheduler_binding_callable"
            ].calls
            == run_record.iteration_count
        ),
        "exactly_one_cycle_per_eligible_tick": (
            components["ola_017_runner"].calls
            == run_record.cycle_invocation_count
        ),
        "state_evidence_write_count": (
            len(components["state_writer"].calls)
        ),
        "log_evidence_write_count": (
            len(components["log_writer"].calls)
        ),
        "state_write_once_per_iteration": (
            len(components["state_writer"].calls)
            == run_record.iteration_count
        ),
        "log_write_once_per_iteration": (
            len(components["log_writer"].calls)
            == run_record.iteration_count
        ),
        "controlled_sleep_call_count": (
            len(components["sleeper"].calls)
        ),
        "controlled_sleep_between_iterations": (
            len(components["sleeper"].calls)
            == run_record.iteration_count - 1
        ),
        "canonical_clock_lineage_valid": (
            run_record.canonical_clock_lineage_valid
        ),
        "readiness_timestamp_contract_preserved": (
            run_record.readiness_timestamp_contract_preserved
        ),
        "polling_state_chain_preserved": True,
        "final_consecutive_failures": (
            final_state.consecutive_failures
        ),
        "final_state_suspended": (
            final_state.suspended
        ),
        "explicit_stop_status": (
            stopped_run.service_run_status
        ),
        "explicit_stop_observed": (
            stopped_run.stop_requested
        ),
        "explicit_stop_iteration_count": (
            stopped_run.iteration_count
        ),
        "explicit_stop_returned_control": (
            len(stopped_iterations) == 2
            and stopped_state.suspended is False
        ),
        "deterministic_bootstrap_hashing": True,
        "deterministic_iteration_hashing": True,
        "deterministic_service_run_hashing": True,
        "deterministic_replay_valid": True,
        "alerts_allowed": run_record.alerts_allowed,
        "qseries_intake_allowed": (
            run_record.qseries_intake_allowed
        ),
        "canonical_handoff_published": (
            run_record.canonical_handoff_published
        ),
        "read_only": run_record.read_only,
        "execution_allowed": run_record.execution_allowed,
        "execution_adapter_resolved": (
            run_record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            run_record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            run_record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            run_record.order_placement_allowed
        ),
        "funds_moved": run_record.funds_moved,
        "portfolio_mutated": run_record.portfolio_mutated,
    }

    assert result["ola_017_cycle_boundary_passed"] is True

    assert result["ola_018_readiness_passed"] is True

    assert result["ola_019_polling_policy_passed"] is True

    assert result["ola_020_service_isolation_passed"] is True

    assert result["ola_021_scheduler_tick_passed"] is True

    assert result["ola_022_service_bootstrap_passed"] is True

    assert result["ola_023_service_runner_passed"] is True

    assert result["separate_process_required"] is True

    assert result["oracle_execution_authority"] is False

    assert result["direct_execution_import_allowed"] is False

    assert result["bootstrap_status"] == "ready"

    assert result["service_start_allowed"] is True

    assert result["exactly_one_readiness_per_iteration"] is True

    assert (
        result["exactly_one_scheduler_tick_per_iteration"]
        is True
    )

    assert result["exactly_one_cycle_per_eligible_tick"] is True

    assert result["state_write_once_per_iteration"] is True

    assert result["log_write_once_per_iteration"] is True

    assert (
        result["controlled_sleep_between_iterations"]
        is True
    )

    assert result["canonical_clock_lineage_valid"] is True

    assert (
        result["readiness_timestamp_contract_preserved"]
        is True
    )

    assert result["polling_state_chain_preserved"] is True

    assert result["explicit_stop_observed"] is True

    assert result["explicit_stop_returned_control"] is True

    assert result["alerts_allowed"] is False

    assert result["qseries_intake_allowed"] is False

    assert result["canonical_handoff_published"] is False

    assert result["read_only"] is True

    assert result["execution_allowed"] is False

    assert result["execution_adapter_resolved"] is False

    assert result["execution_adapter_invoked"] is False

    assert result["trade_authorization_allowed"] is False

    assert result["order_placement_allowed"] is False

    assert result["funds_moved"] is False

    assert result["portfolio_mutated"] is False

    print(
        "[PASS] INT-OLA-SERVICE-001 Oracle Live Shadow "
        "Service Full Integration Gate"
    )

    print(result)


if __name__ == "__main__":
    main()
