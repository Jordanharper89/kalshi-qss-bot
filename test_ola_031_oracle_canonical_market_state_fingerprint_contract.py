from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalMarketStateFingerprint,
    MARKET_STATE_FIELDS,
    OracleCanonicalMarketStateFingerprintContract,
    RawSourceObservation,
    CanonicalObservation,
    MarketStateFingerprintContractError,
)


OBSERVED_AT = datetime(
    2026,
    7,
    14,
    4,
    13,
    47,
    67988,
    tzinfo=timezone.utc,
)

ACQUIRED_AT_ONE = datetime(
    2026,
    7,
    14,
    4,
    13,
    48,
    tzinfo=timezone.utc,
)

ACQUIRED_AT_TWO = datetime(
    2026,
    7,
    14,
    4,
    13,
    57,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    source_market_id,
    acquired_at,
    acquisition_batch_id,
    yes_ask_dollars="0.6140",
    yes_ask_size_fp="40.00",
    previous_yes_ask_dollars="0.6000",
    provenance_acquired_at="frame-one",
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
        "previous_yes_ask_dollars": (
            previous_yes_ask_dollars
        ),
        "previous_price_dollars": "0.0000",
        "volume_fp": "0.00",
        "volume_24h_fp": "0.00",
        "open_interest_fp": "0.00",
        "liquidity_dollars": "0.0000",
    }

    raw = RawSourceObservation.create(
        source_observation_id=(
            "kalshi.market."
            + source_market_id
            + "."
            + acquisition_batch_id
        ),
        observed_at=OBSERVED_AT,
        observation_type="market_snapshot",
        payload=payload,
        provenance={
            "source_id": "source.kalshi.market_data",
            "adapter_id": (
                "adapter.oracle.kalshi.public_markets.shadow"
            ),
            "acquired_at": provenance_acquired_at,
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=acquired_at,
        acquisition_batch_id=acquisition_batch_id,
    )


def run_same_state_different_frame_test():
    contract = OracleCanonicalMarketStateFingerprintContract()

    first_observation = build_observation(
        source_market_id="KXTEST-MARKET-1",
        acquired_at=ACQUIRED_AT_ONE,
        acquisition_batch_id="batch.ola.031.001",
        previous_yes_ask_dollars="0.6000",
        provenance_acquired_at="frame-one",
    )

    second_observation = build_observation(
        source_market_id="KXTEST-MARKET-1",
        acquired_at=ACQUIRED_AT_TWO,
        acquisition_batch_id="batch.ola.031.002",
        previous_yes_ask_dollars="0.6100",
        provenance_acquired_at="frame-two",
    )

    first = contract.fingerprint(
        observation=first_observation
    )

    second = contract.fingerprint(
        observation=second_observation
    )

    assert first_observation.observation_id != (
        second_observation.observation_id
    )

    assert first_observation.content_hash != (
        second_observation.content_hash
    )

    assert first.market_state_hash == second.market_state_hash
    assert first.fingerprint_id == second.fingerprint_id
    assert first.same_market_state_as(second) is True

    return first, second


def run_actual_market_change_test():
    contract = OracleCanonicalMarketStateFingerprintContract()

    before = contract.fingerprint(
        observation=build_observation(
            source_market_id="KXTEST-MARKET-1",
            acquired_at=ACQUIRED_AT_ONE,
            acquisition_batch_id="batch.ola.031.003",
            yes_ask_dollars="0.6140",
            yes_ask_size_fp="40.00",
        )
    )

    after = contract.fingerprint(
        observation=build_observation(
            source_market_id="KXTEST-MARKET-1",
            acquired_at=ACQUIRED_AT_TWO,
            acquisition_batch_id="batch.ola.031.004",
            yes_ask_dollars="0.9950",
            yes_ask_size_fp="27.00",
        )
    )

    assert before.market_state_hash != after.market_state_hash
    assert before.fingerprint_id != after.fingerprint_id
    assert before.same_market_state_as(after) is False

    return before, after


def run_market_identity_binding_test():
    contract = OracleCanonicalMarketStateFingerprintContract()

    first = contract.fingerprint(
        observation=build_observation(
            source_market_id="KXTEST-MARKET-1",
            acquired_at=ACQUIRED_AT_ONE,
            acquisition_batch_id="batch.ola.031.005",
        )
    )

    second = contract.fingerprint(
        observation=build_observation(
            source_market_id="KXTEST-MARKET-2",
            acquired_at=ACQUIRED_AT_ONE,
            acquisition_batch_id="batch.ola.031.006",
        )
    )

    assert first.market_state_hash == second.market_state_hash
    assert first.fingerprint_id != second.fingerprint_id
    assert first.same_market_state_as(second) is False


def run_exact_fixed_point_preservation_test():
    contract = OracleCanonicalMarketStateFingerprintContract()

    fingerprint = contract.fingerprint(
        observation=build_observation(
            source_market_id="KXTEST-MARKET-1",
            acquired_at=ACQUIRED_AT_ONE,
            acquisition_batch_id="batch.ola.031.007",
            yes_ask_dollars="0.6140",
            yes_ask_size_fp="40.00",
        )
    )

    state = fingerprint.market_state_dict()

    assert state["yes_ask_dollars"] == "0.6140"
    assert state["yes_ask_size_fp"] == "40.00"
    assert isinstance(state["yes_ask_dollars"], str)
    assert isinstance(state["yes_ask_size_fp"], str)


def run_projection_boundary_test():
    first, second = run_same_state_different_frame_test()

    state = first.market_state_dict()

    assert tuple(sorted(state.keys())) == tuple(
        sorted(MARKET_STATE_FIELDS)
    )

    for excluded_field in (
        "observation_id",
        "source_observation_id",
        "observed_at",
        "acquired_at",
        "acquisition_batch_id",
        "content_hash",
        "replay_hash",
        "provenance",
        "previous_yes_bid_dollars",
        "previous_yes_ask_dollars",
        "previous_price_dollars",
    ):
        assert excluded_field not in state

    assert first.acquisition_envelope_excluded is True
    assert first.source_history_excluded is True
    assert second.acquisition_envelope_excluded is True
    assert second.source_history_excluded is True


def run_missing_state_field_fail_closed_test():
    raw = RawSourceObservation.create(
        source_observation_id="missing.state.field",
        observed_at=OBSERVED_AT,
        observation_type="market_snapshot",
        payload={
            "source_market_id": "KXTEST-MISSING",
            "yes_bid_dollars": "0.1000",
        },
        provenance={
            "source_id": "source.kalshi.market_data",
        },
    )

    observation = CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT_ONE,
        acquisition_batch_id="batch.ola.031.missing",
    )

    try:
        CanonicalMarketStateFingerprint.create(
            observation=observation
        )

        raise AssertionError(
            "missing market state fields must fail closed"
        )

    except MarketStateFingerprintContractError:
        pass


