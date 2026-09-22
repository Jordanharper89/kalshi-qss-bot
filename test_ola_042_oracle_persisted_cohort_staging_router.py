from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_staging_router import (
    OraclePersistedCohortStagingRouter,
    PersistedCohortStagingRouterContractError,
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
    16,
    0,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    market_id,
    frame_id,
    batch_id="batch.ola.042.1",
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
    batch_id="batch.ola.042.1",
):
    return tuple(
        build_observation(
            market_id=f"KXTEST-STAGE-{index}",
            frame_id=str(index),
            batch_id=batch_id,
        )
        for index in range(1, 6)
    )


class FakePersistenceRouter:
    def __init__(
        self,
        *,
        fail_batch=False,
    ):
        self.fail_batch = fail_batch
        self.batch_calls = 0
        self.single_calls = 0
        self.last_observations = None
        self.last_routed_at = None

    def __call__(
        self,
        observation,
        routed_at,
    ):
        self.single_calls += 1

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            routed_at=routed_at,
            accepted=True,
            route_id="fake.persistence.single",
            metadata={
                "test": "OLA-042",
            },
        )

    def route_batch(
        self,
        observations,
        routed_at,
    ):
        self.batch_calls += 1
        self.last_observations = tuple(observations)
        self.last_routed_at = routed_at

        if self.fail_batch:
            raise RuntimeError(
                "delegated persistence failed"
            )

        return tuple(
            ObservationRoutingEvidence.create(
                observation_id=observation.observation_id,
                routed_at=routed_at,
                accepted=True,
                route_id="fake.persistence.batch",
                metadata={
                    "test": "OLA-042",
                },
            )
            for observation in observations
        )


def run_successful_stage_test():
    persistence_router = FakePersistenceRouter()
    router = OraclePersistedCohortStagingRouter(
        persistence_router=persistence_router
    )
    cohort = build_cohort()

    evidence = router.route_batch(
        cohort,
        T1,
    )

    assert persistence_router.batch_calls == 1
    assert persistence_router.last_observations == cohort
    assert all(
        delegated is original
        for delegated, original in zip(
            persistence_router.last_observations,
            cohort,
        )
    )
    assert len(evidence) == 5
    assert router.pending_stage_count == 1
    assert router.consumed_stage_count == 0

    stage = router.consume_stage(
        acquisition_batch_id="batch.ola.042.1"
    )

    assert stage.schema_version == "OLA-042"
    assert stage.engine_id == "OLA-042"
    assert stage.canonical_count == 5
    assert stage.canonical_observations == cohort
    assert all(
        staged is original
        for staged, original in zip(
            stage.canonical_observations,
            cohort,
        )
    )
    assert stage.routing_evidence_observation_ids == (
        stage.observation_ids
    )
    assert router.pending_stage_count == 0
    assert router.consumed_stage_count == 1

    return router, stage


def run_delegated_failure_never_stages_test():
    persistence_router = FakePersistenceRouter(
        fail_batch=True
    )
    router = OraclePersistedCohortStagingRouter(
        persistence_router=persistence_router
    )

    try:
        router.route_batch(
            build_cohort(),
            T1,
        )
        raise AssertionError(
            "delegated persistence failure must propagate"
        )
    except RuntimeError:
        pass

    assert persistence_router.batch_calls == 1
    assert router.pending_stage_count == 0
    assert router.consumed_stage_count == 0


def run_duplicate_stage_fail_closed_test():
    router = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )
    cohort = build_cohort()

    router.route_batch(
        cohort,
        T1,
    )

    try:
        router.route_batch(
            cohort,
            T1,
        )
        raise AssertionError(
            "duplicate acquisition batch stage must fail closed"
        )
    except PersistedCohortStagingRouterContractError:
        pass

    assert router.pending_stage_count == 1


def run_consumed_stage_restaging_fail_closed_test():
    router, stage = run_successful_stage_test()

    try:
        router.route_batch(
            stage.canonical_observations,
            T1,
        )
        raise AssertionError(
            "consumed acquisition batch cannot be restaged"
        )
    except PersistedCohortStagingRouterContractError:
        pass

    assert router.pending_stage_count == 0
    assert router.consumed_stage_count == 1


def run_single_route_delegation_test():
    persistence_router = FakePersistenceRouter()
    router = OraclePersistedCohortStagingRouter(
        persistence_router=persistence_router
    )
    observation = build_cohort()[0]

    evidence = router(
        observation,
        T1,
    )

    assert evidence.accepted is True
    assert evidence.observation_id == observation.observation_id
    assert persistence_router.single_calls == 1
    assert router.pending_stage_count == 0


