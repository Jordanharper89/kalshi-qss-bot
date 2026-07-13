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
    OracleLiveShadowServiceRunnerCompatibilityError,
    OracleLiveShadowServiceRunnerContractError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingState,
)


SOURCE_ID = "source.kalshi.market_data"

ADAPTER_ID = (
    "adapter.oracle.kalshi.public_markets.shadow"
)

BASE_TIME = datetime(
    2026,
    7,
    12,
    19,
    0,
    0,
    tzinfo=timezone.utc,
)


class SequenceClock:
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

    def __call__(
        self,
    ):
        result = self.current

        self.current = (
            self.current
            + self.step
        )

        return result


class RegressingClock:
    def __init__(
        self,
    ):
        self.values = [
            BASE_TIME,
            BASE_TIME + timedelta(seconds=1),
            BASE_TIME - timedelta(seconds=1),
        ]

    def __call__(
        self,
    ):
        return self.values.pop(0)


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


class StopController:
    def __init__(
        self,
        *,
        stop_after_checks=None,
    ):
        self.checks = 0

        self.stop_after_checks = stop_after_checks

    def __call__(
        self,
    ):
        self.checks += 1

        if self.stop_after_checks is None:
            return False

        return (
            self.checks
            >= self.stop_after_checks
        )


class EvidenceWriter:
    def __init__(
        self,
        role,
    ):
        self.role = role

        self.calls = []

    def __call__(
        self,
        *,
        evidence,
    ):
        self.calls.append(
            evidence
        )

        return {
            "status": "written",
            "role": self.role,
            "write_number": len(self.calls),
        }


class ReadinessProvider:
    def __init__(
        self,
    ):
        self.calls = 0

        self.received_timestamps = []

    def __call__(
        self,
        *,
        iteration_number,
        polling_state_id,
        checked_at,
        evaluated_at,
    ):
        self.calls += 1

        self.received_timestamps.append(
            (
                checked_at,
                evaluated_at,
            )
        )

        return KalshiLiveReadReadinessRecord(
            schema_version="OLA-018",
            engine_id="OLA-018",
            readiness_id=(
                f"readiness.ola023.{iteration_number}"
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
                f"{iteration_number + 10:064x}"
            ),
            source_control_decision_hash=(
                f"{iteration_number + 20:064x}"
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
            ),
            readiness_metadata=(
                ("iteration_number", iteration_number),
                ("polling_state_id", polling_state_id),
            ),
            readiness_hash=(
                f"{iteration_number + 30:064x}"
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


class TimestampViolatingReadinessProvider:
    def __call__(
        self,
        *,
        iteration_number,
        polling_state_id,
        checked_at,
        evaluated_at,
    ):
        bad_evaluated_at = (
            evaluated_at
            + timedelta(minutes=5)
        )

        return ReadinessProvider().__call__(
            iteration_number=iteration_number,
            polling_state_id=polling_state_id,
            checked_at=checked_at,
            evaluated_at=bad_evaluated_at,
        )


class SuccessfulCycleRunner:
    def __init__(
        self,
    ):
        self.calls = 0

    def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "status": "completed",
            "source_id": SOURCE_ID,
            "adapter_id": ADAPTER_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "observation_count": 1,
            "canonical_count": 1,
            "duplicate_count": 0,
            "routed_count": 1,
            "postgresql_persistence_count": 1,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "read_only": True,
            "execution_allowed": False,
        }


class DeterministicTickBinding:
    def __init__(
        self,
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


def build_service_contract():
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
            "environment": "production",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_bootstrap_record():
    contract = OracleLiveShadowServiceBootstrapContract(
        service_contract=build_service_contract()
    )

    runtime_root = Path(
        "C:/qseries/runtime"
    )

    return contract.bootstrap(
        oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
        ola_boundaries=REQUIRED_OLA_BOUNDARIES,
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
            "environment": "production",
            "service_mode": "live_shadow",
        },
    )


def build_polling_policy():
    return ShadowPollingPolicy.create(
        policy_id="oracle.kalshi.shadow.polling.ola023",
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
            "test": "OLA-023",
        },
    )


def initial_state():
    return ShadowPollingState.create(
        state_id="polling.state.ola023.initial",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "initial",
        },
    )


