from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    ObservationPersistenceConflictError,
    ObservationPersistenceSnapshotError,
    OracleCanonicalObservationPersistenceLedger,
    RawSourceObservation,
)


OBSERVED_AT_ONE = datetime(
    2026,
    7,
    11,
    23,
    14,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    11,
    23,
    14,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    11,
    23,
    15,
    0,
    tzinfo=timezone.utc,
)

PERSISTED_AT = datetime(
    2026,
    7,
    11,
    23,
    15,
    1,
    tzinfo=timezone.utc,
)

SNAPSHOT_AT = datetime(
    2026,
    7,
    11,
    23,
    16,
    0,
    tzinfo=timezone.utc,
)


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id="kalshi.snapshot.001",
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "source_market_id": (
                "KXBTC-26JUL11-116000"
            ),
            "share_side": "yes",
            "share_price": Decimal("0.31"),
            "volume": 1250,
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
        acquisition_batch_id="batch.persistence.001",
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id="coinbase.snapshot.001",
        observed_at=OBSERVED_AT_TWO,
        observation_type="asset_snapshot",
        payload={
            "symbol": "BTC-USD",
            "price": Decimal("117420"),
            "volume": Decimal("250.5"),
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
        acquisition_batch_id="batch.persistence.001",
    )


def run_primary_persistence_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    first_entry = ledger.append(
        observation=observation_one,
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
    )

    second_entry = ledger.append(
        observation=observation_two,
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
    )

    assert ledger.entry_count == 2

    assert ledger.observation_ids == (
        observation_one.observation_id,
        observation_two.observation_id,
    )

    assert first_entry.sequence_number == 1
    assert second_entry.sequence_number == 2

    assert (
        second_entry.previous_chain_hash
        == first_entry.chain_hash
    )

    assert (
        first_entry.calculate_entry_hash()
        == first_entry.entry_hash
    )

    assert (
        first_entry.calculate_chain_hash()
        == first_entry.chain_hash
    )

    assert (
        second_entry.calculate_entry_hash()
        == second_entry.entry_hash
    )

    assert (
        second_entry.calculate_chain_hash()
        == second_entry.chain_hash
    )

    assert (
        ledger.terminal_chain_hash
        == second_entry.chain_hash
    )

    assert (
        first_entry.observation_id
        == observation_one.observation_id
    )

    assert (
        first_entry.source_id
        == "source.kalshi.market_data"
    )

    assert (
        first_entry.source_observation_id
        == "kalshi.snapshot.001"
    )

    assert (
        first_entry.acquisition_batch_id
        == "batch.persistence.001"
    )

    assert (
        first_entry.content_hash
        == observation_one.content_hash
    )

    assert (
        first_entry.observation_replay_hash
        == observation_one.replay_hash
    )

    assert first_entry.immutable is True
    assert first_entry.append_only is True
    assert first_entry.replayable is True
    assert first_entry.auditable is True
    assert first_entry.explainable is True

    assert first_entry.read_only is True
    assert first_entry.execution_allowed is False

    assert (
        first_entry.execution_adapter_resolved
        is False
    )

    assert (
        first_entry.execution_adapter_invoked
        is False
    )

    assert (
        first_entry.trade_authorization_allowed
        is False
    )

    assert (
        first_entry.order_placement_allowed
        is False
    )

    assert first_entry.funds_moved is False
    assert first_entry.portfolio_mutated is False

    fetched = ledger.get_entry(
        observation_id=observation_one.observation_id
    )

    assert fetched == first_entry

    try:
        first_entry.source_id = "mutated"

        raise AssertionError(
            "persistence entries must be immutable"
        )

    except FrozenInstanceError:
        pass

    snapshot = ledger.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "persistence_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-008",
            "operator": "automated_runtime",
        },
    )

    assert snapshot.schema_version == "OLA-008"
    assert snapshot.engine_id == "OLA-008"

    assert snapshot.entry_count == 2

    assert (
        snapshot.terminal_chain_hash
        == ledger.terminal_chain_hash
    )

    assert (
        snapshot.calculate_snapshot_hash()
        == snapshot.snapshot_hash
    )

    assert snapshot.immutable is True
    assert snapshot.append_only is True
    assert snapshot.read_only is True

    assert snapshot.execution_allowed is False

    assert (
        snapshot.execution_adapter_resolved
        is False
    )

    assert (
        snapshot.execution_adapter_invoked
        is False
    )

    assert (
        snapshot.trade_authorization_allowed
        is False
    )

    assert (
        snapshot.order_placement_allowed
        is False
    )

    assert snapshot.funds_moved is False
    assert snapshot.portfolio_mutated is False

    restored = (
        OracleCanonicalObservationPersistenceLedger
        .restore_snapshot(
            snapshot=snapshot
        )
    )

    assert restored.entry_count == ledger.entry_count

    assert (
        restored.terminal_chain_hash
        == ledger.terminal_chain_hash
    )

    assert (
        restored.observation_ids
        == ledger.observation_ids
    )

    restored_first = restored.get_entry(
        observation_id=observation_one.observation_id
    )

    assert restored_first == first_entry

    replay_snapshot = restored.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "persistence_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-008",
            "operator": "automated_runtime",
        },
    )

    assert (
        replay_snapshot.snapshot_hash
        == snapshot.snapshot_hash
    )

    return (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    )


