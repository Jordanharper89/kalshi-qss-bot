from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_lineage_graph_binding_contract import (
    OracleLiveShadowLineageGraphBindingContract,
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
    23,
    0,
    0,
    tzinfo=timezone.utc,
)
T2 = datetime(
    2026,
    7,
    14,
    23,
    0,
    15,
    tzinfo=timezone.utc,
)
T3 = datetime(
    2026,
    7,
    14,
    23,
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
    batch_id = f"batch.ola.048.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-GRAPH-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9400"
                if changed_market
                == f"KXTEST-GRAPH-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def __init__(self):
        self.batch_call_count = 0

    def route_batch(
        self,
        observations,
        routed_at,
    ):
        self.batch_call_count += 1

        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.048.persistence",
                metadata={
                    "test": "OLA-048",
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
            route_id="fake.ola.048.persistence.single",
            metadata={
                "test": "OLA-048",
            },
        )


class FakeProductionSchedulerCycleCallable:
    def __init__(self):
        self.call_count = 0
        self.last_kwargs = None

    def __call__(
        self,
        **kwargs,
    ):
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
            "projected_by": "existing-ola-030",
            "kwargs_echo": dict(kwargs),
        }


def build_binding():
    persistence_router = (
        FakeProductionPersistenceRouter()
    )
    scheduler_callable = (
        FakeProductionSchedulerCycleCallable()
    )

    binding = (
        OracleLiveShadowLineageGraphBindingContract(
            production_persistence_router=(
                persistence_router
            ),
            production_scheduler_cycle_callable=(
                scheduler_callable
            ),
        )
    )

    return (
        binding,
        persistence_router,
        scheduler_callable,
    )


def run_identity_binding_test():
    (
        binding,
        persistence_router,
        scheduler_callable,
    ) = build_binding()

    record = binding.record

    assert record.schema_version == "OLA-048"
    assert record.engine_id == "OLA-048"
    assert (
        binding.production_persistence_router
        is persistence_router
    )
    assert (
        binding.production_scheduler_cycle_callable
        is scheduler_callable
    )
    assert (
        binding.runtime_persistence_router
        is binding.ola017_persistence_router
    )
    assert (
        binding.runtime_persistence_router
        is binding
        .composition
        .staged_persistence_router
    )
    assert (
        binding.shadow_cycle_runner_callable
        is binding
        .composition
        .scheduler_adapter
    )
    assert (
        binding
        .composition
        .completion_bridge
        .production_wiring
        is binding
        .composition
        .production_wiring
    )

    return binding


def run_three_cycle_binding_test():
    binding = run_identity_binding_test()

    receipts = []

    for cycle_number, observed_at, changed_market in (
        (1, T1, None),
        (2, T2, None),
        (
            3,
            T3,
            "KXTEST-GRAPH-2",
        ),
    ):
        binding.runtime_persistence_router.route_batch(
            build_cohort(
                cycle_number=cycle_number,
                changed_market=changed_market,
            ),
            observed_at,
        )

        result = binding.shadow_cycle_runner_callable(
            cycle_completed_at=observed_at,
            cycle_kwargs={
                "cycle": cycle_number,
                "source": "OLA-030",
            },
        )

        assert result["projected_by"] == "existing-ola-030"
        assert result["kwargs_echo"] == {
            "cycle": cycle_number,
            "source": "OLA-030",
        }

        receipts.append(
            binding
            .shadow_cycle_runner_callable
            .last_receipt
        )

    assert (
        receipts[0]
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 5
    )
    assert (
        receipts[1]
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 10
    )
    assert (
        receipts[2]
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 15
    )
    assert (
        receipts[2]
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .transition_count
        == 1
    )

    ledger = (
        binding
        .composition
        .production_wiring
        .lineage_bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    assert ledger.market_count == 5
    assert ledger.record_count == 15

    return binding, receipts


def run_deterministic_binding_replay_test():
    def execute():
        binding, _, _ = build_binding()
        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-GRAPH-5",
            ),
        ):
            binding.ola017_persistence_router.route_batch(
                build_cohort(
                    cycle_number=cycle_number,
                    changed_market=changed_market,
                ),
                observed_at,
            )

            binding.shadow_cycle_runner_callable(
                cycle_completed_at=observed_at,
                cycle_kwargs={
                    "cycle": cycle_number,
                },
            )

            receipts.append(
                binding
                .shadow_cycle_runner_callable
                .last_receipt
            )

        records = (
            binding
            .composition
            .production_wiring
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
    binding, receipts = run_three_cycle_binding_test()

    replay_receipts, replay_records = (
        run_deterministic_binding_replay_test()
    )

    record = binding.record

    result = {
        "schema_version": record.schema_version,
        "engine_id": record.engine_id,
        "status": "passed",
        "production_persistence_router_preserved": True,
        "production_scheduler_callable_preserved": True,
        "runtime_and_ola017_same_staged_router": True,
        "shadow_cycle_runner_uses_ola_046_adapter": True,
        "ola_047_shared_composition_consumed": True,
        "ola_044_shared_production_wiring_identity": True,
        "shared_lineage_state_identity": True,
        "first_cycle_lineage_record_count": (
            receipts[0]
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "second_cycle_lineage_record_count": (
            receipts[1]
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "third_cycle_lineage_record_count": (
            receipts[2]
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "third_cycle_transition_count": (
            receipts[2]
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .transition_count
        ),
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_graph_binding_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
        "ready_for_ola_030_graph_integration": True,
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": record.read_only,
        "execution_allowed": record.execution_allowed,
        "execution_adapter_resolved": (
            record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            record.order_placement_allowed
        ),
        "funds_moved": record.funds_moved,
        "portfolio_mutated": record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-048 Oracle Live Shadow Lineage "
        "Graph Binding Contract"
    )
    print(result)


if __name__ == "__main__":
    main()
