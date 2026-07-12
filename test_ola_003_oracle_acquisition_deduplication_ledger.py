from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    DeduplicationLedgerSnapshotError,
    OracleAcquisitionDeduplicationLedger,
    RawSourceObservation,
)


OBSERVED_AT = datetime(
    2026,
    7,
    11,
    21,
    59,
    30,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    11,
    22,
    0,
    0,
    tzinfo=timezone.utc,
)

CHECKED_AT = datetime(
    2026,
    7,
    11,
    22,
    0,
    1,
    tzinfo=timezone.utc,
)

SNAPSHOT_AT = datetime(
    2026,
    7,
    11,
    22,
    1,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    source_observation_id,
    market_id,
    price,
):
    raw = RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=OBSERVED_AT,
        observation_type="market_snapshot",
        payload={
            "market_id": market_id,
            "price": Decimal(price),
            "volume": 1000,
        },
        provenance={
            "adapter_id": "adapter.oracle.test.market",
            "transport": "test",
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.market",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch-ola-003-test",
    )


def run_primary_contract_test():
    ledger = OracleAcquisitionDeduplicationLedger(
        policy_id="oracle.dedup.content_hash.v1",
        entry_metadata={
            "ledger_version": 1,
            "persistence_required": True,
        },
    )

    observation_one = build_observation(
        source_observation_id="source-observation-100",
        market_id="TEST-MARKET-1",
        price="0.56",
    )

    identical_observation = build_observation(
        source_observation_id="source-observation-100",
        market_id="TEST-MARKET-1",
        price="0.56",
    )

    observation_two = build_observation(
        source_observation_id="source-observation-101",
        market_id="TEST-MARKET-2",
        price="0.31",
    )

    first = ledger.evaluate(
        observation_one,
        CHECKED_AT,
    )

    duplicate = ledger.evaluate(
        identical_observation,
        CHECKED_AT,
    )

    second = ledger.evaluate(
        observation_two,
        CHECKED_AT,
    )

    assert first.duplicate is False
    assert duplicate.duplicate is True
    assert second.duplicate is False

    assert (
        first.canonical_observation_id
        == observation_one.observation_id
    )

    assert (
        duplicate.canonical_observation_id
        == observation_one.observation_id
    )

    assert (
        duplicate.observation_id
        == observation_one.observation_id
    )

    assert ledger.entry_count == 2

    assert len(ledger.content_hashes) == 2

    first_entry = ledger.get_entry(
        content_hash=observation_one.content_hash
    )

    assert first_entry is not None

    assert (
        first_entry.calculate_entry_hash()
        == first_entry.entry_hash
    )

    assert (
        first_entry.canonical_observation_id
        == observation_one.observation_id
    )

    assert first_entry.source_id == "source.test.market"

    assert (
        first_entry.observation_type
        == "market_snapshot"
    )

    assert first_entry.first_seen_at == CHECKED_AT

    try:
        first_entry.source_id = "mutated"
        raise AssertionError(
            "deduplication ledger entries must be immutable"
        )
    except FrozenInstanceError:
        pass

    snapshot = ledger.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "deduplication_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-003",
            "operator": "automated_runtime",
        },
    )

    assert snapshot.schema_version == "OLA-003"
    assert snapshot.engine_id == "OLA-003"
    assert snapshot.entry_count == 2

    assert (
        snapshot.calculate_snapshot_hash()
        == snapshot.snapshot_hash
    )

    assert snapshot.read_only is True
    assert snapshot.execution_allowed is False
    assert snapshot.acquisition_performed is False
    assert snapshot.routing_performed is False

    assert (
        snapshot.trade_authorization_allowed
        is False
    )

    assert snapshot.order_placement_allowed is False

    assert (
        snapshot.execution_adapter_invocation_allowed
        is False
    )

    assert snapshot.funds_moved is False
    assert snapshot.portfolio_mutated is False

    restored = (
        OracleAcquisitionDeduplicationLedger
        .restore_snapshot(
            snapshot=snapshot,
            entry_metadata={
                "ledger_version": 1,
                "persistence_required": True,
            },
        )
    )

    assert restored.entry_count == ledger.entry_count

    restored_duplicate = restored.evaluate(
        identical_observation,
        CHECKED_AT,
    )

    assert restored_duplicate.duplicate is True

    assert (
        restored_duplicate.canonical_observation_id
        == observation_one.observation_id
    )

    canonical_snapshot_data = (
        snapshot.to_canonical_dict()
    )

    restored_from_dict = (
        OracleAcquisitionDeduplicationLedger
        .restore_canonical_dict(
            snapshot_data=canonical_snapshot_data,
            entry_metadata={
                "ledger_version": 1,
                "persistence_required": True,
            },
        )
    )

    assert restored_from_dict.entry_count == 2

    replay_snapshot = restored_from_dict.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "deduplication_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-003",
            "operator": "automated_runtime",
        },
    )

    assert (
        replay_snapshot.snapshot_hash
        == snapshot.snapshot_hash
    )

    for original_entry, restored_entry in zip(
        snapshot.entries,
        replay_snapshot.entries,
    ):
        assert (
            original_entry.entry_hash
            == restored_entry.entry_hash
        )

        assert (
            restored_entry.calculate_entry_hash()
            == restored_entry.entry_hash
        )

    return ledger, snapshot, first, duplicate


