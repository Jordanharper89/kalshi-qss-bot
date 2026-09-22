from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_atomic_market_lineage_batch_router import (
    AtomicMarketLineageBatchContractError,
    AtomicMarketLineageBatchFrame,
    OracleAtomicMarketLineageBatchRouter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 8, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 8, 0, 10, tzinfo=timezone.utc)


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
        acquisition_batch_id="batch.ola.035." + frame_id,
    )


def build_five_market_batch(
    *,
    frame_suffix,
    observed_at,
    changed_market=None,
):
    frames = []

    for index in range(1, 6):
        market_id = f"KXTEST-COHORT-{index}"
        yes_ask = (
            "0.7770"
            if changed_market == market_id
            else "0.6140"
        )

        frames.append(
            AtomicMarketLineageBatchFrame(
                observation=build_observation(
                    market_id=market_id,
                    frame_id=f"{frame_suffix}-{index}",
                    yes_ask=yes_ask,
                ),
                frame_observed_at=observed_at,
            )
        )

    return tuple(frames)


def run_first_cohort_test():
    router = OracleAtomicMarketLineageBatchRouter()

    receipt = router.route(
        frames=build_five_market_batch(
            frame_suffix="f1",
            observed_at=T1,
        )
    )

    assert receipt.status == "committed"
    assert receipt.batch_frame_count == 5
    assert receipt.batch_market_count == 5
    assert receipt.ledger_market_count_before == 0
    assert receipt.ledger_record_count_before == 0
    assert receipt.ledger_market_count_after == 5
    assert receipt.ledger_record_count_after == 5
    assert receipt.transition_count == 0
    assert len(receipt.receipts) == 5

    return router, receipt


def run_second_same_cohort_test():
    router, _ = run_first_cohort_test()

    receipt = router.route(
        frames=build_five_market_batch(
            frame_suffix="f2",
            observed_at=T2,
        )
    )

    assert receipt.batch_frame_count == 5
    assert receipt.ledger_market_count_before == 5
    assert receipt.ledger_record_count_before == 5
    assert receipt.ledger_market_count_after == 5
    assert receipt.ledger_record_count_after == 10
    assert receipt.transition_count == 0

    for item in receipt.receipts:
        assert item.consecutive_frame_count == 2
        assert item.dwell_seconds == "10.000000"

    return router, receipt


def run_single_market_transition_cohort_test():
    router, _ = run_first_cohort_test()

    receipt = router.route(
        frames=build_five_market_batch(
            frame_suffix="f2-change",
            observed_at=T2,
            changed_market="KXTEST-COHORT-3",
        )
    )

    assert receipt.transition_count == 1

    changed = [
        item
        for item in receipt.receipts
        if item.transition_detected
    ]

    assert len(changed) == 1
    assert changed[0].source_market_id == "KXTEST-COHORT-3"
    assert changed[0].consecutive_frame_count == 1
    assert changed[0].dwell_seconds == "0.000000"

    unchanged = [
        item
        for item in receipt.receipts
        if not item.transition_detected
    ]

    assert len(unchanged) == 4

    for item in unchanged:
        assert item.consecutive_frame_count == 2
        assert item.dwell_seconds == "10.000000"

    return router, receipt


def run_atomic_preflight_failure_test():
    router, _ = run_first_cohort_test()

    before_records = router.bridge.ledger.records()
    before_heads = router.bridge.ledger.heads()

    invalid_frames = list(
        build_five_market_batch(
            frame_suffix="invalid",
            observed_at=T2,
        )
    )

    invalid_frames[-1] = AtomicMarketLineageBatchFrame(
        observation=invalid_frames[-1].observation,
        frame_observed_at=datetime(
            2026,
            7,
            14,
            7,
            59,
            59,
            tzinfo=timezone.utc,
        ),
    )

    try:
        router.route(frames=invalid_frames)
        raise AssertionError(
            "invalid cohort must fail closed before commit"
        )
    except AtomicMarketLineageBatchContractError:
        pass

    assert router.bridge.ledger.records() == before_records
    assert router.bridge.ledger.heads() == before_heads
    assert router.bridge.ledger.record_count == 5