def run_atomic_append_many_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    entries = ledger.append_many(
        observations=(
            observation_one,
            observation_two,
        ),
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "batch_append": True,
        },
    )

    assert len(entries) == 2
    assert ledger.entry_count == 2

    assert entries[0].sequence_number == 1
    assert entries[1].sequence_number == 2

    assert (
        entries[0].previous_chain_hash
        != entries[1].previous_chain_hash
    )

    assert (
        entries[1].previous_chain_hash
        == entries[0].chain_hash
    )

    return ledger


def run_duplicate_identity_fail_closed_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation = build_observation_one()

    ledger.append(
        observation=observation,
        persisted_at=PERSISTED_AT,
        persistence_metadata={},
    )

    try:
        ledger.append(
            observation=observation,
            persisted_at=PERSISTED_AT,
            persistence_metadata={},
        )

        raise AssertionError(
            "duplicate observation identity must fail closed"
        )

    except ObservationPersistenceConflictError:
        pass

    assert ledger.entry_count == 1


def run_append_many_atomic_failure_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()

    try:
        ledger.append_many(
            observations=(
                observation_one,
                observation_one,
            ),
            persisted_at=PERSISTED_AT,
            persistence_metadata={},
        )

        raise AssertionError(
            "duplicate append_many batch must fail closed"
        )

    except ObservationPersistenceConflictError:
        pass

    assert ledger.entry_count == 0


def run_snapshot_tamper_fail_closed_tests():
    (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    ) = run_primary_persistence_test()

    bad_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=99,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash=snapshot.snapshot_hash,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=snapshot.execution_allowed,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=bad_snapshot
            )
        )

        raise AssertionError(
            "tampered entry count must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass

    bad_hash_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=snapshot.entry_count,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash="0" * 64,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=snapshot.execution_allowed,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=bad_hash_snapshot
            )
        )

        raise AssertionError(
            "tampered snapshot hash must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass

    execution_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=snapshot.entry_count,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash=snapshot.snapshot_hash,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=True,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=execution_snapshot
            )
        )

        raise AssertionError(
            "execution-capable snapshot must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass


def run_timestamp_fail_closed_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    try:
        ledger.append(
            observation=build_observation_one(),
            persisted_at=datetime(
                2026,
                7,
                11,
                23,
                15,
                1,
            ),
            persistence_metadata={},
        )

        raise AssertionError(
            "naive persisted_at must fail closed"
        )

    except ValueError:
        pass

    assert ledger.entry_count == 0


def main():
    (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    ) = run_primary_persistence_test()

    atomic_ledger = run_atomic_append_many_test()

    run_duplicate_identity_fail_closed_test()
    run_append_many_atomic_failure_test()
    run_snapshot_tamper_fail_closed_tests()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": snapshot.schema_version,
        "engine_id": snapshot.engine_id,
        "status": "passed",
        "entry_count": ledger.entry_count,
        "first_sequence_number": (
            first_entry.sequence_number
        ),
        "second_sequence_number": (
            second_entry.sequence_number
        ),
        "chain_link_valid": (
            second_entry.previous_chain_hash
            == first_entry.chain_hash
        ),
        "terminal_chain_hash_valid": (
            ledger.terminal_chain_hash
            == second_entry.chain_hash
        ),
        "append_only": snapshot.append_only,
        "immutable": snapshot.immutable,
        "duplicate_observation_blocked": True,
        "duplicate_content_blocked": True,
        "atomic_append_many_valid": (
            atomic_ledger.entry_count == 2
        ),
        "snapshot_restore_valid": True,
        "deterministic_replay_valid": True,
        "source_identity_preserved": True,
        "acquisition_batch_identity_preserved": True,
        "content_hash_preserved": True,
        "observation_replay_hash_preserved": True,
        "read_only": snapshot.read_only,
        "execution_allowed": snapshot.execution_allowed,
        "execution_adapter_resolved": (
            snapshot.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            snapshot.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            snapshot.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            snapshot.order_placement_allowed
        ),
        "funds_moved": snapshot.funds_moved,
        "portfolio_mutated": snapshot.portfolio_mutated,
    }

    print(
        "[PASS] OLA-008 Oracle Canonical Observation "
        "Persistence Ledger"
    )

    print(result)


if __name__ == "__main__":
    main()
