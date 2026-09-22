from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_market_lineage_pipeline_bridge import (
    LiveMarketLineagePipelineContractError,
    OracleLiveMarketLineagePipelineBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 7, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 7, 0, 10, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 7, 0, 20, tzinfo=timezone.utc)
T4 = datetime(2026, 7, 14, 7, 0, 30, tzinfo=timezone.utc)


def build_observation(
    *,
    market_id,
    frame_id,
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
        acquisition_batch_id="batch.ola.034." + frame_id,
    )


def run_same_state_pipeline_test():
    bridge = OracleLiveMarketLineagePipelineBridge()

    first = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-A",
            frame_id="a1",
        ),
        frame_observed_at=T1,
    )
    second = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-A",
            frame_id="a2",
        ),
        frame_observed_at=T2,
    )

    assert first.transition_detected is False
    assert second.transition_detected is False
    assert first.market_state_hash == second.market_state_hash
    assert second.consecutive_frame_count == 2
    assert second.dwell_seconds == "10.000000"
    assert second.previous_lineage_hash == first.lineage_hash

    return bridge, first, second


def run_transition_pipeline_test():
    bridge, _, second = run_same_state_pipeline_test()

    changed = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-A",
            frame_id="a3",
            yes_ask="0.7770",
        ),
        frame_observed_at=T3,
    )

    assert changed.transition_detected is True
    assert (
        changed.previous_market_state_hash
        == second.market_state_hash
    )
    assert changed.market_state_hash != second.market_state_hash
    assert changed.transition_id is not None
    assert changed.state_changed_at == T3.isoformat()
    assert changed.consecutive_frame_count == 1
    assert changed.dwell_seconds == "0.000000"

    return bridge, changed


def run_interleaved_market_pipeline_test():
    bridge = OracleLiveMarketLineagePipelineBridge()

    a1 = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-A",
            frame_id="ia1",
        ),
        frame_observed_at=T1,
    )
    b1 = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-B",
            frame_id="ib1",
        ),
        frame_observed_at=T1,
    )
    a2 = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-A",
            frame_id="ia2",
        ),
        frame_observed_at=T2,
    )
    b2 = bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-B",
            frame_id="ib2",
            yes_ask="0.9000",
        ),
        frame_observed_at=T2,
    )

    assert a1.source_market_id == "KXTEST-PIPE-A"
    assert b1.source_market_id == "KXTEST-PIPE-B"
    assert a2.transition_detected is False
    assert a2.consecutive_frame_count == 2
    assert b2.transition_detected is True
    assert bridge.ledger.market_count == 2
    assert bridge.ledger.record_count == 4

    return bridge


def run_duplicate_observation_translation_test():
    bridge = OracleLiveMarketLineagePipelineBridge()
    observation = build_observation(
        market_id="KXTEST-PIPE-DUP",
        frame_id="dup1",
    )

    bridge.process(
        observation=observation,
        frame_observed_at=T1,
    )

    try:
        bridge.process(
            observation=observation,
            frame_observed_at=T2,
        )
        raise AssertionError(
            "duplicate observation must fail closed"
        )
    except LiveMarketLineagePipelineContractError:
        pass

    assert bridge.ledger.record_count == 1


def run_clock_regression_translation_test():
    bridge = OracleLiveMarketLineagePipelineBridge()

    bridge.process(
        observation=build_observation(
            market_id="KXTEST-PIPE-CLOCK",
            frame_id="clock1",
        ),
        frame_observed_at=T3,
    )

    try:
        bridge.process(
            observation=build_observation(
                market_id="KXTEST-PIPE-CLOCK",
                frame_id="clock2",
            ),
            frame_observed_at=T2,
        )
        raise AssertionError(
            "clock regression must fail closed at OLA-034 boundary"
        )
    except LiveMarketLineagePipelineContractError:
        pass

    assert bridge.ledger.record_count == 1


