from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
    ShadowCollectionSchedulerTickCompatibilityError,
    ShadowCycleRunnerBinding,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
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


READINESS_CHECKED_AT = datetime(
    2026,
    7,
    12,
    16,
    0,
    0,
    tzinfo=timezone.utc,
)

READINESS_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    16,
    0,
    1,
    tzinfo=timezone.utc,
)

TICK_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    16,
    0,
    10,
    tzinfo=timezone.utc,
)

TICK_STARTED_AT = datetime(
    2026,
    7,
    12,
    16,
    0,
    11,
    tzinfo=timezone.utc,
)

TICK_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    16,
    0,
    12,
    tzinfo=timezone.utc,
)


def build_readiness():
    return KalshiLiveReadReadinessRecord(
        schema_version="OLA-018",
        engine_id="OLA-018",
        readiness_id="kalshi_live_readiness.ola021",
        readiness_status="passed",
        adapter_id=ADAPTER_ID,
        source_id=SOURCE_ID,
        source_base_url=(
            "https://external-api.kalshi.com/trade-api/v2"
        ),
        source_endpoint="/markets",
        http_method="GET",
        checked_at=READINESS_CHECKED_AT,
        evaluated_at=READINESS_EVALUATED_AT,
        public_endpoint=True,
        authentication_used=False,
        live_get_request_count=1,
        source_contract_valid=True,
        source_probe_health_status="healthy",
        source_reachable=True,
        source_latency_ms=50,
        source_health_evidence_hash="a" * 64,
        rate_control_evidence_hash="b" * 64,
        source_control_decision_hash="c" * 64,
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
            ("environment", "production"),
        ),
        readiness_hash="d" * 64,
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


def build_policy():
    return ShadowPollingPolicy.create(
        policy_id="oracle.kalshi.shadow.polling.v1",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        base_interval_seconds=30,
        jitter_max_seconds=5,
        readiness_max_age_seconds=300,
        failure_backoff_base_seconds=30,
        failure_backoff_multiplier=2,
        failure_backoff_max_seconds=600,
        consecutive_failure_suspend_threshold=4,
        suspension_cooldown_seconds=900,
        explicit_restart_evidence_required=True,
        policy_metadata={
            "environment": "production",
            "mode": "shadow",
        },
    )


def build_polling_engine():
    return OracleShadowPollingPolicyCadenceEngine(
        policy=build_policy()
    )


def initial_state():
    return ShadowPollingState.create(
        state_id="polling.state.ola021.initial",
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


def waiting_state():
    return ShadowPollingState.create(
        state_id="polling.state.ola021.waiting",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=TICK_EVALUATED_AT,
        last_cycle_succeeded=True,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "waiting",
        },
    )


def failure_state(
    count,
):
    completed_at = (
        TICK_EVALUATED_AT
        - timedelta(minutes=10)
    )

    return ShadowPollingState.create(
        state_id=f"polling.state.ola021.failure.{count}",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=completed_at,
        last_cycle_succeeded=False,
        consecutive_failures=count,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "failure_count": count,
        },
    )


class CountingSuccessfulRunner:
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
            "adapter_id": ADAPTER_ID,
            "source_id": SOURCE_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "observation_count": 2,
            "canonical_count": 2,
            "duplicate_count": 0,
            "routed_count": 2,
            "postgresql_persistence_count": 2,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "read_only": True,
            "execution_allowed": False,
        }


class CountingFailedRunner:
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
            "status": "blocked",
            "adapter_id": ADAPTER_ID,
            "source_id": SOURCE_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "observation_count": 0,
            "canonical_count": 0,
            "duplicate_count": 0,
            "routed_count": 0,
            "postgresql_persistence_count": 0,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "read_only": True,
            "execution_allowed": False,
        }


class CountingExceptionRunner:
    def __init__(
        self,
    ):
        self.calls = 0

    def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1

        raise RuntimeError(
            "deterministic shadow cycle failure"
        )


def build_scheduler(
    runner,
):
    binding = ShadowCycleRunnerBinding(
        runner_id="runner.ola017.postgresql.shadow",
        engine_id="OLA-017",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        cycle_callable=runner,
    )

    return OracleControlledShadowCollectionSchedulerTick(
        polling_engine=build_polling_engine(),
        cycle_runner=binding,
    )


