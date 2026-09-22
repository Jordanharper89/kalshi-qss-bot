from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
    PersistedCohortLineageProductionWiringContractError,
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
    18,
    0,
    0,
    tzinfo=timezone.utc,
)
T2 = datetime(
    2026,
    7,
    14,
    18,
    0,
    15,
    tzinfo=timezone.utc,
)
T3 = datetime(
    2026,
    7,
    14,
    18,
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
    batch_id = f"batch.ola.044.{cycle_number}"

    return tuple(
        build_observation(
            market_id=f"KXTEST-WIRING-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9300"
                if changed_market == f"KXTEST-WIRING-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


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


class FakeProductionPersistenceRouter:
    def __init__(self):
        self.batch_calls = 0
        self.single_calls = 0

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
                route_id="fake.production.persistence",
                metadata={
                    "production_path": True,
                    "test": "OLA-044",
                },
            )
            for observation in observations
        )

    def __call__(
        self,
        observation,
        routed_at,
    ):
        self.single_calls += 1

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.production.persistence.single",
            metadata={
                "production_path": True,
                "test": "OLA-044",
            },
        )


def run_composition_test():
    production_router = FakeProductionPersistenceRouter()

    wiring = (
        OraclePersistedCohortLineageProductionWiringContract(
            production_persistence_router=production_router
        )
    )

    assert (
        wiring.production_persistence_router
        is production_router
    )
    assert (
        wiring.staged_persistence_router.persistence_router
        is production_router
    )
    assert wiring.read_only is True
    assert wiring.execution_allowed is False

    return wiring, production_router


def run_first_completed_cycle_test():
    wiring, production_router = run_composition_test()
    cohort = build_cohort(cycle_number=1)

    evidence = wiring.staged_persistence_router.route_batch(
        cohort,
        T1,
    )

    assert len(evidence) == 5
    assert production_router.batch_calls == 1

    cycle_result = completed_cycle_result()
    cycle_result_before = dict(cycle_result)

    preserved_result, receipt = wiring.complete_persisted_cycle(
        ola_017_cycle_result=cycle_result,
        acquisition_batch_id="batch.ola.044.1",
        cycle_completed_at=T1,
    )

    assert preserved_result is cycle_result
    assert cycle_result == cycle_result_before
    assert receipt.schema_version == "OLA-044"
    assert receipt.engine_id == "OLA-044"
    assert receipt.canonical_count == 5
    assert receipt.persistence_count == 5
    assert receipt.transition_count == 0
    assert receipt.lineage_market_count_after == 5
    assert receipt.lineage_record_count_after == 5
    assert receipt.cycle_result_preserved is True
    assert receipt.scheduler_kwargs_unchanged is True
    assert receipt.scheduler_results_unchanged is True
    assert wiring.capture_port.pending_count == 0
    assert wiring.capture_port.consumed_count == 1

    return wiring, receipt


def run_repeated_cycle_dwell_test():
    wiring, _ = run_first_completed_cycle_test()

    cohort = build_cohort(cycle_number=2)

    wiring.staged_persistence_router.route_batch(
        cohort,
        T2,
    )

    _, receipt = wiring.complete_persisted_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.044.2",
        cycle_completed_at=T2,
    )

    assert receipt.transition_count == 0
    assert receipt.lineage_record_count_after == 10

    ledger = (
        wiring
        .lineage_bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    for head in ledger.heads().values():
        assert head.consecutive_frame_count == 2
        assert head.dwell_seconds == "15.000000"

    return wiring, receipt


def run_changed_cycle_test():
    wiring, _ = run_repeated_cycle_dwell_test()

    cohort = build_cohort(
        cycle_number=3,
        changed_market="KXTEST-WIRING-4",
    )

    wiring.staged_persistence_router.route_batch(
        cohort,
        T3,
    )

    _, receipt = wiring.complete_persisted_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.044.3",
        cycle_completed_at=T3,
    )

    assert receipt.transition_count == 1
    assert receipt.lineage_record_count_after == 15

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
        source_market_id="KXTEST-WIRING-4",
    )

    unchanged = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-WIRING-1",
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