def run_wrong_observation_type_fail_closed_test():
    raw = RawSourceObservation.create(
        source_observation_id="wrong.type",
        observed_at=OBSERVED_AT,
        observation_type="trade_print",
        payload={
            "source_market_id": "KXTEST-WRONG-TYPE",
        },
        provenance={
            "source_id": "source.kalshi.market_data",
        },
    )

    observation = CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT_ONE,
        acquisition_batch_id="batch.ola.031.wrong-type",
    )

    try:
        CanonicalMarketStateFingerprint.create(
            observation=observation
        )

        raise AssertionError(
            "non-market-snapshot observation must fail closed"
        )

    except MarketStateFingerprintContractError:
        pass


def run_deterministic_replay_test():
    contract = OracleCanonicalMarketStateFingerprintContract()

    observation = build_observation(
        source_market_id="KXTEST-DETERMINISTIC",
        acquired_at=ACQUIRED_AT_ONE,
        acquisition_batch_id="batch.ola.031.deterministic",
    )

    first = contract.fingerprint(
        observation=observation
    )

    second = contract.fingerprint(
        observation=observation
    )

    assert first == second
    assert first.fingerprint_hash == second.fingerprint_hash


def main():
    same_state_first, same_state_second = (
        run_same_state_different_frame_test()
    )

    changed_before, changed_after = (
        run_actual_market_change_test()
    )

    run_market_identity_binding_test()
    run_exact_fixed_point_preservation_test()
    run_projection_boundary_test()
    run_missing_state_field_fail_closed_test()
    run_wrong_observation_type_fail_closed_test()
    run_deterministic_replay_test()

    result = {
        "schema_version": same_state_first.schema_version,
        "engine_id": same_state_first.engine_id,
        "status": "passed",
        "market_state_field_count": (
            same_state_first.state_field_count
        ),
        "exact_live_market_state_identity": True,
        "oi_046_market_dna_reused": False,
        "acquisition_envelope_excluded": (
            same_state_first.acquisition_envelope_excluded
        ),
        "source_history_fields_excluded": (
            same_state_first.source_history_excluded
        ),
        "same_state_different_frame_hash_equal": (
            same_state_first.market_state_hash
            == same_state_second.market_state_hash
        ),
        "same_state_different_frame_fingerprint_equal": (
            same_state_first.fingerprint_id
            == same_state_second.fingerprint_id
        ),
        "actual_market_change_hash_changed": (
            changed_before.market_state_hash
            != changed_after.market_state_hash
        ),
        "actual_market_change_fingerprint_changed": (
            changed_before.fingerprint_id
            != changed_after.fingerprint_id
        ),
        "market_identity_bound_to_fingerprint": True,
        "exact_fixed_point_strings_preserved": (
            same_state_first.exact_fixed_point_strings_preserved
        ),
        "missing_state_field_fails_closed": True,
        "wrong_observation_type_fails_closed": True,
        "deterministic_replay_valid": True,
        "dwell_change_lineage_foundation_ready": True,
        "read_only": same_state_first.read_only,
        "execution_allowed": same_state_first.execution_allowed,
        "execution_adapter_resolved": (
            same_state_first.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            same_state_first.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            same_state_first.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            same_state_first.order_placement_allowed
        ),
        "funds_moved": same_state_first.funds_moved,
        "portfolio_mutated": same_state_first.portfolio_mutated,
    }

    print(
        "[PASS] OLA-031 Oracle Canonical Market State "
        "Fingerprint Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