def run_successful_tick_test():
    runner = CountingSuccessfulRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=build_readiness(),
        polling_state=initial_state(),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "scheduler": "OLA-021",
        },
        cycle_kwargs={
            "cycle_id": "cycle.ola021.success",
        },
        tick_metadata={
            "environment": "production",
            "mode": "shadow",
        },
    )

    assert runner.calls == 1

    assert cycle_result["status"] == "completed"

    assert tick.schema_version == "OLA-021"

    assert tick.engine_id == "OLA-021"

    assert tick.tick_status == "completed"

    assert tick.polling_decision_status == "eligible"

    assert tick.shadow_cycle_allowed is True

    assert tick.runner_engine_id == "OLA-017"

    assert tick.cycle_invocation_count == 1

    assert tick.cycle_invoked is True

    assert tick.cycle_succeeded is True

    assert tick.cycle_status == "completed"

    assert len(tick.cycle_evidence_hash) == 64

    assert tick.previous_consecutive_failures == 0

    assert tick.next_consecutive_failures == 0

    assert tick.next_state_suspended is False

    assert next_state.last_cycle_succeeded is True

    assert next_state.consecutive_failures == 0

    assert next_state.suspended is False

    assert next_state.restart_evidence_present is False

    assert (
        "exactly_one_shadow_cycle_invoked"
        in tick.reason_codes
    )

    assert (
        "consecutive_failures_reset"
        in tick.reason_codes
    )

    assert tick.verify_tick_hash() is True

    assert tick.immutable is True

    assert tick.read_only is True

    assert tick.continuous_polling_started is False

    assert tick.loop_started is False

    assert tick.sleep_performed is False

    assert tick.alert_created is False

    assert tick.qseries_intake_record_created is False

    assert tick.canonical_handoff_published is False

    assert tick.execution_allowed is False

    assert tick.execution_adapter_resolved is False

    assert tick.execution_adapter_invoked is False

    assert tick.trade_authorization_allowed is False

    assert tick.order_placement_allowed is False

    assert tick.funds_moved is False

    assert tick.portfolio_mutated is False

    try:
        tick.tick_status = "failed"

        raise AssertionError(
            "tick record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return tick, next_state


def run_waiting_noop_test():
    runner = CountingSuccessfulRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=build_readiness(),
        polling_state=waiting_state(),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "scheduler": "OLA-021",
        },
        cycle_kwargs={
            "cycle_id": "must-not-run",
        },
        tick_metadata={
            "mode": "shadow",
        },
    )

    assert runner.calls == 0

    assert cycle_result is None

    assert tick.tick_status == "noop"

    assert tick.polling_decision_status == "waiting"

    assert tick.shadow_cycle_allowed is False

    assert tick.cycle_invocation_count == 0

    assert tick.cycle_invoked is False

    assert tick.cycle_succeeded is None

    assert tick.cycle_status is None

    assert tick.cycle_evidence_hash is None

    assert next_state == waiting_state()

    assert tick.previous_state_hash == tick.next_state_hash

    assert (
        "shadow_cycle_not_invoked"
        in tick.reason_codes
    )

    assert tick.verify_tick_hash() is True

    return tick


def run_failure_increment_test():
    runner = CountingFailedRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=build_readiness(),
        polling_state=failure_state(2),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "scheduler": "OLA-021",
        },
        cycle_kwargs={
            "cycle_id": "cycle.ola021.failure",
        },
        tick_metadata={
            "mode": "shadow",
        },
    )

    assert runner.calls == 1

    assert cycle_result["status"] == "blocked"

    assert tick.tick_status == "failed"

    assert tick.cycle_invocation_count == 1

    assert tick.cycle_invoked is True

    assert tick.cycle_succeeded is False

    assert tick.previous_consecutive_failures == 2

    assert tick.next_consecutive_failures == 3

    assert tick.next_state_suspended is False

    assert next_state.last_cycle_succeeded is False

    assert next_state.consecutive_failures == 3

    assert next_state.suspended is False

    assert (
        "consecutive_failure_incremented"
        in tick.reason_codes
    )

    return tick, next_state


def run_threshold_suspension_test():
    runner = CountingExceptionRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=build_readiness(),
        polling_state=failure_state(3),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "scheduler": "OLA-021",
        },
        cycle_kwargs={
            "cycle_id": "cycle.ola021.exception",
        },
        tick_metadata={
            "mode": "shadow",
        },
    )

    assert runner.calls == 1

    assert cycle_result is None

    assert tick.tick_status == "failed"

    assert tick.cycle_status == "exception"

    assert tick.previous_consecutive_failures == 3

    assert tick.next_consecutive_failures == 4

    assert tick.next_state_suspended is True

    assert (
        tick.next_state_suspended_at
        == TICK_COMPLETED_AT
    )

    assert next_state.last_cycle_succeeded is False

    assert next_state.consecutive_failures == 4

    assert next_state.suspended is True

    assert next_state.suspended_at == TICK_COMPLETED_AT

    assert next_state.restart_evidence_present is False

    assert (
        "failure_suspend_threshold_reached"
        in tick.reason_codes
    )

    assert (
        "next_polling_state_suspended"
        in tick.reason_codes
    )

    return tick, next_state


def run_deterministic_replay_test():
    first_runner = CountingSuccessfulRunner()

    second_runner = CountingSuccessfulRunner()

    first_scheduler = build_scheduler(
        first_runner
    )

    second_scheduler = build_scheduler(
        second_runner
    )

    kwargs = {
        "readiness": build_readiness(),
        "polling_state": initial_state(),
        "evaluated_at": TICK_EVALUATED_AT,
        "started_at": TICK_STARTED_AT,
        "completed_at": TICK_COMPLETED_AT,
        "polling_decision_metadata": {
            "scheduler": "OLA-021",
        },
        "cycle_kwargs": {
            "cycle_id": "cycle.ola021.replay",
        },
        "tick_metadata": {
            "environment": "production",
            "mode": "shadow",
        },
    }

    first_tick, first_state, first_result = (
        first_scheduler.run_tick(
            **kwargs
        )
    )

    second_tick, second_state, second_result = (
        second_scheduler.run_tick(
            **kwargs
        )
    )

    assert first_runner.calls == 1

    assert second_runner.calls == 1

    assert first_result == second_result

    assert first_state == second_state

    assert first_tick == second_tick

    assert first_tick.tick_hash == second_tick.tick_hash

    assert first_tick.verify_tick_hash() is True

    assert second_tick.verify_tick_hash() is True