def run_fail_closed_tests():
    ledger = OracleAcquisitionDeduplicationLedger()

    observation = build_observation(
        source_observation_id="source-observation-200",
        market_id="TEST-MARKET-3",
        price="0.77",
    )

    try:
        ledger.evaluate(
            observation,
            datetime(
                2026,
                7,
                11,
                22,
                0,
                0,
            ),
        )
        raise AssertionError(
            "naive checked_at must fail closed"
        )
    except ValueError:
        pass

    ledger.evaluate(
        observation,
        CHECKED_AT,
    )

    snapshot = ledger.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={},
        audit_metadata={},
    )

    tampered_snapshot_data = (
        snapshot.to_canonical_dict()
    )

    tampered_snapshot_data["entry_count"] = 99

    try:
        (
            OracleAcquisitionDeduplicationLedger
            .restore_canonical_dict(
                snapshot_data=tampered_snapshot_data
            )
        )
        raise AssertionError(
            "tampered snapshot must fail closed"
        )
    except DeduplicationLedgerSnapshotError:
        pass

    tampered_entry_data = (
        snapshot.to_canonical_dict()
    )

    tampered_entry_data["entries"][0][
        "canonical_observation_id"
    ] = "tampered-observation-id"

    try:
        (
            OracleAcquisitionDeduplicationLedger
            .restore_canonical_dict(
                snapshot_data=tampered_entry_data
            )
        )
        raise AssertionError(
            "tampered entry must fail closed"
        )
    except DeduplicationLedgerSnapshotError:
        pass

    incompatible_data = (
        snapshot.to_canonical_dict()
    )

    incompatible_data["execution_allowed"] = True

    try:
        (
            OracleAcquisitionDeduplicationLedger
            .restore_canonical_dict(
                snapshot_data=incompatible_data
            )
        )
        raise AssertionError(
            "execution-capable snapshot must fail closed"
        )
    except DeduplicationLedgerSnapshotError:
        pass

    invalid_entry_hash_data = (
        snapshot.to_canonical_dict()
    )

    invalid_entry_hash_data["entries"][0][
        "entry_hash"
    ] = "0" * 64

    try:
        (
            OracleAcquisitionDeduplicationLedger
            .restore_canonical_dict(
                snapshot_data=invalid_entry_hash_data
            )
        )
        raise AssertionError(
            "invalid entry hash must fail closed"
        )
    except DeduplicationLedgerSnapshotError:
        pass

    invalid_snapshot_hash_data = (
        snapshot.to_canonical_dict()
    )

    invalid_snapshot_hash_data[
        "snapshot_hash"
    ] = "0" * 64

    try:
        (
            OracleAcquisitionDeduplicationLedger
            .restore_canonical_dict(
                snapshot_data=invalid_snapshot_hash_data
            )
        )
        raise AssertionError(
            "invalid snapshot hash must fail closed"
        )
    except DeduplicationLedgerSnapshotError:
        pass


def main():
    (
        ledger,
        snapshot,
        first,
        duplicate,
    ) = run_primary_contract_test()

    run_fail_closed_tests()

    result = {
        "schema_version": snapshot.schema_version,
        "engine_id": snapshot.engine_id,
        "status": "passed",
        "policy_id": ledger.policy_id,
        "entry_count": ledger.entry_count,
        "first_duplicate": first.duplicate,
        "repeat_duplicate": duplicate.duplicate,
        "snapshot_entry_count": snapshot.entry_count,
        "entry_hash_contract_valid": True,
        "snapshot_hash_contract_valid": True,
        "snapshot_restore_valid": True,
        "canonical_dict_restore_valid": True,
        "read_only": snapshot.read_only,
        "execution_allowed": snapshot.execution_allowed,
        "acquisition_performed": (
            snapshot.acquisition_performed
        ),
        "routing_performed": snapshot.routing_performed,
        "trade_authorization_allowed": (
            snapshot.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            snapshot.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            snapshot.execution_adapter_invocation_allowed
        ),
        "funds_moved": snapshot.funds_moved,
        "portfolio_mutated": snapshot.portfolio_mutated,
    }

    print(
        "[PASS] OLA-003 "
        "Oracle Acquisition Deduplication Ledger"
    )

    print(result)


if __name__ == "__main__":
    main()
