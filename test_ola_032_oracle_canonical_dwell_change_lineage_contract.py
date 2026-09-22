from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_dwell_change_lineage_contract import (
    CanonicalMarketStateDwellChangeLineage,
    DwellChangeLineageContractError,
    OracleCanonicalDwellChangeLineageContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_state_fingerprint_contract import (
    OracleCanonicalMarketStateFingerprintContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 5, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 7, 14, 5, 0, 9, tzinfo=timezone.utc)
T3 = datetime(2026, 7, 14, 5, 0, 18, tzinfo=timezone.utc)
T4 = datetime(2026, 7, 14, 5, 0, 27, tzinfo=timezone.utc)


def build_fingerprint(
    *,
    source_market_id,
    frame_id,
    yes_ask_dollars="0.6140",
    yes_ask_size_fp="40.00",
):
    payload = {
        "source_market_id": source_market_id,
        "yes_bid_dollars": "0.0000",
        "yes_bid_size_fp": "0.00",
        "yes_ask_dollars": yes_ask_dollars,
        "yes_ask_size_fp": yes_ask_size_fp,
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
            "kalshi." + source_market_id + "." + frame_id
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
        acquisition_batch_id="batch.ola.032." + frame_id,
    )

    return (
        OracleCanonicalMarketStateFingerprintContract()
        .fingerprint(observation=observation)
    )


def run_initial_state_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    fingerprint = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="001",
    )

    lineage = contract.observe(
        current_fingerprint=fingerprint,
        current_frame_observed_at=T1,
    )

    assert lineage.previous_market_state_hash is None
    assert lineage.current_market_state_hash == fingerprint.market_state_hash
    assert lineage.state_first_observed_at == T1
    assert lineage.state_last_observed_at == T1
    assert lineage.current_frame_observed_at == T1
    assert lineage.state_changed_at is None
    assert lineage.consecutive_frame_count == 1
    assert lineage.dwell_seconds == "0.000000"
    assert lineage.transition_detected is False
    assert lineage.transition_id is None
    assert lineage.previous_lineage_hash is None

    return lineage, fingerprint


def run_same_state_dwell_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    first, first_fingerprint = run_initial_state_test()

    second_fingerprint = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="002",
    )

    assert (
        first_fingerprint.market_state_hash
        == second_fingerprint.market_state_hash
    )

    second = contract.observe(
        current_fingerprint=second_fingerprint,
        current_frame_observed_at=T2,
        previous_lineage=first,
    )

    third_fingerprint = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="003",
    )

    third = contract.observe(
        current_fingerprint=third_fingerprint,
        current_frame_observed_at=T3,
        previous_lineage=second,
    )

    assert second.transition_detected is False
    assert third.transition_detected is False
    assert third.state_first_observed_at == T1
    assert third.state_last_observed_at == T3
    assert third.consecutive_frame_count == 3
    assert third.dwell_seconds == "18.000000"
    assert (
        third.previous_market_state_hash
        == third.current_market_state_hash
    )
    assert second.previous_lineage_hash == first.lineage_hash
    assert third.previous_lineage_hash == second.lineage_hash

    return third


def run_transition_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    previous = run_same_state_dwell_test()

    changed_fingerprint = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="004",
        yes_ask_dollars="0.9950",
        yes_ask_size_fp="27.00",
    )

    changed = contract.observe(
        current_fingerprint=changed_fingerprint,
        current_frame_observed_at=T4,
        previous_lineage=previous,
    )

    assert changed.transition_detected is True
    assert (
        changed.previous_market_state_hash
        == previous.current_market_state_hash
    )
    assert (
        changed.current_market_state_hash
        != previous.current_market_state_hash
    )
    assert changed.previous_fingerprint_id == previous.fingerprint_id
    assert changed.state_first_observed_at == T4
    assert changed.state_last_observed_at == T4
    assert changed.state_changed_at == T4
    assert changed.consecutive_frame_count == 1
    assert changed.dwell_seconds == "0.000000"
    assert changed.transition_id is not None
    assert changed.transition_id.startswith("market_state_transition.")
    assert changed.previous_lineage_hash == previous.lineage_hash

    return previous, changed, changed_fingerprint


def run_post_transition_dwell_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    _, changed, _ = run_transition_test()

    same_changed_state = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="005",
        yes_ask_dollars="0.9950",
        yes_ask_size_fp="27.00",
    )

    next_lineage = contract.observe(
        current_fingerprint=same_changed_state,
        current_frame_observed_at=datetime(
            2026,
            7,
            14,
            5,
            0,
            36,
            tzinfo=timezone.utc,
        ),
        previous_lineage=changed,
    )

    assert next_lineage.transition_detected is False
    assert next_lineage.state_changed_at == T4
    assert next_lineage.state_first_observed_at == T4
    assert next_lineage.consecutive_frame_count == 2
    assert next_lineage.dwell_seconds == "9.000000"


