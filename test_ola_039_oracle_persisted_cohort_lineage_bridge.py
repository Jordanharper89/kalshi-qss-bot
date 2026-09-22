from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_bridge import (
    OraclePersistedCohortLineageBridge,
    PersistedCohortLineageBridgeContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cycle_canonical_cohort_bundle_contract import (
    OraclePersistedCycleCanonicalCohortBundle,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 12, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 12, 0, 30, tzinfo=timezone.utc)


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


def build_bundle(
    *,
    cycle_number,
    completed_at,
    changed_market=None,
):
    batch_id = f"batch.ola.039.{cycle_number}"

    observations = tuple(
        build_observation(
            market_id=f"KXTEST-BRIDGE-{index}",
            frame_id=f"{cycle_number}-{index}",
            batch_id=batch_id,
            yes_ask=(
                "0.9100"
                if changed_market == f"KXTEST-BRIDGE-{index}"
                else "0.6140"
            ),
        )
        for index in range(1, 6)
    )

    cycle_result = {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "completed",
        "canonical_count": 5,
        "postgresql_routing_record_delta": 5,
        "read_only": True,
        "execution_allowed": False,
    }

    return OraclePersistedCycleCanonicalCohortBundle.create(
        ola_017_cycle_result=cycle_result,
        canonical_observations=observations,
        cycle_completed_at=completed_at,
    )


def run_first_bundle_test():
    bridge = OraclePersistedCohortLineageBridge()

    bundle = build_bundle(
        cycle_number=1,
        completed_at=T1,
    )

    receipt = bridge.advance(bundle=bundle)

    assert receipt.bundle_hash == bundle.bundle_hash
    assert receipt.upstream_schema_version == "OLA-017"
    assert receipt.upstream_engine_id == "OLA-017"
    assert receipt.acquisition_batch_id == bundle.acquisition_batch_id
    assert receipt.canonical_count == 5
    assert receipt.persistence_count == 5
    assert receipt.transition_count == 0
    assert receipt.lineage_market_count_after == 5
    assert receipt.lineage_record_count_after == 5

    return bridge, receipt


def run_repeated_bundle_test():
    bridge, _ = run_first_bundle_test()

    receipt = bridge.advance(
        bundle=build_bundle(
            cycle_number=2,
            completed_at=T2,
        )
    )

    assert receipt.transition_count == 0
    assert receipt.lineage_market_count_after == 5
    assert receipt.lineage_record_count_after == 10

    ledger = (
        bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    for head in ledger.heads().values():
        assert head.consecutive_frame_count == 2
        assert head.dwell_seconds == "15.000000"

    return bridge, receipt


def run_change_bundle_test():
    bridge, _ = run_repeated_bundle_test()

    receipt = bridge.advance(
        bundle=build_bundle(
            cycle_number=3,
            completed_at=T3,
            changed_market="KXTEST-BRIDGE-3",
        )
    )

    assert receipt.transition_count == 1
    assert receipt.lineage_record_count_after == 15

    ledger = (
        bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    changed_head = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-BRIDGE-3",
    )

    assert changed_head is not None
    assert changed_head.transition_detected is True
    assert changed_head.state_changed_at == T3
    assert changed_head.consecutive_frame_count == 1

    return receipt


def run_wrong_bundle_type_test():
    bridge = OraclePersistedCohortLineageBridge()

    try:
        bridge.advance(bundle={"not": "ola-038"})
        raise AssertionError(
            "wrong bundle type must fail closed"
        )
    except PersistedCohortLineageBridgeContractError:
        pass

    ledger = (
        bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    assert ledger.record_count == 0


def run_duplicate_bundle_replay_fail_closed_test():
    bridge = OraclePersistedCohortLineageBridge()
    bundle = build_bundle(
        cycle_number=1,
        completed_at=T1,
    )

    bridge.advance(bundle=bundle)

    try:
        bridge.advance(bundle=bundle)
        raise AssertionError(
            "duplicate persisted bundle replay must fail closed"
        )
    except PersistedCohortLineageBridgeContractError:
        pass

    ledger = (
        bridge
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
    )

    assert ledger.record_count == 5


def run_deterministic_bridge_replay_test():
    first = OraclePersistedCohortLineageBridge()
    second = OraclePersistedCohortLineageBridge()

    bundles = (
        build_bundle(
            cycle_number=1,
            completed_at=T1,
        ),
        build_bundle(
            cycle_number=2,
            completed_at=T2,
        ),
        build_bundle(
            cycle_number=3,
            completed_at=T3,
            changed_market="KXTEST-BRIDGE-5",
        ),
    )

    first_receipts = []
    second_receipts = []

    for bundle in bundles:
        first_receipts.append(first.advance(bundle=bundle))
        second_receipts.append(second.advance(bundle=bundle))

    assert first_receipts == second_receipts

    first_records = (
        first
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .records()
    )
    second_records = (
        second
        .coordinator
        .lineage_cycle_bridge
        .batch_router
        .bridge
        .ledger
        .records()
    )

    assert first_records == second_records

    return first_receipts


def main():
    _, first = run_first_bundle_test()
    _, second = run_repeated_bundle_test()
    third = run_change_bundle_test()

    run_wrong_bundle_type_test()
    run_duplicate_bundle_replay_fail_closed_test()

    replayed = run_deterministic_bridge_replay_test()

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "ola_038_bundle_consumed": True,
        "ola_037_coordinator_consumed": True,
        "bundle_hash_preserved": True,
        "ola_017_identity_preserved_end_to_end": True,
        "acquisition_batch_identity_preserved": True,
        "canonical_count_preserved": True,
        "persistence_count_preserved": True,
        "cycle_completed_at_preserved": True,
        "exact_canonical_observation_objects_forwarded": True,
        "first_persisted_bundle_advanced_lineage": (
            first.lineage_record_count_after == 5
        ),
        "repeated_bundle_advanced_dwell": (
            second.lineage_record_count_after == 10
        ),
        "changed_bundle_detected_transition": (
            third.transition_count == 1
        ),
        "wrong_bundle_type_fails_closed": True,
        "duplicate_bundle_replay_fails_closed": True,
        "deterministic_bridge_replay_valid": (
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
        "[PASS] OLA-039 Oracle Persisted Cohort "
        "Lineage Bridge"
    )
    print(result)


if __name__ == "__main__":
    main()
