from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    OracleCanonicalObservationPersistenceLedger,
    OracleCanonicalObservationPersistenceRouter,
    PersistenceRoutingContractError,
    PersistenceRoutingFailure,
    RawSourceObservation,
)


OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    0,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    0,
    0,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    0,
    1,
    0,
    tzinfo=timezone.utc,
)

ROUTED_AT_ONE = datetime(
    2026,
    7,
    12,
    0,
    1,
    1,
    tzinfo=timezone.utc,
)

ROUTED_AT_TWO = datetime(
    2026,
    7,
    12,
    0,
    1,
    2,
    tzinfo=timezone.utc,
)


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id="kalshi.route.snapshot.001",
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "source_market_id": "KXBTC-TEST-001",
            "share_side": "yes",
            "share_price": Decimal("0.31"),
        },
        provenance={
            "source_id": "source.kalshi.market_data",
            "adapter_id": "adapter.oracle.kalshi",
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.009.001",
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id="coinbase.route.snapshot.001",
        observed_at=OBSERVED_AT_TWO,
        observation_type="asset_snapshot",
        payload={
            "symbol": "BTC-USD",
            "price": Decimal("117420"),
        },
        provenance={
            "source_id": "source.coinbase.market_data",
            "adapter_id": "adapter.oracle.coinbase",
        },
    )

    return CanonicalObservation.create(
        source_id="source.coinbase.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.009.001",
    )


def build_router():
    ledger = OracleCanonicalObservationPersistenceLedger()

    router = OracleCanonicalObservationPersistenceRouter(
        persistence_ledger=ledger,
        route_id="oracle.canonical.persistence.router.v1",
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
        replay_metadata={
            "replay_source": "persistence_router",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-009",
            "operator": "automated_runtime",
        },
    )

    return router, ledger


def run_primary_routing_test():
    router, ledger = build_router()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    first_evidence = router.route(
        observation_one,
        ROUTED_AT_ONE,
    )

    second_evidence = router(
        observation_two,
        ROUTED_AT_TWO,
    )

    assert first_evidence.accepted is True
    assert second_evidence.accepted is True

    assert first_evidence.route_id == (
        "oracle.canonical.persistence.router.v1"
    )

    assert second_evidence.route_id == (
        "oracle.canonical.persistence.router.v1"
    )

    assert (
        first_evidence.observation_id
        == observation_one.observation_id
    )

    assert (
        second_evidence.observation_id
        == observation_two.observation_id
    )

    assert first_evidence.routed_at == ROUTED_AT_ONE
    assert second_evidence.routed_at == ROUTED_AT_TWO

    assert ledger.entry_count == 2
    assert router.routing_record_count == 2

    first_entry = ledger.get_entry(
        observation_id=observation_one.observation_id
    )

    second_entry = ledger.get_entry(
        observation_id=observation_two.observation_id
    )

    assert first_entry is not None
    assert second_entry is not None

    assert first_entry.persisted_at == ROUTED_AT_ONE
    assert second_entry.persisted_at == ROUTED_AT_TWO

    assert (
        second_entry.previous_chain_hash
        == first_entry.chain_hash
    )

    first_record = router.get_routing_record(
        observation_id=observation_one.observation_id
    )

    second_record = router.get_routing_record(
        observation_id=observation_two.observation_id
    )

    assert first_record is not None
    assert second_record is not None

    assert first_record.schema_version == "OLA-009"
    assert first_record.engine_id == "OLA-009"

    assert first_record.persistence_verified is True
    assert first_record.routing_accepted is True

    assert (
        first_record.persistence_entry_id
        == first_entry.persistence_entry_id
    )

    assert (
        first_record.persistence_sequence_number
        == first_entry.sequence_number
    )

    assert (
        first_record.persistence_entry_hash
        == first_entry.entry_hash
    )

    assert (
        first_record.persistence_chain_hash
        == first_entry.chain_hash
    )

    assert (
        first_record.persistence_previous_chain_hash
        == first_entry.previous_chain_hash
    )

    assert (
        first_record.observation_id
        == observation_one.observation_id
    )

    assert (
        first_record.source_id
        == observation_one.source_id
    )

    assert (
        first_record.acquisition_batch_id
        == observation_one.acquisition_batch_id
    )

    assert (
        first_record.content_hash
        == observation_one.content_hash
    )

    assert (
        first_record.observation_replay_hash
        == observation_one.replay_hash
    )

    assert first_record.immutable is True
    assert first_record.replayable is True
    assert first_record.auditable is True
    assert first_record.explainable is True

    assert first_record.read_only is True
    assert first_record.execution_allowed is False

    assert (
        first_record.execution_adapter_resolved
        is False
    )

    assert (
        first_record.execution_adapter_invoked
        is False
    )

    assert (
        first_record.trade_authorization_allowed
        is False
    )

    assert (
        first_record.order_placement_allowed
        is False
    )

    assert first_record.funds_moved is False
    assert first_record.portfolio_mutated is False

    try:
        first_record.routing_accepted = False

        raise AssertionError(
            "persistence routing record must be immutable"
        )

    except FrozenInstanceError:
        pass

    first_metadata = dict(first_evidence.metadata)

    assert (
        first_metadata["persistence_verified"]
        is True
    )

    assert (
        first_metadata["persistence_entry_id"]
        == first_entry.persistence_entry_id
    )

    assert (
        first_metadata["persistence_sequence_number"]
        == 1
    )

    assert (
        first_metadata["persistence_chain_hash"]
        == first_entry.chain_hash
    )

    assert (
        first_metadata["observation_content_hash"]
        == observation_one.content_hash
    )

    assert (
        first_metadata["observation_replay_hash"]
        == observation_one.replay_hash
    )

    return (
        router,
        ledger,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    )


