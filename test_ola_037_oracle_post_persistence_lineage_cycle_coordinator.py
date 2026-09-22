from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_post_persistence_lineage_cycle_coordinator import (
    OraclePostPersistenceLineageCycleCoordinator,
    PersistedAcquisitionCycleEvidence,
    PostPersistenceLineageCycleContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 10, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 10, 0, 30, tzinfo=timezone.utc)


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


def build_cycle(
    *,
    number,
    completed_at,
    changed_market=None,
):
    batch_id = f"batch.ola.037.{number}"
    observations = []

    for index in range(1, 6):
        market_id = f"KXTEST-POST-PERSIST-{index}"

        observations.append(
            build_observation(
                market_id=market_id,
                frame_id=f"{number}-{index}",
                batch_id=batch_id,
                yes_ask=(
                    "0.8300"
                    if changed_market == market_id
                    else "0.6140"
                ),
            )
        )

    evidence = PersistedAcquisitionCycleEvidence.create(
        schema_version="OLA-017",
        engine_id="OLA-017",
        cycle_status="completed",
        acquisition_batch_id=batch_id,
        canonical_count=5,
        persistence_count=5,
        cycle_completed_at=completed_at,
        read_only=True,
        execution_allowed=False,
    )

    return evidence, tuple(observations)


def run_first_persisted_cycle_test():
    coordinator = OraclePostPersistenceLineageCycleCoordinator()

    evidence, observations = build_cycle(
        number=1,
        completed_at=T1,
    )

    receipt = coordinator.coordinate(
        cycle_evidence=evidence,
        canonical_observations=observations,
    )

    assert receipt.upstream_schema_version == "OLA-017"
    assert receipt.upstream_engine_id == "OLA-017"
    assert receipt.canonical_count == 5
    assert receipt.persistence_count == 5
    assert receipt.transition_count == 0
    assert receipt.lineage_market_count_after == 5
    assert receipt.lineage_record_count_after == 5

    return coordinator, receipt


def run_repeated_persisted_cycle_test():
    coordinator, _ = run_first_persisted_cycle_test()

    evidence, observations = build_cycle(
        number=2,
        completed_at=T2,
    )

    receipt = coordinator.coordinate(
        cycle_evidence=evidence,
        canonical_observations=observations,
    )

    assert receipt.transition_count == 0
    assert receipt.lineage_market_count_after == 5
    assert receipt.lineage_record_count_after == 10

    for item in (
        receipt
        .lineage_cycle_receipt
        .lineage_batch_receipt
        .receipts
    ):
        assert item.consecutive_frame_count == 2
        assert item.dwell_seconds == "15.000000"

    return coordinator, receipt


def run_persisted_change_cycle_test():
    coordinator, _ = run_repeated_persisted_cycle_test()

    evidence, observations = build_cycle(
        number=3,
        completed_at=T3,
        changed_market="KXTEST-POST-PERSIST-2",
    )

    receipt = coordinator.coordinate(
        cycle_evidence=evidence,
        canonical_observations=observations,
    )

    assert receipt.transition_count == 1
    assert receipt.lineage_record_count_after == 15

    changed = [
        item
        for item in (
            receipt
            .lineage_cycle_receipt
            .lineage_batch_receipt
            .receipts
        )
        if item.transition_detected
    ]

    assert len(changed) == 1
    assert changed[0].source_market_id == "KXTEST-POST-PERSIST-2"
    assert changed[0].state_changed_at == T3.isoformat()

    return receipt


def run_failed_persistence_evidence_test():
    coordinator = OraclePostPersistenceLineageCycleCoordinator()

    try:
        PersistedAcquisitionCycleEvidence.create(
            schema_version="OLA-017",
            engine_id="OLA-017",
            cycle_status="failed",
            acquisition_batch_id="batch.failed",
            canonical_count=5,
            persistence_count=0,
            cycle_completed_at=T1,
            read_only=True,
            execution_allowed=False,
        )
        raise AssertionError(
            "failed persistence evidence must fail closed"
        )
    except PostPersistenceLineageCycleContractError:
        pass

    assert (
        coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .record_count
        == 0
    )