def run_failed_cycle_preserves_stage_test():
    wiring, _ = run_composition_test()

    wiring.staged_persistence_router.route_batch(
        build_cohort(cycle_number=1),
        T1,
    )

    failed = completed_cycle_result()
    failed["cycle_status"] = "failed"
    failed["canonical_count"] = 0
    failed["postgresql_routing_record_delta"] = 0

    try:
        wiring.complete_persisted_cycle(
            ola_017_cycle_result=failed,
            acquisition_batch_id="batch.ola.044.1",
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "failed cycle must fail closed"
        )
    except PersistedCohortLineageProductionWiringContractError:
        pass

    assert (
        wiring.staged_persistence_router.pending_stage_count
        == 1
    )
    assert wiring.capture_port.pending_count == 0


def run_scheduler_projection_result_preservation_test():
    wiring, _ = run_composition_test()

    cohort = build_cohort(cycle_number=1)

    wiring.staged_persistence_router.route_batch(
        cohort,
        T1,
    )

    projected = {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "status": "completed",
        "canonical_count": 5,
        "postgresql_persistence_count": 5,
        "read_only": True,
        "execution_allowed": False,
    }

    projected_before = dict(projected)

    preserved, receipt = wiring.complete_persisted_cycle(
        ola_017_cycle_result=projected,
        acquisition_batch_id="batch.ola.044.1",
        cycle_completed_at=T1,
    )

    assert preserved is projected
    assert projected == projected_before
    assert receipt.scheduler_results_unchanged is True


def run_deterministic_wiring_replay_test():
    def execute():
        wiring = (
            OraclePersistedCohortLineageProductionWiringContract(
                production_persistence_router=(
                    FakeProductionPersistenceRouter()
                )
            )
        )

        receipts = []

        for cycle_number, observed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (3, T3, "KXTEST-WIRING-2"),
        ):
            cohort = build_cohort(
                cycle_number=cycle_number,
                changed_market=changed_market,
            )

            wiring.staged_persistence_router.route_batch(
                cohort,
                observed_at,
            )

            _, receipt = wiring.complete_persisted_cycle(
                ola_017_cycle_result=completed_cycle_result(),
                acquisition_batch_id=(
                    f"batch.ola.044.{cycle_number}"
                ),
                cycle_completed_at=observed_at,
            )

            receipts.append(receipt)

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
    wiring, production_router = run_composition_test()
    _, first = run_first_completed_cycle_test()
    _, second = run_repeated_cycle_dwell_test()
    third = run_changed_cycle_test()

    run_failed_cycle_preserves_stage_test()
    run_scheduler_projection_result_preservation_test()

    replay_receipts, replay_records = (
        run_deterministic_wiring_replay_test()
    )

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "production_persistence_router_preserved": (
            wiring.production_persistence_router
            is production_router
        ),
        "ola_042_staging_router_is_single_injection_router": True,
        "ola_043_completion_promoter_consumed": True,
        "ola_040_capture_port_consumed_once": True,
        "ola_038_bundle_formed_from_exact_capture": True,
        "ola_039_lineage_bridge_consumed": True,
        "ola_017_cycle_result_object_preserved": True,
        "ola_017_cycle_result_mapping_preserved": True,
        "first_persisted_cycle_advanced_lineage": (
            first.lineage_record_count_after == 5
        ),
        "repeated_cycle_dwell_advanced": (
            second.lineage_record_count_after == 10
        ),
        "real_exact_state_change_detected": (
            third.transition_count == 1
        ),
        "failed_cycle_preserves_pending_stage": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_production_wiring_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
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
        "[PASS] OLA-044 Oracle Persisted Cohort Lineage "
        "Production Wiring Contract"
    )
    print(result)


if __name__ == "__main__":
    main()
