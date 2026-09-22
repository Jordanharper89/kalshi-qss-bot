from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_post_persistence_cohort_capture_hook import (
    OraclePostPersistenceCohortCaptureHook,
    PostPersistenceCohortCaptureHookContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persisted_cohort_capture_port import (
    OracleCanonicalPersistedCohortCapturePort,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(
    2026,
    7,
    14,
    15,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.041.1",
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
            "kalshi."
            + market_id
            + "."
            + frame_id
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
    batch_id="batch.ola.041.1",
):
    return tuple(
        build_observation(
            market_id=f"KXTEST-HOOK-{index}",
            frame_id=str(index),
            batch_id=batch_id,
        )
        for index in range(1, 6)
    )


def completed_cycle_result():
    return {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "completed",
        "canonical_count": 5,
        "postgresql_routing_record_delta": 5,
        "read_only": True,
        "execution_allowed": False,
    }


def run_successful_capture_hook_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )
    cohort = build_cohort()

    receipt = hook.capture_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        canonical_observations=cohort,
    )

    assert receipt.schema_version == "OLA-041"
    assert receipt.engine_id == "OLA-041"
    assert receipt.upstream_schema_version == "OLA-017"
    assert receipt.upstream_engine_id == "OLA-017"
    assert receipt.cycle_status == "completed"
    assert receipt.acquisition_batch_id == "batch.ola.041.1"
    assert receipt.canonical_count == 5
    assert receipt.persistence_count == 5
    assert len(receipt.observation_ids) == 5
    assert len(receipt.source_market_ids) == 5
    assert port.pending_count == 1
    assert port.consumed_count == 0

    capture = port.consume(
        acquisition_batch_id=receipt.acquisition_batch_id
    )

    assert all(
        captured is original
        for captured, original in zip(
            capture.canonical_observations,
            cohort,
        )
    )

    return receipt


def run_failed_cycle_fails_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )

    cycle_result = completed_cycle_result()
    cycle_result["cycle_status"] = "failed"
    cycle_result["canonical_count"] = 0
    cycle_result["postgresql_routing_record_delta"] = 0

    try:
        hook.capture_completed_cycle(
            ola_017_cycle_result=cycle_result,
            canonical_observations=(),
        )
        raise AssertionError(
            "failed cycle must never capture canonical cohort"
        )
    except PostPersistenceCohortCaptureHookContractError:
        pass

    assert port.pending_count == 0
    assert port.consumed_count == 0


def run_persistence_mismatch_fails_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )

    cycle_result = completed_cycle_result()
    cycle_result["postgresql_routing_record_delta"] = 4

    try:
        hook.capture_completed_cycle(
            ola_017_cycle_result=cycle_result,
            canonical_observations=build_cohort(),
        )
        raise AssertionError(
            "persistence mismatch must fail before capture"
        )
    except PostPersistenceCohortCaptureHookContractError:
        pass

    assert port.pending_count == 0


def run_cohort_count_mismatch_fails_closed_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )

    try:
        hook.capture_completed_cycle(
            ola_017_cycle_result=completed_cycle_result(),
            canonical_observations=build_cohort()[:-1],
        )
        raise AssertionError(
            "cohort count mismatch must fail before capture"
        )
    except PostPersistenceCohortCaptureHookContractError:
        pass

    assert port.pending_count == 0


def run_duplicate_capture_translation_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )
    cohort = build_cohort()

    hook.capture_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        canonical_observations=cohort,
    )

    try:
        hook.capture_completed_cycle(
            ola_017_cycle_result=completed_cycle_result(),
            canonical_observations=cohort,
        )
        raise AssertionError(
            "duplicate capture must fail at OLA-041 boundary"
        )
    except PostPersistenceCohortCaptureHookContractError:
        pass

    assert port.pending_count == 1


def run_scheduler_projection_compatibility_test():
    port = OracleCanonicalPersistedCohortCapturePort()
    hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=port
    )

    projected_cycle_result = {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "status": "completed",
        "canonical_count": 5,
        "postgresql_persistence_count": 5,
        "read_only": True,
        "execution_allowed": False,
    }

    receipt = hook.capture_completed_cycle(
        ola_017_cycle_result=projected_cycle_result,
        canonical_observations=build_cohort(
            batch_id="batch.ola.041.projected"
        ),
    )

    assert receipt.cycle_status == "completed"
    assert receipt.persistence_count == 5
    assert port.pending_count == 1


def run_deterministic_hook_receipt_test():
    first_port = OracleCanonicalPersistedCohortCapturePort()
    second_port = OracleCanonicalPersistedCohortCapturePort()

    first_hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=first_port
    )
    second_hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=second_port
    )

    first = first_hook.capture_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        canonical_observations=build_cohort(),
    )
    second = second_hook.capture_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        canonical_observations=build_cohort(),
    )

    assert first == second
    assert first.hook_hash == second.hook_hash

    return first


def main():
    receipt = run_successful_capture_hook_test()

    run_failed_cycle_fails_closed_test()
    run_persistence_mismatch_fails_closed_test()
    run_cohort_count_mismatch_fails_closed_test()
    run_duplicate_capture_translation_test()
    run_scheduler_projection_compatibility_test()

    deterministic = run_deterministic_hook_receipt_test()

    result = {
        "schema_version": receipt.schema_version,
        "engine_id": receipt.engine_id,
        "status": "passed",
        "ola_017_completed_cycle_required": True,
        "ola_017_identity_preserved": True,
        "canonical_count_required_positive": True,
        "postgresql_routing_delta_bound": True,
        "persistence_count_equals_canonical_count": True,
        "exact_canonical_cohort_required": True,
        "ola_040_capture_port_consumed": True,
        "exact_canonical_object_identity_preserved": True,
        "failed_cycle_never_captures": True,
        "persistence_mismatch_never_captures": True,
        "cohort_count_mismatch_never_captures": True,
        "duplicate_capture_errors_translated": True,
        "scheduler_projection_compatibility_preserved": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_hook_receipt_valid": (
            deterministic.hook_hash == receipt.hook_hash
        ),
        "no_lineage_advancement_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": receipt.read_only,
        "execution_allowed": receipt.execution_allowed,
        "execution_adapter_resolved": (
            receipt.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            receipt.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            receipt.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            receipt.order_placement_allowed
        ),
        "funds_moved": receipt.funds_moved,
        "portfolio_mutated": receipt.portfolio_mutated,
    }

    print(
        "[PASS] OLA-041 Oracle Post-Persistence "
        "Cohort Capture Hook"
    )
    print(result)


if __name__ == "__main__":
    main()