def build_components(
    *,
    stop_after_checks=None,
    readiness_callable=None,
    clock_callable=None,
):
    readiness_provider = (
        ReadinessProvider()
        if readiness_callable is None
        else readiness_callable
    )

    cycle_runner = SuccessfulCycleRunner()

    polling_engine = OracleShadowPollingPolicyCadenceEngine(
        policy=build_polling_policy()
    )

    scheduler = OracleControlledShadowCollectionSchedulerTick(
        polling_engine=polling_engine,
        cycle_runner=ShadowCycleRunnerBinding(
            runner_id="runner.ola017.ola023",
            engine_id="OLA-017",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            cycle_callable=cycle_runner,
        ),
    )

    tick_binding = DeterministicTickBinding(
        scheduler
    )

    state_writer = EvidenceWriter(
        "runtime/state"
    )

    log_writer = EvidenceWriter(
        "runtime/logs"
    )

    clock = (
        SequenceClock(
            start=(
                BASE_TIME
                + timedelta(minutes=1)
            )
        )
        if clock_callable is None
        else clock_callable
    )

    sleeper = SleepRecorder()

    stop_controller = StopController(
        stop_after_checks=stop_after_checks
    )

    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=build_bootstrap_record(),
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
                provider_id=(
                    "provider.ola018.kalshi.readiness"
                ),
                engine_id="OLA-018",
                readiness_callable=readiness_provider,
            )
        ),
        scheduler=OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021.live_shadow"
            ),
            engine_id="OLA-021",
            tick_callable=tick_binding,
        ),
        state_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id="writer.runtime.state.ola023",
                evidence_role="runtime/state",
                writer_callable=state_writer,
            )
        ),
        log_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id="writer.runtime.logs.ola023",
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
        "runner": runner,
        "readiness_provider": readiness_provider,
        "cycle_runner": cycle_runner,
        "tick_binding": tick_binding,
        "state_writer": state_writer,
        "log_writer": log_writer,
        "sleeper": sleeper,
        "stop_controller": stop_controller,
    }


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
            "service_engine_id": "OLA-023",
            "iteration_number": iteration_number,
        },
        "cycle_kwargs": {
            "service_iteration_number": iteration_number,
        },
        "tick_metadata": {
            "service_engine_id": "OLA-023",
            "iteration_number": iteration_number,
        },
    }


def run_controlled_three_iteration_test():
    components = build_components()

    (
        run_record,
        iterations,
        final_state,
    ) = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=3,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
            "test_run": True,
        },
    )

    assert run_record.schema_version == "OLA-023"

    assert run_record.engine_id == "OLA-023"

    assert run_record.service_run_status == "completed"

    assert run_record.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert run_record.iteration_count == 3

    assert len(iterations) == 3

    assert components["readiness_provider"].calls == 3

    assert components["tick_binding"].calls == 3

    assert components["cycle_runner"].calls == 3

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

    assert run_record.canonical_clock_lineage_valid is True

    assert (
        run_record.readiness_timestamp_contract_preserved
        is True
    )

    assert final_state.last_cycle_succeeded is True

    assert final_state.consecutive_failures == 0

    assert final_state.suspended is False

    assert run_record.final_state_id == final_state.state_id

    assert run_record.final_state_hash == final_state.state_hash

    assert run_record.stop_requested is False

    assert run_record.separate_process_required is True

    assert run_record.alerts_allowed is False

    assert run_record.qseries_intake_allowed is False

    assert run_record.canonical_handoff_published is False

    assert run_record.read_only is True

    assert run_record.execution_allowed is False

    assert run_record.execution_adapter_resolved is False

    assert run_record.execution_adapter_invoked is False

    assert run_record.trade_authorization_allowed is False

    assert run_record.order_placement_allowed is False

    assert run_record.funds_moved is False

    assert run_record.portfolio_mutated is False

    assert run_record.verify_service_run_hash() is True

    received_timestamps = (
        components["readiness_provider"].received_timestamps
    )

    assert len(received_timestamps) == 3

    for iteration, timestamps in zip(
        iterations,
        received_timestamps,
    ):
        checked_at, evaluated_at = timestamps

        assert iteration.readiness_checked_at == checked_at

        assert iteration.readiness_evaluated_at == evaluated_at

        assert iteration.canonical_clock_lineage_valid is True

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

        assert iteration.verify_iteration_hash() is True

        assert iteration.read_only is True

        assert iteration.alert_created is False

        assert (
            iteration.qseries_intake_record_created
            is False
        )

        assert (
            iteration.canonical_handoff_published
            is False
        )

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

    return (
        run_record,
        iterations,
        final_state,
        components,
    )


def run_explicit_stop_test():
    components = build_components(
        stop_after_checks=4
    )

    (
        run_record,
        iterations,
        final_state,
    ) = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=None,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "explicit_stop",
        },
    )

    assert run_record.service_run_status == "stopped"

    assert run_record.stop_requested is True

    assert run_record.iteration_count == 2

    assert len(iterations) == 2

    assert components["readiness_provider"].calls == 2

    assert components["tick_binding"].calls == 2

    assert components["cycle_runner"].calls == 2

    assert len(components["state_writer"].calls) == 2

    assert len(components["log_writer"].calls) == 2

    assert len(components["sleeper"].calls) == 1

    assert final_state.consecutive_failures == 0

    return run_record


def run_deterministic_replay_test():
    first = build_components()

    second = build_components()

    first_result = first["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=2,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "deterministic_replay",
        },
    )

    second_result = second["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=2,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "deterministic_replay",
        },
    )

    first_run, first_iterations, first_state = first_result

    second_run, second_iterations, second_state = second_result

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


