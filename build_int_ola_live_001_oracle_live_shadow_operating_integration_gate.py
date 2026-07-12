from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_int_ola_live_001_oracle_live_shadow_operating_integration_gate.py"
)


TEST_CONTENT = r'''
"""
INT-OLA-LIVE-001
Oracle Live Shadow Operating Integration Gate

Full controlled live-shadow operating integration gate for:

OLA-016
Oracle Kalshi Public Market Shadow Source Adapter

OLA-017
Oracle PostgreSQL Shadow Acquisition Cycle Orchestrator boundary

OLA-018
Oracle Kalshi Live Read Readiness Gate

OLA-019
Oracle Shadow Polling Policy and Cadence Engine

OLA-020
Oracle Service Isolation and Canonical Intelligence Handoff Contract

OLA-021
Oracle Controlled Shadow Collection Scheduler Tick

This gate proves:

SOURCE
    |
READINESS
    |
POLLING POLICY
    |
ONE GOVERNED SCHEDULER TICK
    |
OLA-017 BOUND CYCLE IDENTITY
    |
NEXT IMMUTABLE POLLING STATE

Permanent integration rules:

- Kalshi source identity is preserved.
- OLA-016 stays in shadow mode.
- OLA-018 readiness must pass.
- OLA-019 must explicitly permit the cycle.
- OLA-021 may invoke exactly one OLA-017-bound runner.
- Waiting state must invoke zero cycles.
- Failure state must increment consecutive failures.
- Threshold failure must suspend the next state.
- Oracle/Q Series service isolation remains intact.
- No handoff is published by collection scheduling.
- Alerts remain disabled.
- Q Series intake remains disabled.
- No execution capability exists.
- Deterministic replay is required.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthPolicy,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
    ShadowCycleRunnerBinding,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    OracleKalshiLiveReadReadinessGate,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    ADAPTER_ID,
    PRODUCTION_BASE_URL,
    SOURCE_ID,
    OracleKalshiPublicMarketShadowSourceAdapter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (
    ENGINE_ID as OLA_017_ENGINE_ID,
    SCHEMA_VERSION as OLA_017_SCHEMA_VERSION,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingState,
)


SCHEMA_VERSION = "INT-OLA-LIVE-001"
ENGINE_ID = "INT-OLA-LIVE-001"


CHECKED_AT = datetime(
    2026,
    7,
    12,
    17,
    0,
    0,
    tzinfo=timezone.utc,
)

READINESS_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    17,
    0,
    1,
    tzinfo=timezone.utc,
)

TICK_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    17,
    0,
    10,
    tzinfo=timezone.utc,
)

TICK_STARTED_AT = datetime(
    2026,
    7,
    12,
    17,
    0,
    11,
    tzinfo=timezone.utc,
)

TICK_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    17,
    0,
    12,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = CHECKED_AT


class DeterministicKalshiFetcher:
    def __init__(self):
        self.calls = []

    def __call__(
        self,
        *,
        url,
        timeout_seconds,
    ):
        self.calls.append(
            {
                "url": url,
                "timeout_seconds": timeout_seconds,
            }
        )

        return (
            200,
            (
                '{"markets":['
                '{'
                '"ticker":"KXBTC-26JUL12-116000",'
                '"event_ticker":"KXBTC",'
                '"market_type":"binary",'
                '"title":"Bitcoin above 116000",'
                '"subtitle":"BTC price",'
                '"status":"open",'
                '"yes_bid":30,'
                '"yes_ask":31,'
                '"no_bid":68,'
                '"no_ask":69,'
                '"last_price":31,'
                '"open_time":"2026-07-12T00:00:00Z",'
                '"close_time":"2026-07-12T23:00:00Z",'
                '"expiration_time":"2026-07-12T23:00:00Z",'
                '"latest_expiration_time":"2026-07-12T23:00:00Z"'
                '}'
                '],"cursor":""}'
            ),
        )


class SuccessfulOLA017BoundaryRunner:
    def __init__(self):
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
            "schema_version": OLA_017_SCHEMA_VERSION,
            "engine_id": OLA_017_ENGINE_ID,
            "status": "completed",
            "adapter_id": ADAPTER_ID,
            "source_id": SOURCE_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "bootstrap_live_write_ready": True,
            "source_control_allowed_cycle_invoked": True,
            "source_control_blocked_cycle_invoked": False,
            "observation_count": 1,
            "canonical_count": 1,
            "duplicate_count": 0,
            "routed_count": 1,
            "postgresql_routing_record_delta": 1,
            "first_persistence_sequence_number": 1,
            "last_persistence_sequence_number": 1,
            "postgresql_persistence_count": 1,
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


class FailedOLA017BoundaryRunner:
    def __init__(self):
        self.calls = 0

    def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1

        return {
            "schema_version": OLA_017_SCHEMA_VERSION,
            "engine_id": OLA_017_ENGINE_ID,
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


def build_source_control_engine():
    return OracleAcquisitionSourceControlEngine(
        source_policies={
            SOURCE_ID: (
                SourceHealthPolicy.create(
                    policy_id=(
                        "health.kalshi.int_ola_live_001.v1"
                    ),
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=0,
                    max_latency_ms=10000,
                ),
                RateControlPolicy.create(
                    policy_id=(
                        "rate.kalshi.int_ola_live_001.v1"
                    ),
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=10,
                ),
            )
        }
    )


def build_adapter(
    fetcher,
):
    return OracleKalshiPublicMarketShadowSourceAdapter(
        market_status="open",
        page_limit=1,
        max_pages=1,
        timeout_seconds=20,
        base_url=PRODUCTION_BASE_URL,
        http_fetcher=fetcher,
    )


def build_readiness(
    *,
    adapter,
):
    gate = OracleKalshiLiveReadReadinessGate(
        shadow_adapter=adapter,
        source_control_engine=(
            build_source_control_engine()
        ),
    )

    rate_window = RateWindowObservation.create(
        source_id=SOURCE_ID,
        checked_at=CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=0,
        metadata={
            "integration_gate": ENGINE_ID,
            "readiness_probe_reserved": True,
        },
    )

    return gate.evaluate(
        checked_at=CHECKED_AT,
        evaluated_at=READINESS_EVALUATED_AT,
        measured_latency_ms=1,
        consecutive_failures=0,
        rate_window_observation=rate_window,
        readiness_metadata={
            "integration_gate": ENGINE_ID,
            "environment": "production",
        },
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "stage": "readiness",
        },
        audit_metadata={
            "integration_gate": ENGINE_ID,
            "audit_id": "audit.int.ola.live.001",
        },
    )


def build_policy():
    return ShadowPollingPolicy.create(
        policy_id=(
            "oracle.kalshi.shadow.polling."
            "int_ola_live_001.v1"
        ),
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
            "integration_gate": ENGINE_ID,
            "mode": "shadow",
        },
    )


def build_polling_engine():
    return OracleShadowPollingPolicyCadenceEngine(
        policy=build_policy()
    )


def initial_state():
    return ShadowPollingState.create(
        state_id="polling.state.int.ola.live.001.initial",
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


def waiting_state():
    return ShadowPollingState.create(
        state_id="polling.state.int.ola.live.001.waiting",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=TICK_EVALUATED_AT,
        last_cycle_succeeded=True,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "integration_gate": ENGINE_ID,
            "state": "waiting",
        },
    )


def failure_state(
    count,
):
    return ShadowPollingState.create(
        state_id=(
            f"polling.state.int.ola.live.001.failure.{count}"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=(
            TICK_EVALUATED_AT
            - timedelta(minutes=10)
        ),
        last_cycle_succeeded=False,
        consecutive_failures=count,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "integration_gate": ENGINE_ID,
            "failure_count": count,
        },
    )


def build_scheduler(
    runner,
):
    binding = ShadowCycleRunnerBinding(
        runner_id=(
            "runner.ola017.int_ola_live_001"
        ),
        engine_id=OLA_017_ENGINE_ID,
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        cycle_callable=runner,
    )

    return OracleControlledShadowCollectionSchedulerTick(
        polling_engine=build_polling_engine(),
        cycle_runner=binding,
    )


def run_success_path():
    fetcher = DeterministicKalshiFetcher()

    adapter = build_adapter(
        fetcher
    )

    readiness = build_readiness(
        adapter=adapter
    )

    runner = SuccessfulOLA017BoundaryRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=readiness,
        polling_state=initial_state(),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "integration_gate": ENGINE_ID,
            "stage": "polling_decision",
        },
        cycle_kwargs={
            "integration_cycle_id": (
                "cycle.int.ola.live.001.success"
            ),
        },
        tick_metadata={
            "integration_gate": ENGINE_ID,
            "stage": "scheduler_tick",
        },
    )

    assert len(fetcher.calls) == 1

    assert readiness.schema_version == "OLA-018"

    assert readiness.readiness_status == "passed"

    assert readiness.source_id == SOURCE_ID

    assert readiness.adapter_id == ADAPTER_ID

    assert readiness.source_contract_valid is True

    assert readiness.source_reachable is True

    assert (
        readiness.source_probe_health_status
        == "healthy"
    )

    assert (
        readiness.source_control_acquisition_allowed
        is True
    )

    assert (
        readiness.live_shadow_cycle_entry_ready
        is True
    )

    assert readiness.shadow_mode is True

    assert readiness.alerts_allowed is False

    assert readiness.qseries_intake_allowed is False

    assert runner.calls == 1

    assert len(runner.kwargs) == 1

    assert tick.schema_version == "OLA-021"

    assert tick.tick_status == "completed"

    assert tick.polling_decision_status == "eligible"

    assert tick.shadow_cycle_allowed is True

    assert tick.runner_engine_id == OLA_017_ENGINE_ID

    assert tick.cycle_invocation_count == 1

    assert tick.cycle_invoked is True

    assert tick.cycle_succeeded is True

    assert tick.cycle_status == "completed"

    assert cycle_result["schema_version"] == "OLA-017"

    assert cycle_result["engine_id"] == "OLA-017"

    assert cycle_result["status"] == "completed"

    assert cycle_result["shadow_mode"] is True

    assert cycle_result["alerts_allowed"] is False

    assert cycle_result["qseries_intake_allowed"] is False

    assert cycle_result["read_only"] is True

    assert cycle_result["execution_allowed"] is False

    assert next_state.last_cycle_succeeded is True

    assert next_state.consecutive_failures == 0

    assert next_state.suspended is False

    assert next_state.restart_evidence_present is False

    assert tick.verify_tick_hash() is True

    assert adapter.last_acquisition_evidence is None

    return (
        readiness,
        tick,
        next_state,
        cycle_result,
    )


def run_waiting_noop_path():
    fetcher = DeterministicKalshiFetcher()

    adapter = build_adapter(
        fetcher
    )

    readiness = build_readiness(
        adapter=adapter
    )

    runner = SuccessfulOLA017BoundaryRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=readiness,
        polling_state=waiting_state(),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "integration_gate": ENGINE_ID,
        },
        cycle_kwargs={
            "integration_cycle_id": "must-not-run",
        },
        tick_metadata={
            "integration_gate": ENGINE_ID,
        },
    )

    assert runner.calls == 0

    assert cycle_result is None

    assert tick.tick_status == "noop"

    assert tick.polling_decision_status == "waiting"

    assert tick.shadow_cycle_allowed is False

    assert tick.cycle_invocation_count == 0

    assert tick.cycle_invoked is False

    assert next_state == waiting_state()

    assert tick.previous_state_hash == tick.next_state_hash

    return tick


def run_failure_path():
    fetcher = DeterministicKalshiFetcher()

    adapter = build_adapter(
        fetcher
    )

    readiness = build_readiness(
        adapter=adapter
    )

    runner = FailedOLA017BoundaryRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=readiness,
        polling_state=failure_state(2),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "integration_gate": ENGINE_ID,
        },
        cycle_kwargs={
            "integration_cycle_id": (
                "cycle.int.ola.live.001.failure"
            ),
        },
        tick_metadata={
            "integration_gate": ENGINE_ID,
        },
    )

    assert runner.calls == 1

    assert cycle_result["status"] == "blocked"

    assert tick.tick_status == "failed"

    assert tick.cycle_invocation_count == 1

    assert tick.cycle_succeeded is False

    assert tick.previous_consecutive_failures == 2

    assert tick.next_consecutive_failures == 3

    assert next_state.consecutive_failures == 3

    assert next_state.suspended is False

    return tick, next_state


def run_threshold_suspension_path():
    fetcher = DeterministicKalshiFetcher()

    adapter = build_adapter(
        fetcher
    )

    readiness = build_readiness(
        adapter=adapter
    )

    runner = FailedOLA017BoundaryRunner()

    scheduler = build_scheduler(
        runner
    )

    tick, next_state, cycle_result = scheduler.run_tick(
        readiness=readiness,
        polling_state=failure_state(3),
        evaluated_at=TICK_EVALUATED_AT,
        started_at=TICK_STARTED_AT,
        completed_at=TICK_COMPLETED_AT,
        polling_decision_metadata={
            "integration_gate": ENGINE_ID,
        },
        cycle_kwargs={
            "integration_cycle_id": (
                "cycle.int.ola.live.001.threshold"
            ),
        },
        tick_metadata={
            "integration_gate": ENGINE_ID,
        },
    )

    assert runner.calls == 1

    assert cycle_result["status"] == "blocked"

    assert tick.tick_status == "failed"

    assert tick.next_consecutive_failures == 4

    assert tick.next_state_suspended is True

    assert (
        tick.next_state_suspended_at
        == TICK_COMPLETED_AT
    )

    assert next_state.consecutive_failures == 4

    assert next_state.suspended is True

    assert next_state.suspended_at == TICK_COMPLETED_AT

    assert next_state.restart_evidence_present is False

    return tick, next_state


def run_service_isolation_path():
    contract = OracleQSeriesServiceIsolationContract.create(
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
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )

    assert contract.schema_version == "OLA-020"

    assert contract.separate_process_required is True

    assert (
        contract.direct_execution_import_allowed
        is False
    )

    assert contract.oracle_execution_authority is False

    assert (
        contract.qseries_oracle_history_mutation_allowed
        is False
    )

    assert contract.immutable_handoff_required is True

    assert (
        contract.durable_handoff_boundary_required
        is True
    )

    assert (
        contract.independent_qseries_validation_required
        is True
    )

    assert contract.read_only is True

    assert contract.execution_allowed is False

    return contract


def run_deterministic_replay_path():
    first = run_success_path()

    second = run_success_path()

    first_readiness, first_tick, first_state, first_cycle = (
        first
    )

    (
        second_readiness,
        second_tick,
        second_state,
        second_cycle,
    ) = second

    assert first_readiness == second_readiness

    assert (
        first_readiness.readiness_hash
        == second_readiness.readiness_hash
    )

    assert first_tick == second_tick

    assert first_tick.tick_hash == second_tick.tick_hash

    assert first_state == second_state

    assert first_state.state_hash == second_state.state_hash

    assert first_cycle == second_cycle


def main():
    assert OLA_017_SCHEMA_VERSION == "OLA-017"

    assert OLA_017_ENGINE_ID == "OLA-017"

    (
        readiness,
        successful_tick,
        successful_state,
        cycle_result,
    ) = run_success_path()

    waiting_tick = run_waiting_noop_path()

    failed_tick, failed_state = run_failure_path()

    suspended_tick, suspended_state = (
        run_threshold_suspension_path()
    )

    service_contract = run_service_isolation_path()

    run_deterministic_replay_path()

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_016_source_adapter_passed": True,
        "ola_017_cycle_boundary_passed": True,
        "ola_018_readiness_passed": True,
        "ola_019_polling_policy_passed": True,
        "ola_020_service_isolation_passed": True,
        "ola_021_scheduler_tick_passed": True,
        "source_id": readiness.source_id,
        "adapter_id": readiness.adapter_id,
        "source_contract_valid": (
            readiness.source_contract_valid
        ),
        "source_probe_health_status": (
            readiness.source_probe_health_status
        ),
        "source_reachable": readiness.source_reachable,
        "live_shadow_cycle_entry_ready": (
            readiness.live_shadow_cycle_entry_ready
        ),
        "eligible_tick_status": (
            successful_tick.tick_status
        ),
        "eligible_cycle_invocation_count": (
            successful_tick.cycle_invocation_count
        ),
        "exactly_one_cycle_invoked": (
            successful_tick.cycle_invocation_count
            == 1
        ),
        "ola_017_schema_verified": (
            cycle_result["schema_version"]
            == "OLA-017"
        ),
        "ola_017_engine_verified": (
            cycle_result["engine_id"]
            == "OLA-017"
        ),
        "successful_state_failure_count": (
            successful_state.consecutive_failures
        ),
        "waiting_tick_status": waiting_tick.tick_status,
        "waiting_cycle_invocation_count": (
            waiting_tick.cycle_invocation_count
        ),
        "waiting_noop_valid": (
            waiting_tick.cycle_invoked is False
        ),
        "failed_tick_status": failed_tick.tick_status,
        "failure_count_incremented": (
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
        "separate_process_required": (
            service_contract.separate_process_required
        ),
        "oracle_execution_authority": (
            service_contract.oracle_execution_authority
        ),
        "direct_execution_import_allowed": (
            service_contract.direct_execution_import_allowed
        ),
        "deterministic_readiness_replay": True,
        "deterministic_tick_replay": True,
        "deterministic_state_replay": True,
        "shadow_mode": cycle_result["shadow_mode"],
        "alerts_allowed": cycle_result["alerts_allowed"],
        "qseries_intake_allowed": (
            cycle_result["qseries_intake_allowed"]
        ),
        "canonical_handoff_published": (
            successful_tick.canonical_handoff_published
        ),
        "continuous_polling_started": (
            successful_tick.continuous_polling_started
        ),
        "loop_started": successful_tick.loop_started,
        "sleep_performed": successful_tick.sleep_performed,
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

    assert result["ola_016_source_adapter_passed"] is True

    assert result["ola_017_cycle_boundary_passed"] is True

    assert result["ola_018_readiness_passed"] is True

    assert result["ola_019_polling_policy_passed"] is True

    assert result["ola_020_service_isolation_passed"] is True

    assert result["ola_021_scheduler_tick_passed"] is True

    assert result["exactly_one_cycle_invoked"] is True

    assert result["waiting_cycle_invocation_count"] == 0

    assert result["threshold_state_suspended"] is True

    assert result["restart_evidence_invented"] is False

    assert result["separate_process_required"] is True

    assert result["oracle_execution_authority"] is False

    assert result["direct_execution_import_allowed"] is False

    assert result["shadow_mode"] is True

    assert result["alerts_allowed"] is False

    assert result["qseries_intake_allowed"] is False

    assert result["canonical_handoff_published"] is False

    assert result["continuous_polling_started"] is False

    assert result["loop_started"] is False

    assert result["sleep_performed"] is False

    assert result["read_only"] is True

    assert result["execution_allowed"] is False

    assert result["execution_adapter_resolved"] is False

    assert result["execution_adapter_invoked"] is False

    assert result["trade_authorization_allowed"] is False

    assert result["order_placement_allowed"] is False

    assert result["funds_moved"] is False

    assert result["portfolio_mutated"] is False

    print(
        "[PASS] INT-OLA-LIVE-001 Oracle Live Shadow "
        "Operating Integration Gate"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


def write_file(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def main() -> None:
    print("========================================")
    print(" INT-OLA-LIVE-001 INSTALLER")
    print(" Oracle Live Shadow Operating")
    print(" OLA-016 Through OLA-021")
    print(" Integration Gate")
    print("========================================")

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print("[DONE] INT-OLA-LIVE-001 installed")
    print()
    print("Run:")
    print(
        "py test_int_ola_live_001_oracle_live_shadow_"
        "operating_integration_gate.py"
    )


if __name__ == "__main__":
    main()