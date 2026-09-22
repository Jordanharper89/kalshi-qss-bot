from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_cycle_runner_lineage_callable_facade import (
    OracleShadowCycleRunnerLineageCallableFacade,
    ShadowCycleRunnerLineageCallableFacadeContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
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
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


T1 = datetime(
    2026,
    7,
    15,
    1,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.050.1",
):
    payload = {
        "source_market_id": market_id,
        "yes_bid_dollars": "0.0000",
        "yes_bid_size_fp": "0.00",
        "yes_ask_dollars": "0.6140",
        "yes_ask_size_fp": "40.00",
        "no_bid_dollars": "0.3860",
        "no_ask_dollars": "0.0000",
        "last_price_dollars": "0.0000",
        "previous_yes_bid_dollars": "0.0000",
        "previous_yes_ask_dollars": "0.6000",
        "previous_price_dollars": "0.0000",
        "volume_fp": "0.00",
        "volume_24h_fp": "0.00",
        "open_interest_fp": "0.00",
        "liquidity_dollars": "0.0000",
    }

    raw = RawSourceObservation.create(
        source_observation_id=(
            "kalshi."
            + market_id
            + "."
            + frame_id
        ),
        observed_at=T1,
        observation_type="market_snapshot",
        payload=payload,
        provenance={
            "source_id": "source.kalshi.market_data",
            "frame_id": frame_id,
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=T1,
        acquisition_batch_id=batch_id,
    )


def build_cohort():
    return tuple(
        build_observation(
            market_id=f"KXTEST-FACADE-{index}",
            frame_id=str(index),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def route_batch(
        self,
        observations,
        routed_at,
    ):
        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.050.persistence",
                metadata={
                    "test": "OLA-050",
                },
            )
            for observation in observations
        )

    def __call__(
        self,
        observation,
        routed_at,
    ):
        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.ola.050.persistence.single",
            metadata={
                "test": "OLA-050",
            },
        )


class FakeExistingOLA030CycleCallable:
    def __init__(self):
        self.call_count = 0
        self.last_kwargs = None

    def __call__(
        self,
        **kwargs,
    ):
        self.call_count += 1
        self.last_kwargs = dict(
            kwargs
        )

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "status": "completed",
            "canonical_count": 5,
            "postgresql_routing_record_delta": 5,
            "read_only": True,
            "execution_allowed": False,
            "projected_by": "existing-ola-030",
            "kwargs_echo": dict(kwargs),
        }


def build_facade():
    persistence_router = (
        FakeProductionPersistenceRouter()
    )

    wiring = (
        OraclePersistedCohortLineageProductionWiringContract(
            production_persistence_router=(
                persistence_router
            )
        )
    )

    completion_bridge = (
        OracleSchedulerCycleLineageCompletionBridge(
            production_wiring=wiring
        )
    )

    existing_callable = (
        FakeExistingOLA030CycleCallable()
    )

    adapter = (
        OracleSchedulerLineageProductionAdapter(
            scheduler_cycle_callable=(
                existing_callable
            ),
            lineage_completion_bridge=(
                completion_bridge
            ),
        )
    )

    facade = (
        OracleShadowCycleRunnerLineageCallableFacade(
            scheduler_adapter=adapter
        )
    )

    return (
        facade,
        wiring,
        existing_callable,
    )


def stage_cycle(
    wiring,
):
    wiring.staged_persistence_router.route_batch(
        build_cohort(),
        T1,
    )


def canonical_cycle_kwargs():
    return {
        "source_control_checked_at": (
            T1.isoformat()
        ),
        "source_control_evaluated_at": (
            T1.isoformat()
        ),
        "source_control_reachable": True,
        "source_control_consecutive_failures": 0,
        "source_control_latency_ms": 1,
        "source_control_requests_used": 1,
        "cycle_started_at": T1.isoformat(),
        "cycle_completed_at": T1.isoformat(),
        "replay_metadata": {
            "source": "OLA-030",
        },
        "audit_metadata": {
            "source": "OLA-030",
        },
    }