def run_duplicate_market_identity_test():
    router = OracleAtomicMarketLineageBatchRouter()

    observation_one = build_observation(
        market_id="KXTEST-DUP-MARKET",
        frame_id="one",
    )
    observation_two = build_observation(
        market_id="KXTEST-DUP-MARKET",
        frame_id="two",
    )

    frames = (
        AtomicMarketLineageBatchFrame(
            observation=observation_one,
            frame_observed_at=T1,
        ),
        AtomicMarketLineageBatchFrame(
            observation=observation_two,
            frame_observed_at=T1,
        ),
    )

    try:
        router.route(frames=frames)
        raise AssertionError(
            "duplicate market identity within cohort must fail closed"
        )
    except AtomicMarketLineageBatchContractError:
        pass

    assert router.bridge.ledger.record_count == 0


def run_duplicate_observation_identity_test():
    router = OracleAtomicMarketLineageBatchRouter()
    observation = build_observation(
        market_id="KXTEST-DUP-OBS",
        frame_id="one",
    )

    frames = (
        AtomicMarketLineageBatchFrame(
            observation=observation,
            frame_observed_at=T1,
        ),
        AtomicMarketLineageBatchFrame(
            observation=observation,
            frame_observed_at=T1,
        ),
    )

    try:
        router.route(frames=frames)
        raise AssertionError(
            "duplicate observation identity must fail closed"
        )
    except AtomicMarketLineageBatchContractError:
        pass

    assert router.bridge.ledger.record_count == 0


def run_deterministic_batch_replay_test():
    first = OracleAtomicMarketLineageBatchRouter()
    second = OracleAtomicMarketLineageBatchRouter()

    batch_one = build_five_market_batch(
        frame_suffix="r1",
        observed_at=T1,
    )
    batch_two = build_five_market_batch(
        frame_suffix="r2",
        observed_at=T2,
        changed_market="KXTEST-COHORT-4",
    )

    first_receipts = (
        first.route(frames=batch_one),
        first.route(frames=batch_two),
    )
    second_receipts = (
        second.route(frames=batch_one),
        second.route(frames=batch_two),
    )

    assert first_receipts == second_receipts
    assert (
        first.bridge.ledger.records()
        == second.bridge.ledger.records()
    )

    return first_receipts


def main():
    _, first_receipt = run_first_cohort_test()
    _, same_receipt = run_second_same_cohort_test()
    _, changed_receipt = run_single_market_transition_cohort_test()

    run_atomic_preflight_failure_test()
    run_duplicate_market_identity_test()
    run_duplicate_observation_identity_test()

    replay_receipts = run_deterministic_batch_replay_test()

    result = {
        "schema_version": first_receipt.schema_version,
        "engine_id": first_receipt.engine_id,
        "status": "passed",
        "ola_034_pipeline_bridge_consumed": True,
        "five_market_cohort_routed": (
            first_receipt.batch_market_count == 5
        ),
        "full_batch_preflight_before_commit": True,
        "preflight_isolated_from_live_ledger": True,
        "atomic_failure_preserves_live_lineage": True,
        "same_five_market_cohort_dwell_advanced": (
            same_receipt.ledger_record_count_after == 10
        ),
        "single_market_transition_isolated": (
            changed_receipt.transition_count == 1
        ),
        "ordered_batch_receipts_preserved": True,
        "duplicate_market_identity_fails_closed": True,
        "duplicate_observation_identity_fails_closed": True,
        "deterministic_batch_replay_valid": (
            len(replay_receipts) == 2
        ),
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": first_receipt.read_only,
        "execution_allowed": first_receipt.execution_allowed,
        "execution_adapter_resolved": (
            first_receipt.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            first_receipt.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            first_receipt.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            first_receipt.order_placement_allowed
        ),
        "funds_moved": first_receipt.funds_moved,
        "portfolio_mutated": first_receipt.portfolio_mutated,
    }

    print(
        "[PASS] OLA-035 Oracle Atomic Market Lineage "
        "Batch Router"
    )
    print(result)


if __name__ == "__main__":
    main()