def run_deterministic_replay_test():
    first_router, first_ledger = build_router()

    second_router, second_ledger = build_router()

    first_observation_one = build_observation_one()
    first_observation_two = build_observation_two()

    second_observation_one = build_observation_one()
    second_observation_two = build_observation_two()

    first_evidence_one = first_router(
        first_observation_one,
        ROUTED_AT_ONE,
    )

    first_evidence_two = first_router(
        first_observation_two,
        ROUTED_AT_TWO,
    )

    second_evidence_one = second_router(
        second_observation_one,
        ROUTED_AT_ONE,
    )

    second_evidence_two = second_router(
        second_observation_two,
        ROUTED_AT_TWO,
    )

    assert first_evidence_one == second_evidence_one
    assert first_evidence_two == second_evidence_two

    assert (
        first_ledger.terminal_chain_hash
        == second_ledger.terminal_chain_hash
    )

    assert (
        first_router.routing_records
        == second_router.routing_records
    )

    return first_router


def run_duplicate_route_fail_closed_test():
    router, ledger = build_router()

    observation = build_observation_one()

    router(
        observation,
        ROUTED_AT_ONE,
    )

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "duplicate routing must fail closed"
        )

    except PersistenceRoutingFailure:
        pass

    assert ledger.entry_count == 1
    assert router.routing_record_count == 1


def run_external_persistence_conflict_test():
    router, ledger = build_router()

    observation = build_observation_one()

    ledger.append(
        observation=observation,
        persisted_at=ROUTED_AT_ONE,
        persistence_metadata={
            "external_test": True,
        },
    )

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "pre-persisted observation must fail routing closed"
        )

    except PersistenceRoutingFailure:
        pass

    assert ledger.entry_count == 1
    assert router.routing_record_count == 0


def run_timestamp_fail_closed_test():
    router, ledger = build_router()

    observation = build_observation_one()

    try:
        router(
            observation,
            datetime(
                2026,
                7,
                12,
                0,
                1,
                1,
            ),
        )

        raise AssertionError(
            "naive routed_at must fail closed"
        )

    except PersistenceRoutingContractError:
        pass

    assert ledger.entry_count == 0
    assert router.routing_record_count == 0

    try:
        router(
            observation,
            OBSERVED_AT_ONE,
        )

        raise AssertionError(
            "routing before acquired_at must fail closed"
        )

    except PersistenceRoutingContractError:
        pass

    assert ledger.entry_count == 0
    assert router.routing_record_count == 0


def main():
    (
        router,
        ledger,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    ) = run_primary_routing_test()

    replay_router = run_deterministic_replay_test()

    run_duplicate_route_fail_closed_test()
    run_external_persistence_conflict_test()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": first_record.schema_version,
        "engine_id": first_record.engine_id,
        "status": "passed",
        "route_id": router.route_id,
        "routing_record_count": (
            router.routing_record_count
        ),
        "persistence_entry_count": ledger.entry_count,
        "first_routing_accepted": (
            first_evidence.accepted
        ),
        "second_routing_accepted": (
            second_evidence.accepted
        ),
        "persistence_before_acceptance": True,
        "persistence_verified": (
            first_record.persistence_verified
        ),
        "observation_identity_preserved": True,
        "source_identity_preserved": True,
        "acquisition_batch_identity_preserved": True,
        "content_hash_preserved": True,
        "observation_replay_hash_preserved": True,
        "persistence_sequence_preserved": True,
        "persistence_chain_preserved": True,
        "duplicate_route_blocked": True,
        "external_persistence_conflict_blocked": True,
        "deterministic_replay_valid": (
            replay_router.routing_record_count == 2
        ),
        "read_only": first_record.read_only,
        "execution_allowed": first_record.execution_allowed,
        "execution_adapter_resolved": (
            first_record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            first_record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            first_record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            first_record.order_placement_allowed
        ),
        "funds_moved": first_record.funds_moved,
        "portfolio_mutated": first_record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-009 Oracle Canonical Observation "
        "Persistence Router"
    )

    print(result)


if __name__ == "__main__":
    main()