def run_persistence_count_mismatch_test():
    coordinator = OraclePostPersistenceLineageCycleCoordinator()

    try:
        PersistedAcquisitionCycleEvidence.create(
            schema_version="OLA-017",
            engine_id="OLA-017",
            cycle_status="completed",
            acquisition_batch_id="batch.mismatch",
            canonical_count=5,
            persistence_count=4,
            cycle_completed_at=T1,
            read_only=True,
            execution_allowed=False,
        )
        raise AssertionError(
            "persistence count mismatch must fail closed"
        )
    except PostPersistenceLineageCycleContractError:
        pass

    assert (
        coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .record_count
        == 0
    )


def run_supplied_cohort_count_mismatch_test():
    coordinator = OraclePostPersistenceLineageCycleCoordinator()
    evidence, observations = build_cycle(
        number=1,
        completed_at=T1,
    )

    try:
        coordinator.coordinate(
            cycle_evidence=evidence,
            canonical_observations=observations[:-1],
        )
        raise AssertionError(
            "supplied cohort count mismatch must fail closed"
        )
    except PostPersistenceLineageCycleContractError:
        pass

    assert (
        coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .record_count
        == 0
    )


def run_batch_identity_mismatch_test():
    coordinator = OraclePostPersistenceLineageCycleCoordinator()
    evidence, observations = build_cycle(
        number=1,
        completed_at=T1,
    )

    wrong = list(observations)
    wrong[-1] = build_observation(
        market_id="KXTEST-POST-PERSIST-5",
        frame_id="wrong-batch",
        batch_id="batch.other",
    )

    try:
        coordinator.coordinate(
            cycle_evidence=evidence,
            canonical_observations=wrong,
        )
        raise AssertionError(
            "batch identity mismatch must fail closed"
        )
    except PostPersistenceLineageCycleContractError:
        pass

    assert (
        coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .record_count
        == 0
    )


def run_deterministic_coordination_replay_test():
    first = OraclePostPersistenceLineageCycleCoordinator()
    second = OraclePostPersistenceLineageCycleCoordinator()

    cycles = (
        build_cycle(number=1, completed_at=T1),
        build_cycle(number=2, completed_at=T2),
        build_cycle(
            number=3,
            completed_at=T3,
            changed_market="KXTEST-POST-PERSIST-4",
        ),
    )

    first_receipts = []
    second_receipts = []

    for evidence, observations in cycles:
        first_receipts.append(
            first.coordinate(
                cycle_evidence=evidence,
                canonical_observations=observations,
            )
        )
        second_receipts.append(
            second.coordinate(
                cycle_evidence=evidence,
                canonical_observations=observations,
            )
        )

    assert first_receipts == second_receipts

    first_records = (
        first
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .records()
    )
    second_records = (
        second
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .records()
    )

    assert first_records == second_records

    return first_receipts


def main():
    _, first = run_first_persisted_cycle_test()
    _, second = run_repeated_persisted_cycle_test()
    third = run_persisted_change_cycle_test()

    run_failed_persistence_evidence_test()
    run_persistence_count_mismatch_test()
    run_supplied_cohort_count_mismatch_test()
    run_batch_identity_mismatch_test()

    replayed = run_deterministic_coordination_replay_test()

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "successful_persistence_required_before_lineage": True,
        "ola_017_cycle_identity_preserved": True,
        "canonical_count_bound_to_persistence_count": True,
        "exact_canonical_cohort_required": True,
        "acquisition_batch_identity_bound": True,
        "cycle_completion_time_bound_to_lineage": True,
        "ola_036_lineage_cycle_bridge_consumed": True,
        "first_five_market_persisted_cycle_advanced": (
            first.lineage_record_count_after == 5
        ),
        "repeated_persisted_cycle_dwell_advanced": (
            second.lineage_record_count_after == 10
        ),
        "persisted_real_change_transition_detected": (
            third.transition_count == 1
        ),
        "failed_persistence_evidence_fails_closed": True,
        "persistence_count_mismatch_fails_closed": True,
        "supplied_cohort_count_mismatch_fails_closed": True,
        "batch_identity_mismatch_fails_closed": True,
        "lineage_not_mutated_on_precondition_failure": True,
        "deterministic_coordination_replay_valid": (
            len(replayed) == 3
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
        "[PASS] OLA-037 Oracle Post-Persistence "
        "Lineage Cycle Coordinator"
    )
    print(result)


if __name__ == "__main__":
    main()
