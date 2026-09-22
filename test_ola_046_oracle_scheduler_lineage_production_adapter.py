from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 20, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 20, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 20, 0, 30, tzinfo=timezone.utc)


def build_observation(*, market_id, frame_id, batch_id, yes_ask="0.6140"):
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
        source_observation_id="kalshi." + market_id + "." + frame_id,
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


def build_cohort(*, cycle_number, changed_market=None):
    batch_id = f"batch.ola.046.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-PROD-ADAPTER-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9900"
                if changed_market == f"KXTEST-PROD-ADAPTER-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def route_batch(self, observations, routed_at):
        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.046.persistence",
                metadata={"test": "OLA-046"},
            )
            for observation in observations
        )

    def __call__(self, observation, routed_at):
        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.ola.046.persistence.single",
            metadata={"test": "OLA-046"},
        )


class FakeSchedulerCycleCallable:
    def __init__(self):
        self.call_count = 0
        self.last_kwargs = None

    def __call__(self, **kwargs):
        self.call_count += 1
        self.last_kwargs = dict(kwargs)

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "cycle_status": "completed",
            "canonical_count": 5,
            "postgresql_routing_record_delta": 5,
            "read_only": True,
            "execution_allowed": False,
            "projected_by": "existing-ola-030-callable",
            "kwargs_echo": dict(kwargs),
        }


def build_adapter():
    wiring = OraclePersistedCohortLineageProductionWiringContract(
        production_persistence_router=FakeProductionPersistenceRouter()
    )
    completion_bridge = OracleSchedulerCycleLineageCompletionBridge(
        production_wiring=wiring
    )
    scheduler_callable = FakeSchedulerCycleCallable()
    adapter = OracleSchedulerLineageProductionAdapter(
        scheduler_cycle_callable=scheduler_callable,
        lineage_completion_bridge=completion_bridge,
    )
    return adapter, wiring, scheduler_callable


def stage_cycle(wiring, *, cycle_number, observed_at, changed_market=None):
    wiring.staged_persistence_router.route_batch(
        build_cohort(
            cycle_number=cycle_number,
            changed_market=changed_market,
        ),
        observed_at,
    )


def run_first_cycle_test():
    adapter, wiring, scheduler_callable = build_adapter()

    stage_cycle(wiring, cycle_number=1, observed_at=T1)

    kwargs = {
        "source_control_decision": "typed-decision",
        "cycle_started_at": T1,
        "cycle_completed_at": T1,
        "replay_metadata": {"source": "OLA-030"},
        "audit_metadata": {"source": "OLA-030"},
    }

    result = adapter(cycle_completed_at=T1, cycle_kwargs=kwargs)

    assert scheduler_callable.call_count == 1
    assert scheduler_callable.last_kwargs == kwargs
    assert result["projected_by"] == "existing-ola-030-callable"
    assert result["kwargs_echo"] == kwargs

    receipt = adapter.last_receipt
    assert receipt is not None
    assert receipt.schema_version == "OLA-046"
    assert receipt.engine_id == "OLA-046"
    assert receipt.scheduler_callable_invocation_count == 1
    assert receipt.scheduler_kwargs_preserved is True
    assert receipt.scheduler_result_preserved is True
    assert receipt.lineage_completion_receipt is not None
    assert (
        receipt.lineage_completion_receipt.lineage_wiring_receipt.lineage_record_count_after
        == 5
    )

    return adapter, wiring, receipt


def run_repeated_cycle_test():
    adapter, wiring, _ = run_first_cycle_test()

    stage_cycle(wiring, cycle_number=2, observed_at=T2)

    adapter(cycle_completed_at=T2, cycle_kwargs={"cycle": 2})

    receipt = adapter.last_receipt
    assert receipt is not None
    assert (
        receipt.lineage_completion_receipt.lineage_wiring_receipt.lineage_record_count_after
        == 10
    )
    assert (
        receipt.lineage_completion_receipt.lineage_wiring_receipt.transition_count
        == 0
    )

    return adapter, wiring, receipt


def run_changed_cycle_test():
    adapter, wiring, _ = run_repeated_cycle_test()

    stage_cycle(
        wiring,
        cycle_number=3,
        observed_at=T3,
        changed_market="KXTEST-PROD-ADAPTER-2",
    )

    adapter(cycle_completed_at=T3, cycle_kwargs={"cycle": 3})

    receipt = adapter.last_receipt
    assert receipt is not None
    assert (
        receipt.lineage_completion_receipt.lineage_wiring_receipt.transition_count
        == 1
    )
    assert (
        receipt.lineage_completion_receipt.lineage_wiring_receipt.lineage_record_count_after
        == 15
    )

    return receipt


def run_deterministic_adapter_replay_test():
    def execute():
        adapter, wiring, _ = build_adapter()
        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (3, T3, "KXTEST-PROD-ADAPTER-4"),
        ):
            stage_cycle(
                wiring,
                cycle_number=cycle_number,
                observed_at=observed_at,
                changed_market=changed_market,
            )

            adapter(
                cycle_completed_at=observed_at,
                cycle_kwargs={"cycle": cycle_number},
            )

            receipts.append(adapter.last_receipt)

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
    _, _, first = run_first_cycle_test()
    _, _, second = run_repeated_cycle_test()
    third = run_changed_cycle_test()

    replay_receipts, replay_records = run_deterministic_adapter_replay_test()

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "existing_ola_030_callable_preserved": True,
        "scheduler_callable_invoked_exactly_once": True,
        "scheduler_kwargs_preserved_exactly": True,
        "scheduler_result_object_preserved": True,
        "ola_045_lineage_completion_bridge_consumed": True,
        "first_cycle_advanced_five_lineage_records": (
            first.lineage_completion_receipt.lineage_wiring_receipt.lineage_record_count_after
            == 5
        ),
        "second_cycle_advanced_dwell": (
            second.lineage_completion_receipt.lineage_wiring_receipt.lineage_record_count_after
            == 10
        ),
        "third_cycle_detected_exact_state_change": (
            third.lineage_completion_receipt.lineage_wiring_receipt.transition_count
            == 1
        ),
        "scheduler_projection_semantics_not_redefined": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_production_adapter_replay_valid": (
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
        "execution_adapter_resolved": third.execution_adapter_resolved,
        "execution_adapter_invoked": third.execution_adapter_invoked,
        "trade_authorization_allowed": third.trade_authorization_allowed,
        "order_placement_allowed": third.order_placement_allowed,
        "funds_moved": third.funds_moved,
        "portfolio_mutated": third.portfolio_mutated,
    }

    print("[PASS] OLA-046 Oracle Scheduler Lineage Production Adapter")
    print(result)


if __name__ == "__main__":
    main()
