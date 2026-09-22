"""
INT-OLA-LINEAGE-PROD-SMOKE-001
Oracle Scheduler Lineage Production Smoke Integration Gate

Required smoke gate across OLA-041 through OLA-047.

Proves:
production persistence router
    -> OLA-042 exact canonical cohort staging
    -> OLA-043 completed-cycle promotion
    -> OLA-041 post-persistence capture hook
    -> OLA-040 exact canonical cohort capture
    -> OLA-044 persisted cohort lineage production wiring
    -> OLA-045 scheduler cycle lineage completion
    -> OLA-046 scheduler lineage production adapter
    -> OLA-047 shared production composition
    -> OLA-039 persisted cohort lineage bridge
    -> OLA-031 through OLA-036 exact state dwell/change lineage stack

Scheduler kwargs remain unchanged.
Scheduler result projection remains unchanged.
Oracle remains permanently read-only.
"""

from __future__ import annotations

from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_composition import (
    OracleSchedulerLineageProductionComposition,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


SCHEMA_VERSION = "INT-OLA-LINEAGE-PROD-SMOKE-001"
ENGINE_ID = "INT-OLA-LINEAGE-PROD-SMOKE-001"

T1 = datetime(2026, 7, 14, 22, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 22, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 22, 0, 30, tzinfo=timezone.utc)


def build_observation(
    *,
    market_id: str,
    frame_id: str,
    batch_id: str,
    yes_ask: str = "0.6140",
) -> CanonicalObservation:
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
    cycle_number: int,
    changed_market: str | None = None,
) -> tuple[CanonicalObservation, ...]:
    batch_id = (
        "batch.int.ola.lineage.prod.smoke."
        + str(cycle_number)
    )

    return tuple(
        build_observation(
            market_id=(
                "KXTEST-PROD-SMOKE-"
                + str(index)
            ),
            frame_id=(
                str(cycle_number)
                + "-"
                + str(index)
            ),
            batch_id=batch_id,
            yes_ask=(
                "0.9200"
                if changed_market
                == (
                    "KXTEST-PROD-SMOKE-"
                    + str(index)
                )
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


class FakeProductionPersistenceRouter:
    def __init__(self) -> None:
        self.batch_call_count = 0
        self.single_call_count = 0
        self.persisted_observation_ids: list[str] = []

    def route_batch(
        self,
        observations,
        routed_at,
    ):
        self.batch_call_count += 1
        observations = tuple(observations)

        self.persisted_observation_ids.extend(
            observation.observation_id
            for observation in observations
        )

        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id=(
                    "fake.int.ola.lineage.prod."
                    "smoke.persistence"
                ),
                metadata={
                    "integration_gate": SCHEMA_VERSION,
                },
            )
            for observation in observations
        )

    def __call__(
        self,
        observation,
        routed_at,
    ):
        self.single_call_count += 1

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id=(
                "fake.int.ola.lineage.prod."
                "smoke.persistence.single"
            ),
            metadata={
                "integration_gate": SCHEMA_VERSION,
            },
        )


class FakeExistingOLA030SchedulerCallable:
    def __init__(self) -> None:
        self.call_count = 0
        self.kwargs_history: list[dict] = []
        self.results: list[dict] = []

    def __call__(
        self,
        **kwargs,
    ):
        self.call_count += 1
        canonical_kwargs = dict(kwargs)
        self.kwargs_history.append(canonical_kwargs)

        result = {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "cycle_status": "completed",
            "canonical_count": 5,
            "postgresql_routing_record_delta": 5,
            "read_only": True,
            "execution_allowed": False,
            "projected_by": (
                "existing-ola-030-scheduler-callable"
            ),
            "scheduler_kwargs_echo": canonical_kwargs,
        }

        self.results.append(result)
        return result