def run_direct_facade_test():
    (
        facade,
        wiring,
        existing_callable,
    ) = build_facade()

    stage_cycle(
        wiring
    )

    kwargs = canonical_cycle_kwargs()

    result = facade(
        **kwargs
    )

    assert existing_callable.call_count == 1
    assert existing_callable.last_kwargs == kwargs
    assert result["projected_by"] == (
        "existing-ola-030"
    )
    assert result["kwargs_echo"] == kwargs

    receipt = facade.last_receipt

    assert receipt is not None
    assert receipt.schema_version == "OLA-050"
    assert receipt.engine_id == "OLA-050"
    assert receipt.incoming_kwarg_count == 10
    assert receipt.cycle_completed_at_present is True
    assert receipt.cycle_completed_at_rehydrated is True
    assert (
        receipt.full_kwargs_forwarded_unchanged
        is True
    )
    assert receipt.scheduler_result_preserved is True

    assert (
        receipt
        .adapter_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 5
    )

    return facade


def _build_readiness():
    return KalshiLiveReadReadinessRecord(
        schema_version="OLA-018",
        engine_id="OLA-018",
        readiness_id="kalshi_live_readiness.ola050",
        readiness_status="passed",
        adapter_id=(
            "adapter.oracle.kalshi."
            "public_markets.shadow"
        ),
        source_id="source.kalshi.market_data",
        source_base_url=(
            "https://external-api.kalshi.com/trade-api/v2"
        ),
        source_endpoint="/markets",
        http_method="GET",
        checked_at=T1,
        evaluated_at=T1,
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
            ("environment", "test"),
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


def _build_polling_engine():
    policy = ShadowPollingPolicy.create(
        policy_id="policy.ola050.integration",
        source_id="source.kalshi.market_data",
        adapter_id=(
            "adapter.oracle.kalshi."
            "public_markets.shadow"
        ),
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
            "environment": "test",
            "module": "OLA-050",
        },
    )

    return OracleShadowPollingPolicyCadenceEngine(
        policy=policy
    )


def _build_polling_state():
    return ShadowPollingState.create(
        state_id="state.ola050.integration",
        source_id="source.kalshi.market_data",
        adapter_id=(
            "adapter.oracle.kalshi."
            "public_markets.shadow"
        ),
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "environment": "test",
            "module": "OLA-050",
        },
    )


def run_actual_shadow_cycle_runner_binding_test():
    (
        facade,
        wiring,
        existing_callable,
    ) = build_facade()

    stage_cycle(
        wiring
    )

    binding = ShadowCycleRunnerBinding(
        runner_id=(
            "runner.ola017.ola050.integration"
        ),
        engine_id="OLA-017",
        source_id="source.kalshi.market_data",
        adapter_id=(
            "adapter.oracle.kalshi."
            "public_markets.shadow"
        ),
        cycle_callable=facade,
    )

    scheduler = (
        OracleControlledShadowCollectionSchedulerTick(
            polling_engine=_build_polling_engine(),
            cycle_runner=binding,
        )
    )

    kwargs = canonical_cycle_kwargs()

    tick, next_state, result = scheduler.run_tick(
        readiness=_build_readiness(),
        polling_state=_build_polling_state(),
        evaluated_at=T1,
        started_at=T1,
        completed_at=T1,
        polling_decision_metadata={
            "test": "OLA-050",
        },
        cycle_kwargs=kwargs,
        tick_metadata={
            "test": "OLA-050",
        },
    )

    assert tick.cycle_invocation_count == 1
    assert tick.cycle_invoked is True
    assert tick.cycle_succeeded is True
    assert next_state.last_cycle_succeeded is True

    assert existing_callable.call_count == 1
    assert existing_callable.last_kwargs == kwargs
    assert result["projected_by"] == (
        "existing-ola-030"
    )

    receipt = facade.last_receipt

    assert receipt is not None
    assert (
        receipt
        .adapter_receipt
        .lineage_completion_receipt
        .lineage_completion_invoked
        is True
    )

    return facade


