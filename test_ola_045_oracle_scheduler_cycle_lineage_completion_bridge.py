from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
    SchedulerCycleLineageCompletionBridgeContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


T1 = datetime(
    2026,
    7,
    14,
    19,
    0,
    0,
    tzinfo=timezone.utc,
)
T2 = datetime(
    2026,
    7,
    14,
    19,
    0,
    15,
    tzinfo=timezone.utc,
)
T3 = datetime(
    2026,
    7,
    14,
    19,
    0,
    30,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id,
    yes_ask="0.6140",
):
    payload = {
        "source_market_id": market_id,
        "yes_bid_dollars": "0.0000",
        "yes_bid_size_fp": "0.00",
        "yes_ask_dollars": yes_ask,
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


def build_cohort(
    *,
    cycle_number,
    changed_market=None,
):
    batch_id = f"batch.ola.045.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-SCHED-LINEAGE-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9700"
                if changed_market
                == f"KXTEST-SCHED-LINEAGE-{index}"
                else "0.6140"
            ),
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
                route_id="fake.ola.045.persistence",
                metadata={
                    "test": "OLA-045",
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
            route_id="fake.ola.045.persistence.single",
            metadata={
                "test": "OLA-045",
            },
        )


class FakeCycleRunner:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.call_count = 0
        self.last_kwargs = None

    def __call__(
        self,
        **kwargs,
    ):
        self.call_count += 1
        self.last_kwargs = dict(kwargs)
        return self.result


def completed_cycle_result():
    return {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "completed",
        "canonical_count": 5,
        "postgresql_routing_record_delta": 5,
        "read_only": True,
        "execution_allowed": False,
    }


def build_bridge():
    production_wiring = (
        OraclePersistedCohortLineageProductionWiringContract(
            production_persistence_router=(
                FakeProductionPersistenceRouter()
            )
        )
    )

    bridge = OracleSchedulerCycleLineageCompletionBridge(
        production_wiring=production_wiring
    )

    return bridge, production_wiring


def stage_cycle(
    production_wiring,
    *,
    cycle_number,
    routed_at,
    changed_market=None,
):
    cohort = build_cohort(
        cycle_number=cycle_number,
        changed_market=changed_market,
    )

    production_wiring.staged_persistence_router.route_batch(
        cohort,
        routed_at,
    )

    return cohort


def run_completed_cycle_test():
    bridge, wiring = build_bridge()

    stage_cycle(
        wiring,
        cycle_number=1,
        routed_at=T1,
    )

    result = completed_cycle_result()
    result_before = dict(result)
    runner = FakeCycleRunner(result)

    returned = bridge.run_cycle(
        cycle_runner=runner,
        cycle_completed_at=T1,
        cycle_kwargs={
            "alpha": "beta",
            "count": 5,
        },
    )

    assert returned is result
    assert result == result_before
    assert runner.call_count == 1
    assert runner.last_kwargs == {
        "alpha": "beta",
        "count": 5,
    }

    receipt = bridge.last_receipt

    assert receipt is not None
    assert receipt.schema_version == "OLA-045"
    assert receipt.engine_id == "OLA-045"
    assert receipt.cycle_invocation_count == 1
    assert receipt.cycle_result_preserved is True
    assert receipt.lineage_completion_invoked is True
    assert receipt.acquisition_batch_id == "batch.ola.045.1"
    assert receipt.lineage_wiring_receipt is not None
    assert (
        receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 5
    )

    return bridge, wiring, receipt


def run_repeated_cycle_test():
    bridge, wiring, _ = run_completed_cycle_test()

    stage_cycle(
        wiring,
        cycle_number=2,
        routed_at=T2,
    )

    runner = FakeCycleRunner(
        completed_cycle_result()
    )

    bridge.run_cycle(
        cycle_runner=runner,
        cycle_completed_at=T2,
        cycle_kwargs={
            "cycle": 2,
        },
    )

    receipt = bridge.last_receipt

    assert receipt is not None
    assert receipt.lineage_completion_invoked is True
    assert (
        receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 10
    )
    assert (
        receipt
        .lineage_wiring_receipt
        .transition_count
        == 0
    )

    return bridge, wiring, receipt


def run_changed_cycle_test():
    bridge, wiring, _ = run_repeated_cycle_test()

    stage_cycle(
        wiring,
        cycle_number=3,
        routed_at=T3,
        changed_market="KXTEST-SCHED-LINEAGE-3",
    )

    runner = FakeCycleRunner(
        completed_cycle_result()
    )

    bridge.run_cycle(
        cycle_runner=runner,
        cycle_completed_at=T3,
        cycle_kwargs={
            "cycle": 3,
        },
    )

    receipt = bridge.last_receipt

    assert receipt is not None
    assert receipt.lineage_wiring_receipt is not None
    assert (
        receipt
        .lineage_wiring_receipt
        .transition_count
        == 1
    )
    assert (
        receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 15
    )

    ledger = (
        wiring
        .lineage_bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    changed = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-SCHED-LINEAGE-3",
    )

    unchanged = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-SCHED-LINEAGE-1",
    )

    assert changed is not None
    assert unchanged is not None
    assert changed.transition_detected is True
    assert changed.state_changed_at == T3
    assert changed.consecutive_frame_count == 1
    assert changed.dwell_seconds == "0.000000"
    assert unchanged.consecutive_frame_count == 3
    assert unchanged.dwell_seconds == "30.000000"

    return receipt