def run_readiness_timestamp_fail_closed_test():
    components = build_components(
        readiness_callable=(
            TimestampViolatingReadinessProvider()
        )
    )

    try:
        components["runner"].run(
            initial_polling_state=initial_state(),
            max_iterations=1,
            readiness_kwargs_factory=readiness_kwargs_factory,
            scheduler_kwargs_factory=scheduler_kwargs_factory,
            service_metadata={
                "test": "timestamp_violation",
            },
        )

        raise AssertionError(
            "readiness timestamp violation must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass


def run_clock_regression_fail_closed_test():
    components = build_components(
        clock_callable=RegressingClock()
    )

    try:
        components["runner"].run(
            initial_polling_state=initial_state(),
            max_iterations=1,
            readiness_kwargs_factory=readiness_kwargs_factory,
            scheduler_kwargs_factory=scheduler_kwargs_factory,
            service_metadata={
                "test": "clock_regression",
            },
        )

        raise AssertionError(
            "service clock regression must fail closed"
        )

    except OracleLiveShadowServiceRunnerContractError:
        pass


def run_binding_fail_closed_tests():
    try:
        OracleLiveShadowReadinessProviderBinding(
            provider_id="provider.invalid",
            engine_id="OLA-999",
            readiness_callable=lambda: None,
        )

        raise AssertionError(
            "non-OLA-018 provider must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass

    try:
        OracleLiveShadowSchedulerBinding(
            scheduler_id="scheduler.invalid",
            engine_id="OLA-999",
            tick_callable=lambda: None,
        )

        raise AssertionError(
            "non-OLA-021 scheduler must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass

    writer = EvidenceWriter(
        "runtime/state"
    )

    try:
        OracleLiveShadowEvidenceWriterBinding(
            writer_id="writer.invalid",
            evidence_role="runtime/data",
            writer_callable=writer,
        )

        raise AssertionError(
            "unsupported writer role must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass


def main():
    (
        run_record,
        iterations,
        final_state,
        components,
    ) = run_controlled_three_iteration_test()

    stopped_run = run_explicit_stop_test()

    run_deterministic_replay_test()

    run_readiness_timestamp_fail_closed_test()

    run_clock_regression_fail_closed_test()

    run_binding_fail_closed_tests()

    result = {
        "schema_version": run_record.schema_version,
        "engine_id": run_record.engine_id,
        "status": "passed",
        "service_run_status": (
            run_record.service_run_status
        ),
        "oracle_service_id": run_record.oracle_service_id,
        "bootstrap_schema_required": "OLA-022",
        "readiness_provider_engine_required": "OLA-018",
        "scheduler_engine_required": "OLA-021",
        "iteration_count": run_record.iteration_count,
        "readiness_provider_call_count": (
            components["readiness_provider"].calls
        ),
        "scheduler_tick_call_count": (
            components["tick_binding"].calls
        ),
        "ola_017_cycle_call_count": (
            components["cycle_runner"].calls
        ),
        "exactly_one_readiness_request_per_iteration": (
            components["readiness_provider"].calls
            == run_record.iteration_count
        ),
        "exactly_one_scheduler_tick_per_iteration": (
            components["tick_binding"].calls
            == run_record.iteration_count
        ),
        "cycle_invocation_count": (
            run_record.cycle_invocation_count
        ),
        "successful_cycle_count": (
            run_record.successful_cycle_count
        ),
        "state_evidence_write_count": (
            len(components["state_writer"].calls)
        ),
        "log_evidence_write_count": (
            len(components["log_writer"].calls)
        ),
        "controlled_sleep_call_count": (
            len(components["sleeper"].calls)
        ),
        "service_tick_interval_seconds": (
            run_record.service_tick_interval_seconds
        ),
        "canonical_clock_lineage_valid": (
            run_record.canonical_clock_lineage_valid
        ),
        "readiness_timestamps_caller_controlled": True,
        "readiness_timestamp_contract_preserved": (
            run_record.readiness_timestamp_contract_preserved
        ),
        "readiness_future_time_not_invented": True,
        "clock_regression_blocked": True,
        "readiness_timestamp_violation_blocked": True,
        "final_consecutive_failures": (
            final_state.consecutive_failures
        ),
        "final_state_suspended": final_state.suspended,
        "explicit_stop_status": (
            stopped_run.service_run_status
        ),
        "explicit_stop_observed": (
            stopped_run.stop_requested
        ),
        "deterministic_iteration_hashing": True,
        "deterministic_service_run_hashing": True,
        "deterministic_replay_valid": True,
        "separate_process_required": (
            run_record.separate_process_required
        ),
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

    print(
        "[PASS] OLA-023 Oracle Live Shadow "
        "Service Runner"
    )

    print(result)


if __name__ == "__main__":
    main()
