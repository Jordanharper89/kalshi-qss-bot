from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (
    AcquisitionContractError,
    CanonicalObservation,
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlEvidence,
    RawSourceObservation,
    SourceHealthEvidence,
    UnapprovedSourceAdapterError,
    canonical_json,
    stable_hash,
)


ACQUIRED_AT = datetime(
    2026,
    7,
    11,
    20,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    11,
    19,
    59,
    30,
    tzinfo=timezone.utc,
)

CONTROL_CHECKED_AT = datetime(
    2026,
    7,
    11,
    19,
    59,
    50,
    tzinfo=timezone.utc,
)


class TestReadOnlyAdapter:
    adapter_id = "adapter.oracle.test.market"
    source_id = "source.test.market"
    read_only = True
    execution_allowed = False

    def acquire(self, *, acquired_at):
        assert acquired_at == ACQUIRED_AT

        observation_one = RawSourceObservation.create(
            source_observation_id="market-100",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "TEST-MARKET-1",
                "yes_price": Decimal("0.56"),
                "no_price": Decimal("0.44"),
                "volume": 1250,
            },
            provenance={
                "transport": "test",
                "endpoint_family": "market",
                "adapter_version": "1",
            },
        )

        observation_duplicate = RawSourceObservation.create(
            source_observation_id="market-100",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "TEST-MARKET-1",
                "yes_price": Decimal("0.56"),
                "no_price": Decimal("0.44"),
                "volume": 1250,
            },
            provenance={
                "transport": "test",
                "endpoint_family": "market",
                "adapter_version": "1",
            },
        )

        observation_two = RawSourceObservation.create(
            source_observation_id="market-101",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "TEST-MARKET-2",
                "yes_price": Decimal("0.31"),
                "no_price": Decimal("0.69"),
                "volume": 900,
            },
            provenance={
                "transport": "test",
                "endpoint_family": "market",
                "adapter_version": "1",
            },
        )

        return (
            observation_one,
            observation_duplicate,
            observation_two,
        )


def build_runtime():
    seen_content_hashes = {}

    def deduplication_hook(
        observation: CanonicalObservation,
        checked_at,
    ):
        existing_observation_id = seen_content_hashes.get(
            observation.content_hash
        )

        duplicate = existing_observation_id is not None

        canonical_observation_id = (
            existing_observation_id
            if duplicate
            else observation.observation_id
        )

        if not duplicate:
            seen_content_hashes[
                observation.content_hash
            ] = observation.observation_id

        return DeduplicationEvidence.create(
            observation=observation,
            duplicate=duplicate,
            canonical_observation_id=canonical_observation_id,
            checked_at=checked_at,
            deduplication_policy_id="dedup.content_hash.v1",
        )

    def canonical_router(
        observation: CanonicalObservation,
        routed_at,
    ):
        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            route_id="oracle.canonical.observation.router",
            routed_at=routed_at,
            accepted=True,
            metadata={
                "destination": "oracle",
                "persistence_required": True,
            },
        )

    return OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(TestReadOnlyAdapter(),),
        deduplication_hook=deduplication_hook,
        canonical_observation_router=canonical_router,
    )


def build_health_evidence():
    return SourceHealthEvidence.create(
        source_id="source.test.market",
        status="healthy",
        checked_at=CONTROL_CHECKED_AT,
        details={
            "reachable": True,
            "latency_ms": 12,
        },
    )


def build_rate_evidence():
    return RateControlEvidence.create(
        source_id="source.test.market",
        allowed=True,
        checked_at=CONTROL_CHECKED_AT,
        policy_id="rate.test.market.v1",
        details={
            "remaining": 99,
            "window_seconds": 60,
        },
    )