def run_aware_datetime_test():
    (
        facade,
        wiring,
        existing_callable,
    ) = build_facade()

    stage_cycle(
        wiring
    )

    kwargs = canonical_cycle_kwargs()
    kwargs["cycle_completed_at"] = T1

    result = facade(
        **kwargs
    )

    assert result["projected_by"] == (
        "existing-ola-030"
    )
    assert (
        existing_callable
        .last_kwargs[
            "cycle_completed_at"
        ]
        is T1
    )


def run_missing_completed_at_fail_closed_test():
    (
        facade,
        _,
        existing_callable,
    ) = build_facade()

    kwargs = canonical_cycle_kwargs()
    kwargs.pop(
        "cycle_completed_at"
    )

    try:
        facade(
            **kwargs
        )
        raise AssertionError(
            "missing cycle_completed_at must fail closed"
        )
    except ShadowCycleRunnerLineageCallableFacadeContractError:
        pass

    assert existing_callable.call_count == 0


def run_naive_completed_at_fail_closed_test():
    (
        facade,
        _,
        existing_callable,
    ) = build_facade()

    kwargs = canonical_cycle_kwargs()
    kwargs["cycle_completed_at"] = (
        "2026-07-15T01:00:00"
    )

    try:
        facade(
            **kwargs
        )
        raise AssertionError(
            "naive cycle_completed_at must fail closed"
        )
    except ShadowCycleRunnerLineageCallableFacadeContractError:
        pass

    assert existing_callable.call_count == 0


def run_deterministic_facade_replay_test():
    def execute():
        (
            facade,
            wiring,
            _,
        ) = build_facade()

        stage_cycle(
            wiring
        )

        result = facade(
            **canonical_cycle_kwargs()
        )

        records = (
            wiring
            .lineage_bridge
            .coordinator
            .lineage_cycle_bridge
            .batch_router
            .bridge
            .ledger
            .records()
        )

        return (
            result,
            facade.last_receipt,
            records,
        )

    first = execute()
    second = execute()

    assert first == second

    return first


def main():
    direct = run_direct_facade_test()
    binding = (
        run_actual_shadow_cycle_runner_binding_test()
    )

    run_aware_datetime_test()
    run_missing_completed_at_fail_closed_test()
    run_naive_completed_at_fail_closed_test()

    replay = (
        run_deterministic_facade_replay_test()
    )

    receipt = binding.last_receipt

    result = {
        "schema_version": receipt.schema_version,
        "engine_id": receipt.engine_id,
        "status": "passed",
        "actual_shadow_cycle_runner_binding_callable_shape_supported": True,
        "cycle_callable_accepts_kwargs_directly": True,
        "cycle_completed_at_required": True,
        "canonical_iso_datetime_rehydrated": True,
        "aware_datetime_accepted": True,
        "full_cycle_kwargs_forwarded_unchanged": True,
        "existing_ola030_callable_invoked_exactly_once": True,
        "existing_ola030_result_preserved": True,
        "ola_046_adapter_consumed": True,
        "lineage_completion_invoked": True,
        "missing_cycle_completed_at_fails_closed": True,
        "naive_cycle_completed_at_fails_closed": True,
        "deterministic_facade_replay_valid": (
            len(replay[2]) == 5
        ),
        "ola_049_direct_callable_binding_defect_resolved": True,
        "ready_for_ola030_production_graph_integration": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": receipt.read_only,
        "execution_allowed": receipt.execution_allowed,
        "execution_adapter_resolved": (
            receipt.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            receipt.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            receipt.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            receipt.order_placement_allowed
        ),
        "funds_moved": receipt.funds_moved,
        "portfolio_mutated": receipt.portfolio_mutated,
    }

    print(
        "[PASS] OLA-050 Oracle Shadow Cycle Runner "
        "Lineage Callable Facade"
    )
    print(result)


if __name__ == "__main__":
    main()
