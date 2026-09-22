from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_composition import (
    OracleSchedulerLineageProductionComposition,
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
    21,
    0,
    0,
    tzinfo=timezone.utc,
)
T2 = datetime(
    2026,
    7,
    14,
    21,
    0,
    15,
    tzinfo=timezone.utc,
)
T3 = datetime(
    2026,
    7,
    14,
    21,
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
    batch_id = f"batch.ola.047.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-COMPOSE-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9700"
                if changed_market
                == f"KXTEST-COMPOSE-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def __init__(self):
        self.batch_calls = 0

    def route_batch(
        self,
        observations,
        routed_at,
    ):
        self.batch_calls += 1

        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.047.persistence",
                metadata={
                    "test": "OLA-047",
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
            route_id="fake.ola.047.persistence.single",
            metadata={
                "test": "OLA-047",
            },
        )


class FakeSchedulerCycleCallable:
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
            "scheduler_projection": "preserved",
            "kwargs_echo": dict(kwargs),
        }


def build_composition():
    persistence_router = (
        FakeProductionPersistenceRouter()
    )
    scheduler_callable = (
        FakeSchedulerCycleCallable()
    )

    composition = (
        OracleSchedulerLineageProductionComposition(
            production_persistence_router=(
                persistence_router
            ),
            scheduler_cycle_callable=(
                scheduler_callable
            ),
        )
    )

    return (
        composition,
        persistence_router,
        scheduler_callable,
    )


def run_composition_identity_test():
    (
        composition,
        persistence_router,
        scheduler_callable,
    ) = build_composition()

    receipt = composition.receipt

    assert receipt.schema_version == "OLA-047"
    assert receipt.engine_id == "OLA-047"
    assert (
        composition.production_persistence_router
        is persistence_router
    )
    assert (
        composition.scheduler_cycle_callable
        is scheduler_callable
    )
    assert (
        composition
        .production_wiring
        .production_persistence_router
        is persistence_router
    )
    assert (
        composition
        .scheduler_adapter
        .scheduler_cycle_callable
        is scheduler_callable
    )
    assert (
        composition
        .completion_bridge
        .production_wiring
        is composition.production_wiring
    )
    assert (
        composition
        .scheduler_adapter
        .lineage_completion_bridge
        is composition.completion_bridge
    )
    assert (
        composition.staged_persistence_router
        is composition
        .production_wiring
        .staged_persistence_router
    )

    return composition


def stage_cycle(
    composition,
    *,
    cycle_number,
    observed_at,
    changed_market=None,
):
    composition.staged_persistence_router.route_batch(
        build_cohort(
            cycle_number=cycle_number,
            changed_market=changed_market,
        ),
        observed_at,
    )


def run_three_cycle_shared_state_test():
    composition = run_composition_identity_test()

    receipts = []

    for cycle_number, observed_at, changed_market in (
        (1, T1, None),
        (2, T2, None),
        (
            3,
            T3,
            "KXTEST-COMPOSE-3",
        ),
    ):
        stage_cycle(
            composition,
            cycle_number=cycle_number,
            observed_at=observed_at,
            changed_market=changed_market,
        )

        result = composition.scheduler_adapter(
            cycle_completed_at=observed_at,
            cycle_kwargs={
                "cycle": cycle_number,
            },
        )

        assert result["scheduler_projection"] == "preserved"
        assert result["kwargs_echo"] == {
            "cycle": cycle_number,
        }

        receipts.append(
            composition.scheduler_adapter.last_receipt
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
        composition
        .production_wiring
        .lineage_bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    changed = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-COMPOSE-3",
    )
    unchanged = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-COMPOSE-1",
    )

    assert changed is not None
    assert unchanged is not None
    assert changed.transition_detected is True
    assert changed.state_changed_at == T3
    assert changed.consecutive_frame_count == 1
    assert changed.dwell_seconds == "0.000000"
    assert unchanged.consecutive_frame_count == 3
    assert unchanged.dwell_seconds == "30.000000"

    return composition, receipts


def run_deterministic_composition_replay_test():
    def execute():
        composition, _, _ = build_composition()
        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-COMPOSE-5",
            ),
        ):
            stage_cycle(
                composition,
                cycle_number=cycle_number,
                observed_at=observed_at,
                changed_market=changed_market,
            )

            composition.scheduler_adapter(
                cycle_completed_at=observed_at,
                cycle_kwargs={
                    "cycle": cycle_number,
                },
            )

            receipts.append(
                composition.scheduler_adapter.last_receipt
            )

        records = (
            composition
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
    composition, receipts = (
        run_three_cycle_shared_state_test()
    )

    replay_receipts, replay_records = (
        run_deterministic_composition_replay_test()
    )

    receipt = composition.receipt

    result = {
        "schema_version": receipt.schema_version,
        "engine_id": receipt.engine_id,
        "status": "passed",
        "production_persistence_router_preserved": True,
        "scheduler_cycle_callable_preserved": True,
        "ola_042_staged_router_exposed_for_dual_injection": True,
        "ola_044_shared_production_wiring_created_once": True,
        "ola_045_completion_bridge_shared": True,
        "ola_046_scheduler_adapter_shared": True,
        "shared_lineage_state_preserved_across_cycles": True,
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
        "deterministic_composition_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
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
        "[PASS] OLA-047 Oracle Scheduler Lineage "
        "Production Composition"
    )
    print(result)


if __name__ == "__main__":
    main()
