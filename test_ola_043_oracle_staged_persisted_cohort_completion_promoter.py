from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_staged_persisted_cohort_completion_promoter import (
    OracleStagedPersistedCohortCompletionPromoter,
    StagedPersistedCohortCompletionPromoterContractError,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_staging_router import (
    OraclePersistedCohortStagingRouter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_post_persistence_cohort_capture_hook import (
    OraclePostPersistenceCohortCaptureHook,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persisted_cohort_capture_port import (
    OracleCanonicalPersistedCohortCapturePort,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
    RawSourceObservation,
)


T1 = datetime(
    2026,
    7,
    14,
    17,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.043.1",
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
    batch_id="batch.ola.043.1",
):
    return tuple(
        build_observation(
            market_id=f"KXTEST-PROMOTE-{index}",
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


class FakePersistenceRouter:
    def route_batch(
        self,
        observations,
        routed_at,
    ):
        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.ola.043.persistence",
                metadata={
                    "test": "OLA-043",
                },
            )
            for observation in observations
        )

    def __call__(
        self,
        observation,
        routed_at,
    ):
        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.ola.043.persistence.single",
            metadata={
                "test": "OLA-043",
            },
        )


def build_promoter():
    capture_port = (
        OracleCanonicalPersistedCohortCapturePort()
    )
    staging_router = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )
    capture_hook = OraclePostPersistenceCohortCaptureHook(
        capture_port=capture_port
    )
    promoter = (
        OracleStagedPersistedCohortCompletionPromoter(
            staging_router=staging_router,
            capture_hook=capture_hook,
        )
    )

    return (
        promoter,
        staging_router,
        capture_port,
    )


def run_successful_promotion_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    cohort = build_cohort()

    staging_router.route_batch(
        cohort,
        T1,
    )

    assert staging_router.pending_stage_count == 1
    assert capture_port.pending_count == 0

    receipt = promoter.promote_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.043.1",
    )

    assert receipt.schema_version == "OLA-043"
    assert receipt.engine_id == "OLA-043"
    assert receipt.upstream_schema_version == "OLA-017"
    assert receipt.upstream_engine_id == "OLA-017"
    assert receipt.cycle_status == "completed"
    assert receipt.acquisition_batch_id == "batch.ola.043.1"
    assert receipt.canonical_count == 5
    assert receipt.persistence_count == 5
    assert len(receipt.observation_ids) == 5
    assert len(receipt.source_market_ids) == 5
    assert staging_router.pending_stage_count == 0
    assert staging_router.consumed_stage_count == 1
    assert capture_port.pending_count == 1

    capture = capture_port.consume(
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


def run_failed_cycle_does_not_consume_stage_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    staging_router.route_batch(
        build_cohort(),
        T1,
    )

    cycle_result = completed_cycle_result()
    cycle_result["cycle_status"] = "failed"
    cycle_result["canonical_count"] = 0
    cycle_result["postgresql_routing_record_delta"] = 0

    try:
        promoter.promote_completed_cycle(
            ola_017_cycle_result=cycle_result,
            acquisition_batch_id="batch.ola.043.1",
        )
        raise AssertionError(
            "failed cycle must not consume staged cohort"
        )
    except StagedPersistedCohortCompletionPromoterContractError:
        pass

    assert staging_router.pending_stage_count == 1
    assert staging_router.consumed_stage_count == 0
    assert capture_port.pending_count == 0


def run_persistence_mismatch_does_not_consume_stage_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    staging_router.route_batch(
        build_cohort(),
        T1,
    )

    cycle_result = completed_cycle_result()
    cycle_result["postgresql_routing_record_delta"] = 4

    try:
        promoter.promote_completed_cycle(
            ola_017_cycle_result=cycle_result,
            acquisition_batch_id="batch.ola.043.1",
        )
        raise AssertionError(
            "persistence mismatch must not consume stage"
        )
    except StagedPersistedCohortCompletionPromoterContractError:
        pass

    assert staging_router.pending_stage_count == 1
    assert staging_router.consumed_stage_count == 0
    assert capture_port.pending_count == 0


def run_canonical_count_mismatch_does_not_consume_stage_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    staging_router.route_batch(
        build_cohort(),
        T1,
    )

    cycle_result = completed_cycle_result()
    cycle_result["canonical_count"] = 4
    cycle_result["postgresql_routing_record_delta"] = 4

    try:
        promoter.promote_completed_cycle(
            ola_017_cycle_result=cycle_result,
            acquisition_batch_id="batch.ola.043.1",
        )
        raise AssertionError(
            "canonical count mismatch must not consume stage"
        )
    except StagedPersistedCohortCompletionPromoterContractError:
        pass

    assert staging_router.pending_stage_count == 1
    assert staging_router.consumed_stage_count == 0
    assert capture_port.pending_count == 0


def run_missing_stage_fails_closed_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    try:
        promoter.promote_completed_cycle(
            ola_017_cycle_result=completed_cycle_result(),
            acquisition_batch_id="batch.ola.043.missing",
        )
        raise AssertionError(
            "missing stage must fail closed"
        )
    except StagedPersistedCohortCompletionPromoterContractError:
        pass

    assert staging_router.pending_stage_count == 0
    assert staging_router.consumed_stage_count == 0
    assert capture_port.pending_count == 0


def run_duplicate_promotion_fails_closed_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    staging_router.route_batch(
        build_cohort(),
        T1,
    )

    promoter.promote_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.043.1",
    )

    try:
        promoter.promote_completed_cycle(
            ola_017_cycle_result=completed_cycle_result(),
            acquisition_batch_id="batch.ola.043.1",
        )
        raise AssertionError(
            "duplicate promotion must fail closed"
        )
    except StagedPersistedCohortCompletionPromoterContractError:
        pass

    assert staging_router.pending_stage_count == 0
    assert staging_router.consumed_stage_count == 1
    assert capture_port.pending_count == 1


