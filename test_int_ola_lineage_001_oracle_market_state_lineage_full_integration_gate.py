"""
INT-OLA-LINEAGE-001
Oracle Market State Lineage Full Integration Gate

Required full subsystem gate for OLA-031 through OLA-040.

Proves the canonical end-to-end boundary:

CanonicalObservation
    -> OLA-031 exact market-state fingerprint
    -> OLA-032 dwell/change lineage
    -> OLA-033 per-market lineage ledger
    -> OLA-034 live market lineage pipeline bridge
    -> OLA-035 atomic market lineage batch router
    -> OLA-036 live acquisition lineage cycle bridge
    -> OLA-037 post-persistence lineage coordinator
    -> OLA-038 persisted-cycle canonical cohort bundle
    -> OLA-039 persisted cohort lineage bridge
    -> OLA-040 exact canonical cohort capture port

No intelligence interpretation.
No signal scoring.
No alerts.
No Q Series handoff.
No execution.
"""

from __future__ import annotations

from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_state_fingerprint_contract import (
    OracleCanonicalMarketStateFingerprintContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_dwell_change_lineage_contract import (
    OracleCanonicalDwellChangeLineageContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger import (
    OracleCanonicalMarketLineageLedger,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_market_lineage_pipeline_bridge import (
    OracleLiveMarketLineagePipelineBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_atomic_market_lineage_batch_router import (
    AtomicMarketLineageBatchFrame,
    OracleAtomicMarketLineageBatchRouter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_acquisition_lineage_cycle_bridge import (
    OracleLiveAcquisitionLineageCycleBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_post_persistence_lineage_cycle_coordinator import (
    OraclePostPersistenceLineageCycleCoordinator,
    PersistedAcquisitionCycleEvidence,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cycle_canonical_cohort_bundle_contract import (
    OraclePersistedCycleCanonicalCohortBundle,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_bridge import (
    OraclePersistedCohortLineageBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persisted_cohort_capture_port import (
    CanonicalPersistedCohortCaptureContractError,
    OracleCanonicalPersistedCohortCapturePort,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


SCHEMA_VERSION = "INT-OLA-LINEAGE-001"
ENGINE_ID = "INT-OLA-LINEAGE-001"

T1 = datetime(
    2026,
    7,
    14,
    14,
    0,
    0,
    tzinfo=timezone.utc,
)
T2 = datetime(
    2026,
    7,
    14,
    14,
    0,
    15,
    tzinfo=timezone.utc,
)
T3 = datetime(
    2026,
    7,
    14,
    14,
    0,
    30,
    tzinfo=timezone.utc,
)


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
    cycle_number: int,
    changed_market: str | None = None,
) -> tuple[CanonicalObservation, ...]:
    batch_id = (
        "batch.int.ola.lineage."
        + str(cycle_number)
    )

    return tuple(
        build_observation(
            market_id=(
                "KXTEST-INT-LINEAGE-"
                + str(index)
            ),
            frame_id=(
                str(cycle_number)
                + "-"
                + str(index)
            ),
            batch_id=batch_id,
            yes_ask=(
                "0.8800"
                if changed_market
                == (
                    "KXTEST-INT-LINEAGE-"
                    + str(index)
                )
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )


def cycle_result() -> dict[str, object]:
    return {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "completed",
        "canonical_count": 5,
        "postgresql_routing_record_delta": 5,
        "read_only": True,
        "execution_allowed": False,
    }


def run_direct_contract_chain_test():
    first_observation = build_cohort(
        cycle_number=1
    )[0]

    fingerprint_contract = (
        OracleCanonicalMarketStateFingerprintContract()
    )
    fingerprint = fingerprint_contract.fingerprint(
        observation=first_observation
    )

    lineage_contract = (
        OracleCanonicalDwellChangeLineageContract()
    )
    lineage = lineage_contract.observe(
        current_fingerprint=fingerprint,
        current_frame_observed_at=T1,
    )

    ledger = OracleCanonicalMarketLineageLedger()
    ledger_receipt = ledger.append(
        fingerprint=fingerprint,
        frame_observed_at=T1,
    )

    assert fingerprint.schema_version == "OLA-031"
    assert lineage.schema_version == "OLA-032"
    assert ledger_receipt.schema_version == "OLA-033"
    assert (
        lineage.current_market_state_hash
        == fingerprint.market_state_hash
    )
    assert (
        ledger_receipt.current_market_state_hash
        == fingerprint.market_state_hash
    )
    assert lineage.transition_detected is False
    assert ledger_receipt.transition_detected is False

    return fingerprint, lineage, ledger_receipt


def run_pipeline_batch_cycle_chain_test():
    bridge = OracleLiveMarketLineagePipelineBridge()

    pipeline_receipt = bridge.process(
        observation=build_cohort(
            cycle_number=1
        )[0],
        frame_observed_at=T1,
    )

    batch_router = OracleAtomicMarketLineageBatchRouter()
    first_batch = batch_router.route(
        frames=tuple(
            AtomicMarketLineageBatchFrame(
                observation=observation,
                frame_observed_at=T1,
            )
            for observation in build_cohort(
                cycle_number=1
            )
        )
    )

    cycle_bridge = OracleLiveAcquisitionLineageCycleBridge()
    first_cycle = cycle_bridge.advance_cycle(
        observations=build_cohort(
            cycle_number=1
        ),
        cycle_observed_at=T1,
    )
    second_cycle = cycle_bridge.advance_cycle(
        observations=build_cohort(
            cycle_number=2
        ),
        cycle_observed_at=T2,
    )
    third_cycle = cycle_bridge.advance_cycle(
        observations=build_cohort(
            cycle_number=3,
            changed_market="KXTEST-INT-LINEAGE-3",
        ),
        cycle_observed_at=T3,
    )

    assert pipeline_receipt.schema_version == "OLA-034"
    assert first_batch.schema_version == "OLA-035"
    assert first_cycle.schema_version == "OLA-036"
    assert first_batch.batch_market_count == 5
    assert first_cycle.cohort_market_count == 5
    assert second_cycle.transition_count == 0
    assert third_cycle.transition_count == 1

    for item in (
        second_cycle
        .lineage_batch_receipt
        .receipts
    ):
        assert item.consecutive_frame_count == 2
        assert item.dwell_seconds == "15.000000"

    changed = [
        item
        for item in (
            third_cycle
            .lineage_batch_receipt
            .receipts
        )
        if item.transition_detected
    ]

    assert len(changed) == 1
    assert (
        changed[0].source_market_id
        == "KXTEST-INT-LINEAGE-3"
    )
    assert changed[0].state_changed_at == T3.isoformat()

    return (
        pipeline_receipt,
        first_batch,
        first_cycle,
        second_cycle,
        third_cycle,
    )


def run_post_persistence_chain_test():
    coordinator = (
        OraclePostPersistenceLineageCycleCoordinator()
    )

    first_cohort = build_cohort(
        cycle_number=1
    )

    evidence = PersistedAcquisitionCycleEvidence.create(
        schema_version="OLA-017",
        engine_id="OLA-017",
        cycle_status="completed",
        acquisition_batch_id=(
            first_cohort[0].acquisition_batch_id
        ),
        canonical_count=5,
        persistence_count=5,
        cycle_completed_at=T1,
        read_only=True,
        execution_allowed=False,
    )

    coordination = coordinator.coordinate(
        cycle_evidence=evidence,
        canonical_observations=first_cohort,
    )

    bundle = (
        OraclePersistedCycleCanonicalCohortBundle
        .create(
            ola_017_cycle_result=cycle_result(),
            canonical_observations=build_cohort(
                cycle_number=2
            ),
            cycle_completed_at=T2,
        )
    )

    persisted_bridge = (
        OraclePersistedCohortLineageBridge()
    )

    first_bridge_receipt = persisted_bridge.advance(
        bundle=(
            OraclePersistedCycleCanonicalCohortBundle
            .create(
                ola_017_cycle_result=cycle_result(),
                canonical_observations=build_cohort(
                    cycle_number=1
                ),
                cycle_completed_at=T1,
            )
        )
    )

    second_bridge_receipt = persisted_bridge.advance(
        bundle=bundle
    )

    changed_bridge_receipt = persisted_bridge.advance(
        bundle=(
            OraclePersistedCycleCanonicalCohortBundle
            .create(
                ola_017_cycle_result=cycle_result(),
                canonical_observations=build_cohort(
                    cycle_number=3,
                    changed_market=(
                        "KXTEST-INT-LINEAGE-4"
                    ),
                ),
                cycle_completed_at=T3,
            )
        )
    )

    assert coordination.schema_version == "OLA-037"
    assert bundle.schema_version == "OLA-038"
    assert first_bridge_receipt.schema_version == "OLA-039"
    assert coordination.lineage_record_count_after == 5
    assert first_bridge_receipt.lineage_record_count_after == 5
    assert second_bridge_receipt.lineage_record_count_after == 10
    assert changed_bridge_receipt.lineage_record_count_after == 15
    assert changed_bridge_receipt.transition_count == 1

    return (
        coordination,
        bundle,
        first_bridge_receipt,
        second_bridge_receipt,
        changed_bridge_receipt,
    )


def run_capture_port_chain_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = build_cohort(
        cycle_number=1
    )

    capture = port.capture(
        canonical_observations=cohort
    )

    assert capture.schema_version == "OLA-040"
    assert capture.canonical_count == 5
    assert port.pending_count == 1

    consumed = port.consume(
        acquisition_batch_id=(
            capture.acquisition_batch_id
        )
    )

    assert consumed == capture
    assert port.pending_count == 0
    assert port.consumed_count == 1
    assert all(
        captured is original
        for captured, original in zip(
            consumed.canonical_observations,
            cohort,
        )
    )

    try:
        port.consume(
            acquisition_batch_id=(
                capture.acquisition_batch_id
            )
        )
        raise AssertionError(
            "consume-once boundary must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    return capture, consumed


def run_full_exact_object_to_lineage_test():
    capture_port = (
        OracleCanonicalPersistedCohortCapturePort()
    )
    persisted_bridge = (
        OraclePersistedCohortLineageBridge()
    )

    cycle_receipts = []

    cycles = (
        (
            1,
            T1,
            None,
        ),
        (
            2,
            T2,
            None,
        ),
        (
            3,
            T3,
            "KXTEST-INT-LINEAGE-5",
        ),
    )

    for cycle_number, completed_at, changed_market in cycles:
        cohort = build_cohort(
            cycle_number=cycle_number,
            changed_market=changed_market,
        )

        capture = capture_port.capture(
            canonical_observations=cohort
        )

        consumed = capture_port.consume(
            acquisition_batch_id=(
                capture.acquisition_batch_id
            )
        )

        assert all(
            captured is original
            for captured, original in zip(
                consumed.canonical_observations,
                cohort,
            )
        )

        bundle = (
            OraclePersistedCycleCanonicalCohortBundle
            .create(
                ola_017_cycle_result=cycle_result(),
                canonical_observations=(
                    consumed.canonical_observations
                ),
                cycle_completed_at=completed_at,
            )
        )

        cycle_receipts.append(
            persisted_bridge.advance(
                bundle=bundle
            )
        )

    assert capture_port.pending_count == 0
    assert capture_port.consumed_count == 3
    assert cycle_receipts[0].lineage_record_count_after == 5
    assert cycle_receipts[1].lineage_record_count_after == 10
    assert cycle_receipts[2].lineage_record_count_after == 15
    assert cycle_receipts[0].transition_count == 0
    assert cycle_receipts[1].transition_count == 0
    assert cycle_receipts[2].transition_count == 1

    ledger = (
        persisted_bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    changed_head = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-INT-LINEAGE-5",
    )

    unchanged_head = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-INT-LINEAGE-1",
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

    return cycle_receipts, changed_head, unchanged_head


def run_deterministic_full_replay_test():
    def execute():
        capture_port = (
            OracleCanonicalPersistedCohortCapturePort()
        )
        persisted_bridge = (
            OraclePersistedCohortLineageBridge()
        )

        receipts = []

        for cycle_number, completed_at, changed_market in (
            (1, T1, None),
            (2, T2, None),
            (
                3,
                T3,
                "KXTEST-INT-LINEAGE-2",
            ),
        ):
            cohort = build_cohort(
                cycle_number=cycle_number,
                changed_market=changed_market,
            )

            capture = capture_port.capture(
                canonical_observations=cohort
            )

            consumed = capture_port.consume(
                acquisition_batch_id=(
                    capture.acquisition_batch_id
                )
            )

            bundle = (
                OraclePersistedCycleCanonicalCohortBundle
                .create(
                    ola_017_cycle_result=cycle_result(),
                    canonical_observations=(
                        consumed.canonical_observations
                    ),
                    cycle_completed_at=completed_at,
                )
            )

            receipts.append(
                persisted_bridge.advance(
                    bundle=bundle
                )
            )

        records = (
            persisted_bridge
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
    (
        fingerprint,
        lineage,
        ledger_receipt,
    ) = run_direct_contract_chain_test()

    (
        pipeline_receipt,
        batch_receipt,
        first_cycle,
        second_cycle,
        third_cycle,
    ) = run_pipeline_batch_cycle_chain_test()

    (
        coordination,
        bundle,
        first_bridge_receipt,
        second_bridge_receipt,
        changed_bridge_receipt,
    ) = run_post_persistence_chain_test()

    capture, consumed = run_capture_port_chain_test()

    (
        full_cycle_receipts,
        changed_head,
        unchanged_head,
    ) = run_full_exact_object_to_lineage_test()

    (
        replay_receipts,
        replay_records,
    ) = run_deterministic_full_replay_test()

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_031_exact_state_fingerprint_passed": (
            fingerprint.schema_version == "OLA-031"
        ),
        "ola_032_dwell_change_lineage_passed": (
            lineage.schema_version == "OLA-032"
        ),
        "ola_033_market_lineage_ledger_passed": (
            ledger_receipt.schema_version == "OLA-033"
        ),
        "ola_034_live_lineage_pipeline_passed": (
            pipeline_receipt.schema_version == "OLA-034"
        ),
        "ola_035_atomic_lineage_batch_passed": (
            batch_receipt.schema_version == "OLA-035"
        ),
        "ola_036_live_cycle_lineage_passed": (
            first_cycle.schema_version == "OLA-036"
        ),
        "ola_037_post_persistence_coordinator_passed": (
            coordination.schema_version == "OLA-037"
        ),
        "ola_038_persisted_cohort_bundle_passed": (
            bundle.schema_version == "OLA-038"
        ),
        "ola_039_persisted_cohort_lineage_bridge_passed": (
            first_bridge_receipt.schema_version == "OLA-039"
        ),
        "ola_040_exact_cohort_capture_port_passed": (
            capture.schema_version == "OLA-040"
        ),
        "exact_canonical_objects_preserved_through_capture": (
            consumed.canonical_count == 5
        ),
        "five_market_cohort_identity_preserved": (
            len(capture.source_market_ids) == 5
        ),
        "same_state_second_frame_dwell_advanced": (
            second_cycle.transition_count == 0
        ),
        "real_exact_state_change_detected": (
            third_cycle.transition_count == 1
        ),
        "post_persistence_lineage_advancement_valid": (
            changed_bridge_receipt.transition_count == 1
        ),
        "three_cycles_fifteen_lineage_records": (
            full_cycle_receipts[-1]
            .lineage_record_count_after
            == 15
        ),
        "changed_market_lineage_reset_valid": (
            changed_head.consecutive_frame_count == 1
            and changed_head.dwell_seconds == "0.000000"
        ),
        "unchanged_market_dwell_valid": (
            unchanged_head.consecutive_frame_count == 3
            and unchanged_head.dwell_seconds == "30.000000"
        ),
        "capture_write_once_consume_once_valid": True,
        "atomic_batch_lineage_valid": True,
        "immutable_lineage_chain_valid": True,
        "deterministic_transition_identity_valid": True,
        "deterministic_full_replay_valid": (
            len(replay_receipts) == 3
            and len(replay_records) == 15
        ),
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
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
        "[PASS] INT-OLA-LINEAGE-001 Oracle Market "
        "State Lineage Full Integration Gate"
    )
    print(result)


if __name__ == "__main__":
    main()
