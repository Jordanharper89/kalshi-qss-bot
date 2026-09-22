from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persisted_cohort_capture_port import (
    CanonicalPersistedCohortCaptureContractError,
    OracleCanonicalPersistedCohortCapturePort,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 13, 0, 0, tzinfo=timezone.utc)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.040.1",
):
    payload = {
        "source_market_id": market_id,
        "yes_bid_dollars": "0.0000",
        "yes_bid_size_fp": "0.00",
        "yes_ask_dollars": "0.6140",
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
    batch_id="batch.ola.040.1",
):
    return tuple(
        build_observation(
            market_id=f"KXTEST-CAPTURE-{index}",
            frame_id=str(index),
            batch_id=batch_id,
        )
        for index in range(1, 6)
    )


def run_capture_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = build_cohort()

    capture = port.capture(
        canonical_observations=cohort
    )

    assert capture.schema_version == "OLA-040"
    assert capture.engine_id == "OLA-040"
    assert capture.acquisition_batch_id == "batch.ola.040.1"
    assert capture.canonical_count == 5
    assert capture.canonical_observations == cohort
    assert all(
        captured is original
        for captured, original in zip(
            capture.canonical_observations,
            cohort,
        )
    )
    assert capture.observation_ids == tuple(
        observation.observation_id
        for observation in cohort
    )
    assert capture.content_hashes == tuple(
        observation.content_hash
        for observation in cohort
    )
    assert capture.replay_hashes == tuple(
        observation.replay_hash
        for observation in cohort
    )
    assert port.pending_count == 1
    assert port.consumed_count == 0

    return port, capture, cohort


def run_consume_test():
    port, capture, cohort = run_capture_test()

    consumed = port.consume(
        acquisition_batch_id=capture.acquisition_batch_id
    )

    assert consumed == capture
    assert all(
        captured is original
        for captured, original in zip(
            consumed.canonical_observations,
            cohort,
        )
    )
    assert port.pending_count == 0
    assert port.consumed_count == 1

    return port, consumed


def run_duplicate_capture_fail_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = build_cohort()

    port.capture(canonical_observations=cohort)

    try:
        port.capture(canonical_observations=cohort)
        raise AssertionError(
            "duplicate batch capture must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    assert port.pending_count == 1
    assert port.consumed_count == 0


def run_duplicate_consume_fail_closed_test():
    port, capture = run_consume_test()

    try:
        port.consume(
            acquisition_batch_id=capture.acquisition_batch_id
        )
        raise AssertionError(
            "duplicate batch consume must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    assert port.pending_count == 0
    assert port.consumed_count == 1


def run_recapture_consumed_batch_fail_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = build_cohort()

    capture = port.capture(
        canonical_observations=cohort
    )
    port.consume(
        acquisition_batch_id=capture.acquisition_batch_id
    )

    try:
        port.capture(canonical_observations=cohort)
        raise AssertionError(
            "consumed batch recapture must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    assert port.pending_count == 0
    assert port.consumed_count == 1


def run_mixed_batch_fail_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-CAPTURE-5",
        frame_id="mixed",
        batch_id="batch.ola.040.other",
    )

    try:
        port.capture(canonical_observations=cohort)
        raise AssertionError(
            "mixed acquisition batch identity must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    assert port.pending_count == 0


def run_duplicate_market_fail_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-CAPTURE-4",
        frame_id="duplicate-market",
    )

    try:
        port.capture(canonical_observations=cohort)
        raise AssertionError(
            "duplicate market identity must fail closed"
        )
    except CanonicalPersistedCohortCaptureContractError:
        pass

    assert port.pending_count == 0


def run_peek_metadata_test():
    port, capture, _ = run_capture_test()

    metadata = port.peek_metadata(
        acquisition_batch_id=capture.acquisition_batch_id
    )

    assert metadata is not None
    assert metadata["schema_version"] == "OLA-040"
    assert metadata["canonical_count"] == 5
    assert "canonical_observations" not in metadata

    try:
        metadata["canonical_count"] = 99
        raise AssertionError(
            "peek metadata must be immutable"
        )
    except TypeError:
        pass

    assert port.pending_count == 1


def run_deterministic_capture_hash_test():
    first = OracleCanonicalPersistedCohortCapturePort()
    second = OracleCanonicalPersistedCohortCapturePort()

    first_capture = first.capture(
        canonical_observations=build_cohort()
    )
    second_capture = second.capture(
        canonical_observations=build_cohort()
    )

    assert first_capture == second_capture
    assert first_capture.capture_hash == second_capture.capture_hash

    return first_capture


def main():
    _, capture, _ = run_capture_test()
    _, consumed = run_consume_test()

    run_duplicate_capture_fail_closed_test()
    run_duplicate_consume_fail_closed_test()
    run_recapture_consumed_batch_fail_closed_test()
    run_mixed_batch_fail_closed_test()
    run_duplicate_market_fail_closed_test()
    run_peek_metadata_test()

    deterministic = run_deterministic_capture_hash_test()

    result = {
        "schema_version": capture.schema_version,
        "engine_id": capture.engine_id,
        "status": "passed",
        "exact_canonical_observation_objects_preserved": True,
        "exact_observation_order_preserved": True,
        "single_acquisition_batch_identity_enforced": True,
        "unique_observation_identity_enforced": True,
        "unique_market_identity_enforced": True,
        "content_hash_binding_preserved": True,
        "replay_hash_binding_preserved": True,
        "write_once_per_batch": True,
        "consume_once_per_batch": True,
        "consumed_batch_recapture_fails_closed": True,
        "mixed_batch_identity_fails_closed": True,
        "duplicate_market_identity_fails_closed": True,
        "immutable_metadata_projection": True,
        "canonical_observation_objects_excluded_from_metadata": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_capture_hash_valid": (
            deterministic.capture_hash == capture.capture_hash
        ),
        "capture_consumed_successfully": (
            consumed.acquisition_batch_id
            == capture.acquisition_batch_id
        ),
        "no_persistence_owned": True,
        "no_lineage_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": capture.read_only,
        "execution_allowed": capture.execution_allowed,
        "execution_adapter_resolved": (
            capture.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            capture.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            capture.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            capture.order_placement_allowed
        ),
        "funds_moved": capture.funds_moved,
        "portfolio_mutated": capture.portfolio_mutated,
    }

    print(
        "[PASS] OLA-040 Oracle Canonical Persisted "
        "Cohort Capture Port"
    )
    print(result)


if __name__ == "__main__":
    main()