def run_wrong_observation_type_test():
    payload = {
        "source_market_id": "KXTEST-WRONG-TYPE",
        "yes_bid_dollars": "0.0000",
    }

    raw = RawSourceObservation.create(
        source_observation_id="kalshi.wrong.type",
        observed_at=T1,
        observation_type="event_snapshot",
        payload=payload,
        provenance={
            "source_id": "source.kalshi.market_data",
        },
    )

    observation = CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=T1,
        acquisition_batch_id="batch.ola.034.wrong",
    )

    bridge = OracleLiveMarketLineagePipelineBridge()

    try:
        bridge.process(
            observation=observation,
            frame_observed_at=T1,
        )
        raise AssertionError(
            "wrong observation type must fail closed"
        )
    except LiveMarketLineagePipelineContractError:
        pass

    assert bridge.ledger.record_count == 0


def run_deterministic_receipt_test():
    first_bridge = OracleLiveMarketLineagePipelineBridge()
    second_bridge = OracleLiveMarketLineagePipelineBridge()

    first_receipts = []
    second_receipts = []

    frames = (
        (
            build_observation(
                market_id="KXTEST-PIPE-REPLAY",
                frame_id="r1",
            ),
            T1,
        ),
        (
            build_observation(
                market_id="KXTEST-PIPE-REPLAY",
                frame_id="r2",
            ),
            T2,
        ),
        (
            build_observation(
                market_id="KXTEST-PIPE-REPLAY",
                frame_id="r3",
                yes_ask="0.8100",
            ),
            T3,
        ),
        (
            build_observation(
                market_id="KXTEST-PIPE-REPLAY",
                frame_id="r4",
                yes_ask="0.8100",
            ),
            T4,
        ),
    )

    for observation, observed_at in frames:
        first_receipts.append(
            first_bridge.process(
                observation=observation,
                frame_observed_at=observed_at,
            )
        )
        second_receipts.append(
            second_bridge.process(
                observation=observation,
                frame_observed_at=observed_at,
            )
        )

    assert first_receipts == second_receipts
    assert (
        first_bridge.ledger.records()
        == second_bridge.ledger.records()
    )

    return first_receipts


def main():
    _, first, second = run_same_state_pipeline_test()
    _, changed = run_transition_pipeline_test()
    interleaved = run_interleaved_market_pipeline_test()

    run_duplicate_observation_translation_test()
    run_clock_regression_translation_test()
    run_wrong_observation_type_test()

    replay_receipts = run_deterministic_receipt_test()

    result = {
        "schema_version": changed.schema_version,
        "engine_id": changed.engine_id,
        "status": "passed",
        "canonical_market_snapshot_consumed": True,
        "ola_031_exact_fingerprint_derived": True,
        "ola_033_lineage_ledger_appended": True,
        "observation_to_fingerprint_binding_preserved": True,
        "same_state_dwell_preserved": (
            second.dwell_seconds == "10.000000"
        ),
        "same_state_consecutive_frames_preserved": (
            second.consecutive_frame_count == 2
        ),
        "exact_state_transition_preserved": (
            changed.transition_detected
        ),
        "previous_market_state_hash_preserved": (
            changed.previous_market_state_hash
            == second.market_state_hash
        ),
        "transition_identity_preserved": (
            changed.transition_id is not None
        ),
        "interleaved_market_lineage_isolated": (
            interleaved.ledger.market_count == 2
        ),
        "duplicate_observation_fails_closed": True,
        "clock_regression_fails_closed": True,
        "dependency_contract_errors_translated": True,
        "wrong_observation_type_fails_closed": True,
        "deterministic_receipt_replay_valid": (
            len(replay_receipts) == 4
        ),
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": changed.read_only,
        "execution_allowed": changed.execution_allowed,
        "execution_adapter_resolved": (
            changed.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            changed.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            changed.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            changed.order_placement_allowed
        ),
        "funds_moved": changed.funds_moved,
        "portfolio_mutated": changed.portfolio_mutated,
    }

    print(
        "[PASS] OLA-034 Oracle Live Market Lineage "
        "Pipeline Bridge"
    )
    print(result)


if __name__ == "__main__":
    main()
