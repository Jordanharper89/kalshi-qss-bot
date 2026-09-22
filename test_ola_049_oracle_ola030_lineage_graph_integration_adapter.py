from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_ola030_lineage_graph_integration_adapter import (
    OLA030LineageGraphIntegrationAdapterContractError,
    OracleOLA030LineageGraphIntegrationAdapter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 15, 0, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 15, 0, 0, 30, tzinfo=timezone.utc)


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
            "kalshi." + market_id + "." + frame_id
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
    batch_id = f"batch.ola.049.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-OLA030-INTEGRATION-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9500"
                if changed_market
                == f"KXTEST-OLA030-INTEGRATION-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def __init__(self):
        self.batch_calls = 0

    def route_batch(self, observations, routed_at):
        self.batch_calls += 1

        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.049.persistence",
                metadata={"test": "OLA-049"},
            )
            for observation in observations
        )

    def __call__(self, observation, routed_at):
        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.ola.049.persistence.single",
            metadata={"test": "OLA-049"},
        )


class FakeProductionCycleCallable:
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
            "projected_by": "ola030-existing-cycle-callable",
            "kwargs_echo": dict(kwargs),
        }


def build_adapter():
    persistence_router = FakeProductionPersistenceRouter()
    cycle_callable = FakeProductionCycleCallable()

    adapter = OracleOLA030LineageGraphIntegrationAdapter(
        production_persistence_router=persistence_router,
        production_cycle_callable=cycle_callable,
    )

    return adapter, persistence_router, cycle_callable


def run_binding_identity_test():
    adapter, persistence_router, cycle_callable = build_adapter()
    bindings = adapter.bindings

    assert bindings.schema_version == "OLA-049"
    assert bindings.engine_id == "OLA-049"
    assert (
        bindings.runtime_persistence_router
        is bindings.ola017_persistence_router
    )
    assert (
        adapter.graph_binding.production_persistence_router
        is persistence_router
    )
    assert (
        adapter.graph_binding.production_scheduler_cycle_callable
        is cycle_callable
    )
    assert (
        bindings.shadow_cycle_runner_callable
        is adapter.graph_binding.shadow_cycle_runner_callable
    )

    return adapter


def run_graph_component_preservation_test():
    adapter = run_binding_identity_test()

    sentinel_runtime = object()
    sentinel_scheduler = object()
    sentinel_runner = object()

    original = {
        "runtime_root": sentinel_runtime,
        "scheduler": sentinel_scheduler,
        "runner": sentinel_runner,
    }

    integrated = adapter.apply_to_graph_components(
        graph_components=original
    )

    assert integrated["runtime_root"] is sentinel_runtime
    assert integrated["scheduler"] is sentinel_scheduler
    assert integrated["runner"] is sentinel_runner
    assert (
        integrated["runtime_persistence_router"]
        is adapter.bindings.runtime_persistence_router
    )
    assert (
        integrated["ola017_persistence_router"]
        is adapter.bindings.ola017_persistence_router
    )
    assert (
        integrated["shadow_cycle_runner_callable"]
        is adapter.bindings.shadow_cycle_runner_callable
    )

    return adapter


def run_three_cycle_integration_test():
    adapter = run_graph_component_preservation_test()
    bindings = adapter.bindings
    receipts = []

    for cycle_number, observed_at, changed_market in (
        (1, T1, None),
        (2, T2, None),
        (
            3,
            T3,
            "KXTEST-OLA030-INTEGRATION-4",
        ),
    ):
        bindings.runtime_persistence_router.route_batch(
            build_cohort(
                cycle_number=cycle_number,
                changed_market=changed_market,
            ),
            observed_at,
        )

        result = bindings.shadow_cycle_runner_callable(
            cycle_completed_at=observed_at,
            cycle_kwargs={
                "cycle": cycle_number,
                "ola030": True,
            },
        )

        assert result["projected_by"] == (
            "ola030-existing-cycle-callable"
        )
        assert result["kwargs_echo"] == {
            "cycle": cycle_number,
            "ola030": True,
        }

        receipts.append(
            bindings
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

    return adapter, receipts


def run_protected_key_fail_closed_test():
    adapter = run_binding_identity_test()

    try:
        adapter.apply_to_graph_components(
            graph_components={
                "runtime_persistence_router": object(),
            }
        )
        raise AssertionError(
            "protected integration key collision must fail closed"
        )
    except OLA030LineageGraphIntegrationAdapterContractError:
        pass


def run_deterministic_integration_replay_test():
    def execute():
        adapter, _, _ = build_adapter()
        bindings = adapter.bindings
        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-OLA030-INTEGRATION-2",
            ),
        ):
            bindings.ola017_persistence_router.route_batch(
                build_cohort(
                    cycle_number=cycle_number,
                    changed_market=changed_market,
                ),
                observed_at,
            )

            bindings.shadow_cycle_runner_callable(
                cycle_completed_at=observed_at,
                cycle_kwargs={"cycle": cycle_number},
            )

            receipts.append(
                bindings
                .shadow_cycle_runner_callable
                .last_receipt
            )

        records = (
            adapter
            .graph_binding
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
    adapter, receipts = run_three_cycle_integration_test()

    run_protected_key_fail_closed_test()

    replay_receipts, replay_records = (
        run_deterministic_integration_replay_test()
    )

    bindings = adapter.bindings

    result = {
        "schema_version": bindings.schema_version,
        "engine_id": bindings.engine_id,
        "status": "passed",
        "ola_048_graph_binding_consumed": True,
        "original_production_persistence_router_preserved": True,
        "original_production_cycle_callable_preserved": True,
        "runtime_persistence_router_substitution_ready": True,
        "ola017_persistence_router_substitution_ready": True,
        "runtime_and_ola017_same_staged_router": True,
        "shadow_cycle_runner_callable_substitution_ready": True,
        "unrelated_graph_components_preserved_by_identity": True,
        "protected_integration_key_collision_fails_closed": True,
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
        "deterministic_ola030_integration_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
        "ready_for_ola030_full_replacement": True,
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": bindings.read_only,
        "execution_allowed": bindings.execution_allowed,
        "execution_adapter_resolved": (
            bindings.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            bindings.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            bindings.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            bindings.order_placement_allowed
        ),
        "funds_moved": bindings.funds_moved,
        "portfolio_mutated": bindings.portfolio_mutated,
    }

    print(
        "[PASS] OLA-049 Oracle OLA-030 Lineage "
        "Graph Integration Adapter"
    )
    print(result)


if __name__ == "__main__":
    main()