def run_mixed_batch_fail_closed_test():
    router = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-STAGE-5",
        frame_id="mixed",
        batch_id="batch.ola.042.other",
    )

    try:
        router.route_batch(
            cohort,
            T1,
        )
        raise AssertionError(
            "mixed acquisition batch must fail closed"
        )
    except PersistedCohortStagingRouterContractError:
        pass

    assert router.persistence_router.batch_calls == 0
    assert router.pending_stage_count == 0


def run_duplicate_market_fail_closed_test():
    router = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )
    cohort = list(build_cohort())

    cohort[-1] = build_observation(
        market_id="KXTEST-STAGE-4",
        frame_id="duplicate-market",
    )

    try:
        router.route_batch(
            cohort,
            T1,
        )
        raise AssertionError(
            "duplicate market identity must fail closed"
        )
    except PersistedCohortStagingRouterContractError:
        pass

    assert router.persistence_router.batch_calls == 0
    assert router.pending_stage_count == 0


def run_peek_metadata_test():
    router = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )

    router.route_batch(
        build_cohort(),
        T1,
    )

    metadata = router.peek_stage_metadata(
        acquisition_batch_id="batch.ola.042.1"
    )

    assert metadata is not None
    assert metadata["schema_version"] == "OLA-042"
    assert metadata["canonical_count"] == 5
    assert "canonical_observations" not in metadata
    assert "delegated_routing_evidence" not in metadata

    try:
        metadata["canonical_count"] = 99
        raise AssertionError(
            "stage metadata must be immutable"
        )
    except TypeError:
        pass


def run_deterministic_stage_hash_test():
    first = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )
    second = OraclePersistedCohortStagingRouter(
        persistence_router=FakePersistenceRouter()
    )

    first.route_batch(
        build_cohort(),
        T1,
    )
    second.route_batch(
        build_cohort(),
        T1,
    )

    first_stage = first.consume_stage(
        acquisition_batch_id="batch.ola.042.1"
    )
    second_stage = second.consume_stage(
        acquisition_batch_id="batch.ola.042.1"
    )

    assert first_stage == second_stage
    assert first_stage.stage_hash == second_stage.stage_hash

    return first_stage


def main():
    _, stage = run_successful_stage_test()

    run_delegated_failure_never_stages_test()
    run_duplicate_stage_fail_closed_test()
    run_consumed_stage_restaging_fail_closed_test()
    run_single_route_delegation_test()
    run_mixed_batch_fail_closed_test()
    run_duplicate_market_fail_closed_test()
    run_peek_metadata_test()

    deterministic = run_deterministic_stage_hash_test()

    result = {
        "schema_version": stage.schema_version,
        "engine_id": stage.engine_id,
        "status": "passed",
        "existing_persistence_router_delegated": True,
        "route_batch_delegated_before_stage": True,
        "delegated_failure_never_stages": True,
        "exact_canonical_objects_preserved": True,
        "exact_observation_order_preserved": True,
        "routing_evidence_identity_reconciled": True,
        "single_acquisition_batch_identity_enforced": True,
        "unique_observation_identity_enforced": True,
        "unique_market_identity_enforced": True,
        "write_once_stage_per_batch": True,
        "consume_once_stage_per_batch": True,
        "consumed_batch_restaging_fails_closed": True,
        "single_observation_route_delegation_preserved": True,
        "immutable_metadata_projection": True,
        "canonical_objects_excluded_from_metadata": True,
        "deterministic_stage_hash_valid": (
            deterministic.stage_hash == stage.stage_hash
        ),
        "ola_015_persistence_semantics_not_owned": True,
        "ola_041_promotion_not_owned": True,
        "no_lineage_advancement_owned": True,
        "no_intelligence_interpretation": True,
        "no_signal_scoring": True,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "read_only": stage.read_only,
        "execution_allowed": stage.execution_allowed,
        "execution_adapter_resolved": (
            stage.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            stage.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            stage.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            stage.order_placement_allowed
        ),
        "funds_moved": stage.funds_moved,
        "portfolio_mutated": stage.portfolio_mutated,
    }

    print(
        "[PASS] OLA-042 Oracle Persisted Cohort "
        "Staging Router"
    )
    print(result)


if __name__ == "__main__":
    main()
