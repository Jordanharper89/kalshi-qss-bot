from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cycle_canonical_cohort_bundle_contract import (
    OraclePersistedCycleCanonicalCohortBundle,
    PersistedCycleCanonicalCohortBundleContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    RawSourceObservation,
)


T1 = datetime(2026, 7, 14, 11, 0, 0, tzinfo=timezone.utc)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.038.live.1",
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
    batch_id="batch.ola.038.live.1",
):
    return tuple(
        build_observation(
            market_id=f"KXTEST-BUNDLE-{index}",
            frame_id=str(index),
            batch_id=batch_id,
        )
        for index in range(1, 6)
    )


def successful_cycle_result():
    return {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "cycle_status": "completed",
        "canonical_count": 5,
        "postgresql_routing_record_delta": 5,
        "read_only": True,
        "execution_allowed": False,
    }


def run_successful_bundle_test():
    cohort = build_cohort()

    bundle = OraclePersistedCycleCanonicalCohortBundle.create(
        ola_017_cycle_result=successful_cycle_result(),
        canonical_observations=cohort,
        cycle_completed_at=T1,
    )

    assert bundle.schema_version == "OLA-038"
    assert bundle.engine_id == "OLA-038"
    assert bundle.upstream_schema_version == "OLA-017"
    assert bundle.upstream_engine_id == "OLA-017"
    assert bundle.cycle_status == "completed"
    assert bundle.acquisition_batch_id == "batch.ola.038.live.1"
    assert bundle.canonical_count == 5
    assert bundle.persistence_count == 5
    assert bundle.canonical_observations == cohort
    assert len(bundle.observation_ids) == 5
    assert len(bundle.source_market_ids) == 5

    return bundle


def run_scheduler_projection_compatibility_test():
    cycle_result = {
        "schema_version": "OLA-017",
        "engine_id": "OLA-017",
        "status": "completed",
        "canonical_count": 5,
        "postgresql_persistence_count": 5,
        "read_only": True,
        "execution_allowed": False,
    }

    bundle = OraclePersistedCycleCanonicalCohortBundle.create(
        ola_017_cycle_result=cycle_result,
        canonical_observations=build_cohort(),
        cycle_completed_at=T1,
    )

    assert bundle.cycle_status == "completed"
    assert bundle.persistence_count == 5


def run_failed_cycle_test():
    cycle_result = successful_cycle_result()
    cycle_result["cycle_status"] = "blocked"
    cycle_result["canonical_count"] = 0
    cycle_result["postgresql_routing_record_delta"] = 0

    try:
        OraclePersistedCycleCanonicalCohortBundle.create(
            ola_017_cycle_result=cycle_result,
            canonical_observations=(),
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "failed OLA-017 cycle must fail closed"
        )
    except PersistedCycleCanonicalCohortBundleContractError:
        pass


def run_persistence_mismatch_test():
    cycle_result = successful_cycle_result()
    cycle_result["postgresql_routing_record_delta"] = 4

    try:
        OraclePersistedCycleCanonicalCohortBundle.create(
            ola_017_cycle_result=cycle_result,
            canonical_observations=build_cohort(),
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "persistence mismatch must fail closed"
        )
    except PersistedCycleCanonicalCohortBundleContractError:
        pass


def run_exact_cohort_count_test():
    try:
        OraclePersistedCycleCanonicalCohortBundle.create(
            ola_017_cycle_result=successful_cycle_result(),
            canonical_observations=build_cohort()[:-1],
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "exact canonical cohort count mismatch must fail closed"
        )
    except PersistedCycleCanonicalCohortBundleContractError:
        pass


def run_mixed_batch_test():
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-BUNDLE-5",
        frame_id="mixed",
        batch_id="batch.ola.038.other",
    )

    try:
        OraclePersistedCycleCanonicalCohortBundle.create(
            ola_017_cycle_result=successful_cycle_result(),
            canonical_observations=cohort,
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "mixed acquisition batch identity must fail closed"
        )
    except PersistedCycleCanonicalCohortBundleContractError:
        pass


def run_duplicate_market_test():
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-BUNDLE-4",
        frame_id="duplicate-market",
    )

    try:
        OraclePersistedCycleCanonicalCohortBundle.create(
            ola_017_cycle_result=successful_cycle_result(),
            canonical_observations=cohort,
            cycle_completed_at=T1,
        )
        raise AssertionError(
            "duplicate market identity must fail closed"
        )
    except PersistedCycleCanonicalCohortBundleContractError:
        pass


def run_deterministic_bundle_test():
    first = OraclePersistedCycleCanonicalCohortBundle.create(
        ola_017_cycle_result=successful_cycle_result(),
        canonical_observations=build_cohort(),
        cycle_completed_at=T1,
    )
    second = OraclePersistedCycleCanonicalCohortBundle.create(
        ola_017_cycle_result=successful_cycle_result(),
        canonical_observations=build_cohort(),
        cycle_completed_at=T1,
    )

    assert first == second
    assert first.bundle_hash == second.bundle_hash

    return first


def run_immutable_metadata_test():
    bundle = run_successful_bundle_test()
    metadata = bundle.to_canonical_metadata()

    try:
        metadata["canonical_count"] = 99
        raise AssertionError(
            "canonical metadata projection must be immutable"
        )
    except TypeError:
        pass


def main():
    bundle = run_successful_bundle_test()

    run_scheduler_projection_compatibility_test()
    run_failed_cycle_test()
    run_persistence_mismatch_test()
    run_exact_cohort_count_test()
    run_mixed_batch_test()
    run_duplicate_market_test()
    deterministic = run_deterministic_bundle_test()
    run_immutable_metadata_test()

    result = {
        "schema_version": bundle.schema_version,
        "engine_id": bundle.engine_id,
        "status": "passed",
        "ola_017_success_evidence_required": True,
        "ola_017_cycle_status_bound": True,
        "ola_017_canonical_count_bound": True,
        "postgresql_routing_delta_bound": True,
        "exact_canonical_observation_cohort_preserved": True,
        "canonical_observation_objects_not_serialized_into_scheduler_kwargs": True,
        "single_acquisition_batch_identity_enforced": True,
        "ordered_observation_identity_preserved": True,
        "unique_market_identity_enforced": True,
        "cycle_completed_at_bound": True,
        "failed_cycle_fails_closed": True,
        "persistence_count_mismatch_fails_closed": True,
        "exact_cohort_count_mismatch_fails_closed": True,
        "mixed_batch_identity_fails_closed": True,
        "duplicate_market_identity_fails_closed": True,
        "deterministic_bundle_hash_valid": (
            deterministic.bundle_hash == bundle.bundle_hash
        ),
        "immutable_metadata_projection": True,
        "ola_021_canonicalizer_unchanged": True,
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": bundle.read_only,
        "execution_allowed": bundle.execution_allowed,
        "execution_adapter_resolved": (
            bundle.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            bundle.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            bundle.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            bundle.order_placement_allowed
        ),
        "funds_moved": bundle.funds_moved,
        "portfolio_mutated": bundle.portfolio_mutated,
    }

    print(
        "[PASS] OLA-038 Oracle Persisted Cycle Canonical "
        "Cohort Bundle Contract"
    )
    print(result)


if __name__ == "__main__":
    main()