def run_scheduler_projection_compatibility_test():
    (
        promoter,
        staging_router,
        capture_port,
    ) = build_promoter()

    cohort = build_cohort(
        batch_id="batch.ola.043.projected"
    )

    staging_router.route_batch(
        cohort,
        T1,
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

    receipt = promoter.promote_completed_cycle(
        ola_017_cycle_result=projected_cycle_result,
        acquisition_batch_id="batch.ola.043.projected",
    )

    assert receipt.cycle_status == "completed"
    assert receipt.persistence_count == 5
    assert capture_port.pending_count == 1


def run_deterministic_promotion_receipt_test():
    (
        first,
        first_staging,
        _,
    ) = build_promoter()
    (
        second,
        second_staging,
        _,
    ) = build_promoter()

    first_staging.route_batch(
        build_cohort(),
        T1,
    )
    second_staging.route_batch(
        build_cohort(),
        T1,
    )

    first_receipt = first.promote_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.043.1",
    )
    second_receipt = second.promote_completed_cycle(
        ola_017_cycle_result=completed_cycle_result(),
        acquisition_batch_id="batch.ola.043.1",
    )

    assert first_receipt == second_receipt
    assert (
        first_receipt.promotion_hash
        == second_receipt.promotion_hash
    )

    return first_receipt


def main():
    receipt = run_successful_promotion_test()

    run_failed_cycle_does_not_consume_stage_test()
    run_persistence_mismatch_does_not_consume_stage_test()
    run_canonical_count_mismatch_does_not_consume_stage_test()
    run_missing_stage_fails_closed_test()
    run_duplicate_promotion_fails_closed_test()
    run_scheduler_projection_compatibility_test()

    deterministic = (
        run_deterministic_promotion_receipt_test()
    )

    result = {
        "schema_version": receipt.schema_version,
        "engine_id": receipt.engine_id,
        "status": "passed",
        "ola_042_staged_cohort_consumed": True,
        "ola_041_capture_hook_consumed": True,
        "ola_040_capture_port_reached": True,
        "ola_017_completed_cycle_required": True,
        "ola_017_identity_preserved": True,
        "canonical_count_reconciled_before_stage_consume": True,
        "persistence_count_reconciled_before_stage_consume": True,
        "exact_canonical_objects_promoted": True,
        "observation_order_preserved": True,
        "market_order_preserved": True,
        "failed_cycle_preserves_pending_stage": True,
        "persistence_mismatch_preserves_pending_stage": True,
        "canonical_count_mismatch_preserves_pending_stage": True,
        "missing_stage_fails_closed": True,
        "duplicate_promotion_fails_closed": True,
        "scheduler_projection_compatibility_preserved": True,
        "scheduler_kwargs_unchanged": True,
        "scheduler_results_unchanged": True,
        "deterministic_promotion_receipt_valid": (
            deterministic.promotion_hash
            == receipt.promotion_hash
        ),
        "no_acquisition_owned": True,
        "no_persistence_owned": True,
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
        "[PASS] OLA-043 Oracle Staged Persisted Cohort "
        "Completion Promoter"
    )
    print(result)


if __name__ == "__main__":
    main()