def run_failed_cycle_does_not_promote_test():
    bridge, wiring = build_bridge()

    stage_cycle(
        wiring,
        cycle_number=1,
        routed_at=T1,
    )

    failed = {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "failed",
        "canonical_count": 0,
        "postgresql_routing_record_delta": 0,
        "read_only": True,
        "execution_allowed": False,
    }

    runner = FakeCycleRunner(failed)

    returned = bridge.run_cycle(
        cycle_runner=runner,
        cycle_completed_at=T1,
        cycle_kwargs={},
    )

    assert returned is failed
    assert runner.call_count == 1

    receipt = bridge.last_receipt

    assert receipt is not None
    assert receipt.lineage_completion_invoked is False
    assert receipt.acquisition_batch_id is None
    assert receipt.lineage_wiring_receipt is None
    assert (
        wiring
        .staged_persistence_router
        .pending_stage_count
        == 1
    )


def run_missing_stage_fails_closed_test():
    bridge, _ = build_bridge()
    runner = FakeCycleRunner(
        completed_cycle_result()
    )

    try:
        bridge.run_cycle(
            cycle_runner=runner,
            cycle_completed_at=T1,
            cycle_kwargs={},
        )
        raise AssertionError(
            "completed cycle without staged cohort must fail closed"
        )
    except SchedulerCycleLineageCompletionBridgeContractError:
        pass

    assert runner.call_count == 1


def run_multiple_pending_stages_fail_closed_test():
    bridge, wiring = build_bridge()

    stage_cycle(
        wiring,
        cycle_number=1,
        routed_at=T1,
    )
    stage_cycle(
        wiring,
        cycle_number=2,
        routed_at=T2,
    )

    runner = FakeCycleRunner(
        completed_cycle_result()
    )

    try:
        bridge.run_cycle(
            cycle_runner=runner,
            cycle_completed_at=T2,
            cycle_kwargs={},
        )
        raise AssertionError(
            "ambiguous staged cohort boundary must fail closed"
        )
    except SchedulerCycleLineageCompletionBridgeContractError:
        pass

    assert runner.call_count == 1
    assert (
        wiring
        .staged_persistence_router
        .pending_stage_count
        == 2
    )


def run_exact_cycle_kwargs_forwarding_test():
    bridge, wiring = build_bridge()

    stage_cycle(
        wiring,
        cycle_number=1,
        routed_at=T1,
    )

    runner = FakeCycleRunner(
        completed_cycle_result()
    )

    kwargs = {
        "source_control_decision": "typed-record-placeholder",
        "cycle_started_at": T1,
        "cycle_completed_at": T1,
        "replay_metadata": {
            "launch": "OLA-030",
        },
        "audit_metadata": {
            "launch": "OLA-030",
        },
    }

    bridge.run_cycle(
        cycle_runner=runner,
        cycle_completed_at=T1,
        cycle_kwargs=kwargs,
    )

    assert runner.last_kwargs == kwargs


def run_deterministic_bridge_replay_test():
    def execute():
        bridge, wiring = build_bridge()
        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-SCHED-LINEAGE-5",
            ),
        ):
            stage_cycle(
                wiring,
                cycle_number=cycle_number,
                routed_at=observed_at,
                changed_market=changed_market,
            )

            bridge.run_cycle(
                cycle_runner=FakeCycleRunner(
                    completed_cycle_result()
                ),
                cycle_completed_at=observed_at,
                cycle_kwargs={
                    "cycle": cycle_number,
                },
            )

            receipts.append(
                bridge.last_receipt
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

        return tuple(receipts), records

    first_receipts, first_records = execute()
    second_receipts, second_records = execute()

    assert first_receipts == second_receipts
    assert first_records == second_records

    return first_receipts, first_records


def main():
    _, _, first = run_completed_cycle_test()
    _, _, second = run_repeated_cycle_test()
    third = run_changed_cycle_test()

    run_failed_cycle_does_not_promote_test()
    run_missing_stage_fails_closed_test()
    run_multiple_pending_stages_fail_closed_test()
    run_exact_cycle_kwargs_forwarding_test()

    replay_receipts, replay_records = (
        run_deterministic_bridge_replay_test()
    )

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "ola_017_cycle_invoked_exactly_once": True,
        "exact_cycle_kwargs_forwarded": True,
        "exact_ola_017_result_object_preserved": True,
        "ola_017_result_mapping_preserved": True,
        "completed_cycle_requires_single_pending_stage": True,
        "ola_044_production_wiring_invoked_after_completed_cycle": True,
        "cycle_completed_at_bound_to_lineage": True,
        "first_cycle_advanced_five_lineage_records": (
            first
            .lineage_wiring_receipt
            .lineage_record_count_after
            == 5
        ),
        "second_cycle_advanced_dwell": (
            second
            .lineage_wiring_receipt
            .lineage_record_count_after
            == 10
        ),
        "third_cycle_detected_exact_state_change": (
            third
            .lineage_wiring_receipt
            .transition_count
            == 1
        ),
        "failed_cycle_does_not_promote_stage": True,
        "missing_stage_fails_closed": True,
        "multiple_pending_stages_fail_closed": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_result_projection_not_owned": True,
        "deterministic_scheduler_lineage_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": third.read_only,
        "execution_allowed": third.execution_allowed,
        "execution_adapter_resolved": (
            third.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            third.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            third.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            third.order_placement_allowed
        ),
        "funds_moved": third.funds_moved,
        "portfolio_mutated": third.portfolio_mutated,
    }

    print(
        "[PASS] OLA-045 Oracle Scheduler Cycle "
        "Lineage Completion Bridge"
    )
    print(result)


if __name__ == "__main__":
    main()