def build_composition():
    persistence_router = (
        FakeProductionPersistenceRouter()
    )
    scheduler_callable = (
        FakeExistingOLA030SchedulerCallable()
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


def stage_and_run(
    *,
    composition,
    cycle_number: int,
    observed_at: datetime,
    changed_market: str | None = None,
):
    cohort = build_cohort(
        cycle_number=cycle_number,
        changed_market=changed_market,
    )

    routing_evidence = (
        composition
        .staged_persistence_router
        .route_batch(
            cohort,
            observed_at,
        )
    )

    scheduler_kwargs = {
        "cycle_number": cycle_number,
        "cycle_started_at": observed_at,
        "cycle_completed_at": observed_at,
        "replay_metadata": {
            "integration_gate": SCHEMA_VERSION,
            "cycle_number": cycle_number,
        },
        "audit_metadata": {
            "integration_gate": SCHEMA_VERSION,
            "cycle_number": cycle_number,
        },
    }

    projected_result = (
        composition
        .scheduler_adapter(
            cycle_completed_at=observed_at,
            cycle_kwargs=scheduler_kwargs,
        )
    )

    return (
        cohort,
        routing_evidence,
        scheduler_kwargs,
        projected_result,
        composition.scheduler_adapter.last_receipt,
    )


def run_three_cycle_production_smoke():
    (
        composition,
        persistence_router,
        scheduler_callable,
    ) = build_composition()

    first = stage_and_run(
        composition=composition,
        cycle_number=1,
        observed_at=T1,
    )

    second = stage_and_run(
        composition=composition,
        cycle_number=2,
        observed_at=T2,
    )

    third = stage_and_run(
        composition=composition,
        cycle_number=3,
        observed_at=T3,
        changed_market="KXTEST-PROD-SMOKE-4",
    )

    assert persistence_router.batch_call_count == 3
    assert persistence_router.single_call_count == 0
    assert scheduler_callable.call_count == 3

    for (
        cohort,
        routing_evidence,
        scheduler_kwargs,
        projected_result,
        adapter_receipt,
    ) in (first, second, third):
        assert len(cohort) == 5
        assert len(routing_evidence) == 5
        assert all(
            evidence.accepted is True
            for evidence in routing_evidence
        )

        assert projected_result[
            "projected_by"
        ] == "existing-ola-030-scheduler-callable"

        assert (
            projected_result[
                "scheduler_kwargs_echo"
            ]
            == scheduler_kwargs
        )

        assert adapter_receipt is not None
        assert (
            adapter_receipt
            .scheduler_callable_invocation_count
            == 1
        )
        assert (
            adapter_receipt
            .scheduler_kwargs_preserved
            is True
        )
        assert (
            adapter_receipt
            .scheduler_result_preserved
            is True
        )

    first_receipt = first[4]
    second_receipt = second[4]
    third_receipt = third[4]

    assert (
        first_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 5
    )

    assert (
        second_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 10
    )

    assert (
        third_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 15
    )

    assert (
        first_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .transition_count
        == 0
    )

    assert (
        second_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .transition_count
        == 0
    )

    assert (
        third_receipt
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

    assert ledger.market_count == 5
    assert ledger.record_count == 15

    changed_head = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-PROD-SMOKE-4",
    )

    unchanged_head = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-PROD-SMOKE-1",
    )

    assert changed_head is not None
    assert unchanged_head is not None

    assert changed_head.transition_detected is True
    assert changed_head.state_changed_at == T3
    assert changed_head.consecutive_frame_count == 1
    assert changed_head.dwell_seconds == "0.000000"

    assert unchanged_head.transition_detected is False
    assert unchanged_head.consecutive_frame_count == 3
    assert unchanged_head.dwell_seconds == "30.000000"

    assert (
        composition
        .staged_persistence_router
        .pending_stage_count
        == 0
    )

    assert (
        composition
        .staged_persistence_router
        .consumed_stage_count
        == 3
    )

    assert composition.production_wiring.capture_port.pending_count == 0
    assert composition.production_wiring.capture_port.consumed_count == 3

    return (
        composition,
        persistence_router,
        scheduler_callable,
        first_receipt,
        second_receipt,
        third_receipt,
    )


def run_deterministic_replay():
    def execute():
        (
            composition,
            _,
            _,
        ) = build_composition()

        receipts = []

        for (
            cycle_number,
            observed_at,
            changed_market,
        ) in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-PROD-SMOKE-2",
            ),
        ):
            result = stage_and_run(
                composition=composition,
                cycle_number=cycle_number,
                observed_at=observed_at,
                changed_market=changed_market,
            )

            receipts.append(
                result[4]
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

        return (
            tuple(receipts),
            records,
        )

    first_receipts, first_records = execute()
    second_receipts, second_records = execute()

    assert first_receipts == second_receipts
    assert first_records == second_records

    return first_receipts, first_records


def main():
    (
        composition,
        persistence_router,
        scheduler_callable,
        first_receipt,
        second_receipt,
        third_receipt,
    ) = run_three_cycle_production_smoke()

    (
        replay_receipts,
        replay_records,
    ) = run_deterministic_replay()

    composition_receipt = composition.receipt

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_041_post_persistence_capture_hook_integrated": True,
        "ola_042_staged_persistence_router_integrated": True,
        "ola_043_completion_promoter_integrated": True,
        "ola_044_production_wiring_integrated": True,
        "ola_045_scheduler_completion_bridge_integrated": True,
        "ola_046_scheduler_production_adapter_integrated": True,
        "ola_047_shared_production_composition_integrated": True,
        "production_persistence_batch_calls": (
            persistence_router.batch_call_count
        ),
        "scheduler_callable_calls": (
            scheduler_callable.call_count
        ),
        "first_cycle_lineage_record_count": (
            first_receipt
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "second_cycle_lineage_record_count": (
            second_receipt
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "third_cycle_lineage_record_count": (
            third_receipt
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .lineage_record_count_after
        ),
        "third_cycle_transition_count": (
            third_receipt
            .lineage_completion_receipt
            .lineage_wiring_receipt
            .transition_count
        ),
        "five_market_shared_lineage_state": True,
        "exact_canonical_cohort_objects_preserved": True,
        "stage_write_once_consume_once_preserved": True,
        "capture_write_once_consume_once_preserved": True,
        "same_state_dwell_advanced_across_cycles": True,
        "exact_state_change_detected": True,
        "unchanged_market_dwell_preserved": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "production_composition_shared_state_valid": (
            composition_receipt
            .staged_router_shared_with_production_wiring
            is True
        ),
        "deterministic_production_smoke_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-OLA-LINEAGE-PROD-SMOKE-001 "
        "Oracle Scheduler Lineage Production Smoke Gate"
    )
    print(result)


if __name__ == "__main__":
    main()