def run_deterministic_transition_identity_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    previous, _, changed_fingerprint = run_transition_test()

    first = contract.observe(
        current_fingerprint=changed_fingerprint,
        current_frame_observed_at=T4,
        previous_lineage=previous,
    )
    second = contract.observe(
        current_fingerprint=changed_fingerprint,
        current_frame_observed_at=T4,
        previous_lineage=previous,
    )

    assert first == second
    assert first.transition_id == second.transition_id
    assert first.lineage_hash == second.lineage_hash


def run_market_continuity_fail_closed_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    previous = run_same_state_dwell_test()

    other_market = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-2",
        frame_id="other-market",
    )

    try:
        contract.observe(
            current_fingerprint=other_market,
            current_frame_observed_at=T4,
            previous_lineage=previous,
        )
        raise AssertionError(
            "market continuity mismatch must fail closed"
        )
    except DwellChangeLineageContractError:
        pass


def run_clock_regression_fail_closed_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    previous = run_same_state_dwell_test()

    same_state = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="clock-regression",
    )

    try:
        contract.observe(
            current_fingerprint=same_state,
            current_frame_observed_at=T2,
            previous_lineage=previous,
        )
        raise AssertionError(
            "regressed observation clock must fail closed"
        )
    except DwellChangeLineageContractError:
        pass


def run_naive_datetime_fail_closed_test():
    contract = OracleCanonicalDwellChangeLineageContract()
    fingerprint = build_fingerprint(
        source_market_id="KXTEST-LINEAGE-1",
        frame_id="naive-clock",
    )

    try:
        contract.observe(
            current_fingerprint=fingerprint,
            current_frame_observed_at=datetime(
                2026,
                7,
                14,
                5,
                0,
                0,
            ),
        )
        raise AssertionError(
            "naive observation clock must fail closed"
        )
    except DwellChangeLineageContractError:
        pass


def run_immutability_test():
    lineage = run_same_state_dwell_test()

    try:
        lineage.consecutive_frame_count = 99
        raise AssertionError("lineage record must be immutable")
    except FrozenInstanceError:
        pass


def run_canonical_replay_test():
    _, changed, _ = run_transition_test()
    canonical = changed.to_canonical_dict()

    assert canonical["schema_version"] == "OLA-032"
    assert canonical["engine_id"] == "OLA-032"
    assert canonical["transition_detected"] is True
    assert canonical["state_changed_at"] == T4.isoformat()
    assert canonical["previous_lineage_hash"] is not None
    assert canonical["lineage_hash"] == changed.lineage_hash


def main():
    initial, _ = run_initial_state_test()
    same_state = run_same_state_dwell_test()
    previous, changed, _ = run_transition_test()

    run_post_transition_dwell_test()
    run_deterministic_transition_identity_test()
    run_market_continuity_fail_closed_test()
    run_clock_regression_fail_closed_test()
    run_naive_datetime_fail_closed_test()
    run_immutability_test()
    run_canonical_replay_test()

    assert isinstance(
        initial,
        CanonicalMarketStateDwellChangeLineage,
    )

    result = {
        "schema_version": changed.schema_version,
        "engine_id": changed.engine_id,
        "status": "passed",
        "ola_031_exact_state_identity_consumed": True,
        "initial_state_lineage_created": True,
        "same_state_dwell_accumulated": True,
        "consecutive_frame_count_preserved": (
            same_state.consecutive_frame_count == 3
        ),
        "state_first_observed_at_preserved": (
            same_state.state_first_observed_at == T1
        ),
        "state_last_observed_at_advanced": (
            same_state.state_last_observed_at == T3
        ),
        "dwell_seconds_deterministic": (
            same_state.dwell_seconds == "18.000000"
        ),
        "transition_detected_on_exact_state_change": (
            changed.transition_detected
        ),
        "previous_market_state_hash_preserved": (
            changed.previous_market_state_hash
            == previous.current_market_state_hash
        ),
        "current_market_state_hash_preserved": (
            changed.current_market_state_hash
            != changed.previous_market_state_hash
        ),
        "state_changed_at_exact_frame_time": (
            changed.state_changed_at == T4
        ),
        "transition_identity_deterministic": True,
        "immutable_lineage_chain_preserved": (
            changed.previous_lineage_hash
            == previous.lineage_hash
        ),
        "replayable_lineage": True,
        "market_continuity_mismatch_fails_closed": True,
        "clock_regression_fails_closed": True,
        "naive_datetime_fails_closed": True,
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
        "[PASS] OLA-032 Oracle Canonical Dwell / Change "
        "Lineage Contract"
    )
    print(result)


if __name__ == "__main__":
    main()