def run_primary_contract_test():
    runtime = build_runtime()

    first_record = runtime.acquire(
        adapter_id="adapter.oracle.test.market",
        acquired_at=ACQUIRED_AT,
        health_evidence=build_health_evidence(),
        rate_control_evidence=build_rate_evidence(),
        replay_metadata={
            "replay_source": "live_acquisition",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-001",
            "operator": "automated_runtime",
        },
    )

    second_runtime = build_runtime()

    second_record = second_runtime.acquire(
        adapter_id="adapter.oracle.test.market",
        acquired_at=ACQUIRED_AT,
        health_evidence=build_health_evidence(),
        rate_control_evidence=build_rate_evidence(),
        replay_metadata={
            "replay_source": "live_acquisition",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-001",
            "operator": "automated_runtime",
        },
    )

    assert first_record == second_record
    assert first_record.batch_hash == second_record.batch_hash
    assert (
        first_record.acquisition_batch_id
        == second_record.acquisition_batch_id
    )

    assert first_record.schema_version == "OLA-001"
    assert first_record.engine_id == "OLA-001"
    assert first_record.status == "passed"

    assert first_record.source_id == "source.test.market"
    assert (
        first_record.adapter_id
        == "adapter.oracle.test.market"
    )

    assert first_record.observation_count == 3
    assert first_record.canonical_count == 2
    assert first_record.duplicate_count == 1
    assert first_record.routed_count == 2

    assert first_record.read_only is True
    assert first_record.execution_allowed is False
    assert (
        first_record.trade_authorization_allowed
        is False
    )
    assert first_record.order_placement_allowed is False
    assert (
        first_record.execution_adapter_invocation_allowed
        is False
    )
    assert first_record.funds_moved is False
    assert first_record.portfolio_mutated is False

    first_observation = (
        first_record.observations[0].observation
    )
    duplicate_observation = (
        first_record.observations[1].observation
    )

    assert (
        first_observation.observation_id
        == duplicate_observation.observation_id
    )
    assert (
        first_observation.content_hash
        == duplicate_observation.content_hash
    )

    assert (
        first_record.observations[0]
        .deduplication
        .duplicate
        is False
    )
    assert (
        first_record.observations[1]
        .deduplication
        .duplicate
        is True
    )

    assert first_record.observations[0].routing is not None
    assert first_record.observations[1].routing is None
    assert first_record.observations[2].routing is not None

    assert (
        first_record.observations[0]
        .routing
        .accepted
        is True
    )

    recalculated_batch_hash = stable_hash(
        first_record.to_canonical_dict(
            include_batch_hash=False
        )
    )

    assert recalculated_batch_hash == first_record.batch_hash

    canonical_a = canonical_json(
        {
            "b": Decimal("0.560"),
            "a": {
                "z": 2,
                "y": 1,
            },
        }
    )

    canonical_b = canonical_json(
        {
            "a": {
                "y": 1,
                "z": 2,
            },
            "b": Decimal("0.560"),
        }
    )

    assert canonical_a == canonical_b
    assert stable_hash(canonical_a) == stable_hash(canonical_b)

    try:
        first_record.status = "mutated"
        raise AssertionError(
            "AcquisitionBatchRecord must be immutable"
        )
    except FrozenInstanceError:
        pass

    return first_record


def run_fail_closed_tests():
    runtime = build_runtime()

    try:
        runtime.acquire(
            adapter_id="adapter.execution.forbidden",
            acquired_at=ACQUIRED_AT,
            health_evidence=build_health_evidence(),
            rate_control_evidence=build_rate_evidence(),
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "unapproved adapters must fail closed"
        )
    except UnapprovedSourceAdapterError:
        pass

    blocked_health = SourceHealthEvidence.create(
        source_id="source.test.market",
        status="degraded",
        checked_at=CONTROL_CHECKED_AT,
        details={
            "reachable": False,
        },
    )

    try:
        runtime.acquire(
            adapter_id="adapter.oracle.test.market",
            acquired_at=ACQUIRED_AT,
            health_evidence=blocked_health,
            rate_control_evidence=build_rate_evidence(),
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "unhealthy sources must fail closed"
        )
    except RuntimeError:
        pass

    denied_rate = RateControlEvidence.create(
        source_id="source.test.market",
        allowed=False,
        checked_at=CONTROL_CHECKED_AT,
        policy_id="rate.test.market.v1",
        details={
            "remaining": 0,
        },
    )

    try:
        runtime.acquire(
            adapter_id="adapter.oracle.test.market",
            acquired_at=ACQUIRED_AT,
            health_evidence=build_health_evidence(),
            rate_control_evidence=denied_rate,
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "rate-denied sources must fail closed"
        )
    except RuntimeError:
        pass

    try:
        canonical_json({"bad": object()})
        raise AssertionError(
            "unsupported canonical types must fail closed"
        )
    except AcquisitionContractError:
        pass

    try:
        SourceHealthEvidence.create(
            source_id="source.test.market",
            status="healthy",
            checked_at=datetime(2026, 7, 11, 20, 0, 0),
            details={},
        )
        raise AssertionError(
            "naive contract timestamps must fail closed"
        )
    except AcquisitionContractError:
        pass


def main():
    record = run_primary_contract_test()
    run_fail_closed_tests()

    result = {
        "schema_version": record.schema_version,
        "engine_id": record.engine_id,
        "status": record.status,
        "source_id": record.source_id,
        "adapter_id": record.adapter_id,
        "observation_count": record.observation_count,
        "canonical_count": record.canonical_count,
        "duplicate_count": record.duplicate_count,
        "routed_count": record.routed_count,
        "read_only": record.read_only,
        "execution_allowed": record.execution_allowed,
        "trade_authorization_allowed": (
            record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            record.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            record.execution_adapter_invocation_allowed
        ),
        "funds_moved": record.funds_moved,
        "portfolio_mutated": record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-001 "
        "Oracle Live Read-Only Acquisition Runtime"
    )
    print(result)


if __name__ == "__main__":
    main()
