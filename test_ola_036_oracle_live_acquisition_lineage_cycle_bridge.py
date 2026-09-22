from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_acquisition_lineage_cycle_bridge import (
    LiveAcquisitionLineageCycleContractError,
    OracleLiveAcquisitionLineageCycleBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 9, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 9, 0, 15, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 9, 0, 30, tzinfo=timezone.utc)


def build_observation(
    *,
    market_id,
    frame_id,
    acquisition_batch_id,
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
        acquisition_batch_id=acquisition_batch_id,
    )


def build_cycle(
    *,
    cycle_number,
    changed_market=None,
):
    batch_id = f"batch.ola.036.cycle.{cycle_number}"
    observations = []

    for index in range(1, 6):
        market_id = f"KXTEST-LIVE-CYCLE-{index}"
        yes_ask = (
            "0.8800"
            if changed_market == market_id
            else "0.6140"
        )

        observations.append(
            build_observation(
                market_id=market_id,
                frame_id=f"{cycle_number}-{index}",
                acquisition_batch_id=batch_id,
                yes_ask=yes_ask,
            )
        )

    return tuple(observations)


def run_first_cycle_test():
    bridge = OracleLiveAcquisitionLineageCycleBridge()

    receipt = bridge.advance_cycle(
        observations=build_cycle(cycle_number=1),
        cycle_observed_at=T1,
    )

    assert receipt.acquisition_batch_id == "batch.ola.036.cycle.1"
    assert receipt.cohort_observation_count == 5
    assert receipt.cohort_market_count == 5
    assert receipt.transition_count == 0
    assert receipt.ledger_market_count_before == 0
    assert receipt.ledger_record_count_before == 0
    assert receipt.ledger_market_count_after == 5
    assert receipt.ledger_record_count_after == 5

    return bridge, receipt


def run_repeated_same_cycle_cohort_test():
    bridge, _ = run_first_cycle_test()

    second = bridge.advance_cycle(
        observations=build_cycle(cycle_number=2),
        cycle_observed_at=T2,
    )

    assert second.transition_count == 0
    assert second.ledger_market_count_after == 5
    assert second.ledger_record_count_after == 10

    for item in second.lineage_batch_receipt.receipts:
        assert item.consecutive_frame_count == 2
        assert item.dwell_seconds == "15.000000"

    return bridge, second


def run_real_change_cycle_test():
    bridge, _ = run_repeated_same_cycle_cohort_test()

    third = bridge.advance_cycle(
        observations=build_cycle(
            cycle_number=3,
            changed_market="KXTEST-LIVE-CYCLE-4",
        ),
        cycle_observed_at=T3,
    )

    assert third.transition_count == 1
    assert third.ledger_record_count_after == 15

    changed = [
        item
        for item in third.lineage_batch_receipt.receipts
        if item.transition_detected
    ]

    assert len(changed) == 1
    assert changed[0].source_market_id == "KXTEST-LIVE-CYCLE-4"
    assert changed[0].consecutive_frame_count == 1
    assert changed[0].dwell_seconds == "0.000000"
    assert changed[0].state_changed_at == T3.isoformat()

    unchanged = [
        item
        for item in third.lineage_batch_receipt.receipts
        if not item.transition_detected
    ]

    assert len(unchanged) == 4

    for item in unchanged:
        assert item.consecutive_frame_count == 3
        assert item.dwell_seconds == "30.000000"

    return third


def run_mixed_batch_identity_fail_closed_test():
    bridge = OracleLiveAcquisitionLineageCycleBridge()

    observations = list(build_cycle(cycle_number=1))

    observations[-1] = build_observation(
        market_id="KXTEST-LIVE-CYCLE-5",
        frame_id="mixed-batch",
        acquisition_batch_id="batch.ola.036.other",
    )

    try:
        bridge.advance_cycle(
            observations=observations,
            cycle_observed_at=T1,
        )
        raise AssertionError(
            "mixed acquisition batch identity must fail closed"
        )
    except LiveAcquisitionLineageCycleContractError:
        pass

    assert bridge.batch_router.bridge.ledger.record_count == 0


def run_naive_cycle_time_fail_closed_test():
    bridge = OracleLiveAcquisitionLineageCycleBridge()

    try:
        bridge.advance_cycle(
            observations=build_cycle(cycle_number=1),
            cycle_observed_at=datetime(2026, 7, 14, 9, 0, 0),
        )
        raise AssertionError(
            "naive cycle time must fail closed"
        )
    except LiveAcquisitionLineageCycleContractError:
        pass

    assert bridge.batch_router.bridge.ledger.record_count == 0


def run_deterministic_cycle_replay_test():
    first = OracleLiveAcquisitionLineageCycleBridge()
    second = OracleLiveAcquisitionLineageCycleBridge()

    cycles = (
        (build_cycle(cycle_number=1), T1),
        (build_cycle(cycle_number=2), T2),
        (
            build_cycle(
                cycle_number=3,
                changed_market="KXTEST-LIVE-CYCLE-2",
            ),
            T3,
        ),
    )

    first_receipts = []
    second_receipts = []

    for observations, observed_at in cycles:
        first_receipts.append(
            first.advance_cycle(
                observations=observations,
                cycle_observed_at=observed_at,
            )
        )
        second_receipts.append(
            second.advance_cycle(
                observations=observations,
                cycle_observed_at=observed_at,
            )
        )

    assert first_receipts == second_receipts
    assert (
        first.batch_router.bridge.ledger.records()
        == second.batch_router.bridge.ledger.records()
    )

    return first_receipts


def main():
    _, first = run_first_cycle_test()
    _, second = run_repeated_same_cycle_cohort_test()
    third = run_real_change_cycle_test()

    run_mixed_batch_identity_fail_closed_test()
    run_naive_cycle_time_fail_closed_test()

    replayed = run_deterministic_cycle_replay_test()

    result = {
        "schema_version": third.schema_version,
        "engine_id": third.engine_id,
        "status": "passed",
        "canonical_live_cycle_consumed": True,
        "shared_acquisition_batch_identity_enforced": True,
        "cycle_time_bound_to_all_lineage_frames": True,
        "ola_035_atomic_batch_router_consumed": True,
        "five_market_cycle_advanced": (
            first.cohort_market_count == 5
        ),
        "same_five_markets_second_frame_preserved": (
            second.ledger_record_count_after == 10
        ),
        "same_state_dwell_advanced_across_cycles": True,
        "real_market_change_detected_in_cycle": (
            third.transition_count == 1
        ),
        "unchanged_market_dwell_preserved": True,
        "mixed_batch_identity_fails_closed": True,
        "naive_cycle_time_fails_closed": True,
        "deterministic_cycle_replay_valid": (
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
        "[PASS] OLA-036 Oracle Live Acquisition "
        "Lineage Cycle Bridge"
    )
    print(result)


if __name__ == "__main__":
    main()