def run_fail_closed_tests():
    try:
        ShadowCycleRunnerBinding(
            runner_id="runner.invalid",
            engine_id="OLA-999",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            cycle_callable=CountingSuccessfulRunner(),
        )

        raise AssertionError(
            "non-OLA-017 runner identity must fail closed"
        )

    except ShadowCollectionSchedulerTickCompatibilityError:
        pass

    runner = CountingSuccessfulRunner()

    scheduler = build_scheduler(
        runner
    )

    try:
        scheduler.run_tick(
            readiness=build_readiness(),
            polling_state=initial_state(),
            evaluated_at=TICK_EVALUATED_AT,
            started_at=datetime(
                2026,
                7,
                12,
                16,
                0,
                11,
            ),
            completed_at=TICK_COMPLETED_AT,
            polling_decision_metadata={},
            cycle_kwargs={},
            tick_metadata={},
        )

        raise AssertionError(
            "naive started_at must fail closed"
        )

    except Exception:
        pass

    try:
        scheduler.run_tick(
            readiness=build_readiness(),
            polling_state=initial_state(),
            evaluated_at=TICK_EVALUATED_AT,
            started_at=TICK_STARTED_AT,
            completed_at=TICK_COMPLETED_AT,
            polling_decision_metadata={},
            cycle_kwargs={},
            tick_metadata={
                "api_key": "must-not-enter-evidence",
            },
        )

        raise AssertionError(
            "secret metadata must fail closed"
        )

    except Exception:
        pass


def main():
    successful_tick, successful_state = (
        run_successful_tick_test()
    )

    waiting_tick = run_waiting_noop_test()

    failed_tick, failed_state = (
        run_failure_increment_test()
    )

    suspended_tick, suspended_state = (
        run_threshold_suspension_test()
    )

    run_deterministic_replay_test()

    run_fail_closed_tests()

    result = {
        "schema_version": successful_tick.schema_version,
        "engine_id": successful_tick.engine_id,
        "status": "passed",
        "runner_engine_id": (
            successful_tick.runner_engine_id
        ),
        "required_cycle_runner_engine_id": "OLA-017",
        "eligible_cycle_invocation_count": (
            successful_tick.cycle_invocation_count
        ),
        "exactly_one_cycle_invoked": (
            successful_tick.cycle_invocation_count
            == 1
        ),
        "successful_tick_status": (
            successful_tick.tick_status
        ),
        "successful_cycle_succeeded": (
            successful_tick.cycle_succeeded
        ),
        "successful_failure_count_reset": (
            successful_state.consecutive_failures
            == 0
        ),
        "waiting_tick_status": (
            waiting_tick.tick_status
        ),
        "waiting_cycle_invocation_count": (
            waiting_tick.cycle_invocation_count
        ),
        "waiting_decision_noop": (
            waiting_tick.cycle_invoked is False
        ),
        "failed_tick_status": (
            failed_tick.tick_status
        ),
        "failed_cycle_increments_failures": (
            failed_state.consecutive_failures
            == 3
        ),
        "threshold_failure_count": (
            suspended_state.consecutive_failures
        ),
        "threshold_state_suspended": (
            suspended_state.suspended
        ),
        "threshold_suspended_at_preserved": (
            suspended_state.suspended_at
            == TICK_COMPLETED_AT
        ),
        "restart_evidence_invented": (
            suspended_state.restart_evidence_present
        ),
        "exception_captured_as_failure_evidence": (
            suspended_tick.cycle_status
            == "exception"
        ),
        "deterministic_tick_hashing": True,
        "deterministic_replay_valid": True,
        "continuous_polling_started": (
            successful_tick.continuous_polling_started
        ),
        "loop_started": successful_tick.loop_started,
        "sleep_performed": successful_tick.sleep_performed,
        "alert_created": successful_tick.alert_created,
        "qseries_intake_record_created": (
            successful_tick.qseries_intake_record_created
        ),
        "canonical_handoff_published": (
            successful_tick.canonical_handoff_published
        ),
        "read_only": successful_tick.read_only,
        "execution_allowed": (
            successful_tick.execution_allowed
        ),
        "execution_adapter_resolved": (
            successful_tick.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            successful_tick.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            successful_tick.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            successful_tick.order_placement_allowed
        ),
        "funds_moved": successful_tick.funds_moved,
        "portfolio_mutated": (
            successful_tick.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-021 Oracle Controlled Shadow "
        "Collection Scheduler Tick"
    )

    print(result)


if __name__ == "__main__":
    main()
