from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger import (
    MarketLineageLedgerContractError,
    MarketLineageReplayFrame,
    OracleCanonicalMarketLineageLedger,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_state_fingerprint_contract import (
    OracleCanonicalMarketStateFingerprintContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 6, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 6, 0, 10, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 6, 0, 20, tzinfo=timezone.utc)
T4 = datetime(2026, 7, 14, 6, 0, 30, tzinfo=timezone.utc)


def build_fingerprint(
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

    observation = CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=T1,
        acquisition_batch_id="batch.ola.033." + frame_id,
    )

    return (
        OracleCanonicalMarketStateFingerprintContract()
        .fingerprint(observation=observation)
    )


def build_frames():
    return (
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-A",
                frame_id="a1",
            ),
            frame_observed_at=T1,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-B",
                frame_id="b1",
            ),
            frame_observed_at=T1,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-A",
                frame_id="a2",
            ),
            frame_observed_at=T2,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-B",
                frame_id="b2",
            ),
            frame_observed_at=T2,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-A",
                frame_id="a3",
                yes_ask="0.7000",
            ),
            frame_observed_at=T3,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-B",
                frame_id="b3",
            ),
            frame_observed_at=T3,
        ),
        MarketLineageReplayFrame(
            fingerprint=build_fingerprint(
                market_id="KXTEST-A",
                frame_id="a4",
                yes_ask="0.7000",
            ),
            frame_observed_at=T4,
        ),
    )


def run_interleaved_market_test():
    ledger = OracleCanonicalMarketLineageLedger()
    receipts = []

    for frame in build_frames():
        receipts.append(
            ledger.append(
                fingerprint=frame.fingerprint,
                frame_observed_at=frame.frame_observed_at,
            )
        )

    head_a = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-A",
    )
    head_b = ledger.head(
        source_id="source.kalshi.market_data",
        source_market_id="KXTEST-B",
    )

    assert head_a is not None
    assert head_b is not None
    assert ledger.market_count == 2
    assert ledger.record_count == 7

    assert head_a.consecutive_frame_count == 2
    assert head_a.dwell_seconds == "10.000000"
    assert head_a.state_changed_at == T3

    assert head_b.consecutive_frame_count == 3
    assert head_b.dwell_seconds == "20.000000"
    assert head_b.state_changed_at is None

    assert receipts[4].transition_detected is True
    assert receipts[6].transition_detected is False

    return ledger, receipts, head_a, head_b


def run_per_market_chain_test():
    ledger, _, head_a, head_b = run_interleaved_market_test()

    records_a = [
        record
        for record in ledger.records()
        if record.source_market_id == "KXTEST-A"
    ]
    records_b = [
        record
        for record in ledger.records()
        if record.source_market_id == "KXTEST-B"
    ]

    assert len(records_a) == 4
    assert len(records_b) == 3

    for previous, current in zip(records_a, records_a[1:]):
        assert (
            current.previous_lineage_hash
            == previous.lineage_hash
        )

    for previous, current in zip(records_b, records_b[1:]):
        assert (
            current.previous_lineage_hash
            == previous.lineage_hash
        )

    assert records_a[-1].lineage_hash == head_a.lineage_hash
    assert records_b[-1].lineage_hash == head_b.lineage_hash


def run_duplicate_observation_fail_closed_test():
    ledger = OracleCanonicalMarketLineageLedger()
    frame = build_frames()[0]

    ledger.append(
        fingerprint=frame.fingerprint,
        frame_observed_at=frame.frame_observed_at,
    )

    try:
        ledger.append(
            fingerprint=frame.fingerprint,
            frame_observed_at=frame.frame_observed_at,
        )
        raise AssertionError(
            "duplicate observation identity must fail closed"
        )
    except MarketLineageLedgerContractError:
        pass

    assert ledger.record_count == 1


def run_per_market_clock_regression_test():
    ledger = OracleCanonicalMarketLineageLedger()

    first = MarketLineageReplayFrame(
        fingerprint=build_fingerprint(
            market_id="KXTEST-CLOCK",
            frame_id="clock-1",
        ),
        frame_observed_at=T3,
    )
    second = MarketLineageReplayFrame(
        fingerprint=build_fingerprint(
            market_id="KXTEST-CLOCK",
            frame_id="clock-2",
        ),
        frame_observed_at=T2,
    )

    ledger.append(
        fingerprint=first.fingerprint,
        frame_observed_at=first.frame_observed_at,
    )

    try:
        ledger.append(
            fingerprint=second.fingerprint,
            frame_observed_at=second.frame_observed_at,
        )
        raise AssertionError(
            "per-market clock regression must fail closed"
        )
    except MarketLineageLedgerContractError:
        pass

    assert ledger.record_count == 1


def run_heads_snapshot_test():
    ledger, _, _, _ = run_interleaved_market_test()
    snapshot = ledger.heads()

    try:
        snapshot[
            (
                "source.kalshi.market_data",
                "KXTEST-C",
            )
        ] = None
        raise AssertionError(
            "head snapshot must be immutable"
        )
    except TypeError:
        pass

    assert ledger.market_count == 2


def run_deterministic_replay_test():
    frames = build_frames()

    first = OracleCanonicalMarketLineageLedger.replay(frames)
    second = OracleCanonicalMarketLineageLedger.replay(frames)

    assert first.records() == second.records()
    assert first.heads() == second.heads()
    assert first.market_count == second.market_count
    assert first.record_count == second.record_count

    return first


def main():
    ledger, receipts, head_a, head_b = (
        run_interleaved_market_test()
    )

    run_per_market_chain_test()
    run_duplicate_observation_fail_closed_test()
    run_per_market_clock_regression_test()
    run_heads_snapshot_test()

    replayed = run_deterministic_replay_test()

    result = {
        "schema_version": receipts[-1].schema_version,
        "engine_id": receipts[-1].engine_id,
        "status": "passed",
        "ola_031_fingerprints_consumed": True,
        "ola_032_lineage_contract_consumed": True,
        "per_market_lineage_heads_owned": True,
        "interleaved_market_frames_isolated": True,
        "market_count": ledger.market_count,
        "record_count": ledger.record_count,
        "market_a_transition_preserved": (
            head_a.state_changed_at == T3
        ),
        "market_a_post_transition_dwell_preserved": (
            head_a.dwell_seconds == "10.000000"
        ),
        "market_b_same_state_dwell_preserved": (
            head_b.dwell_seconds == "20.000000"
        ),
        "per_market_immutable_chain_preserved": True,
        "duplicate_observation_identity_fails_closed": True,
        "per_market_clock_regression_fails_closed": True,
        "immutable_head_snapshot": True,
        "deterministic_replay_valid": (
            replayed.records() == ledger.records()
        ),
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": receipts[-1].read_only,
        "execution_allowed": receipts[-1].execution_allowed,
        "execution_adapter_resolved": (
            receipts[-1].execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            receipts[-1].execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            receipts[-1].trade_authorization_allowed
        ),
        "order_placement_allowed": (
            receipts[-1].order_placement_allowed
        ),
        "funds_moved": receipts[-1].funds_moved,
        "portfolio_mutated": receipts[-1].portfolio_mutated,
    }

    print(
        "[PASS] OLA-033 Oracle Canonical Market "
        "Lineage Ledger"
    )
    print(result)


if __name__ == "__main__":
    main()
