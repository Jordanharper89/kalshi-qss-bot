from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_append_only_ledger_contract import (
    build_oracle_memory_append_only_ledger_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    OracleMemoryLedgerIntegrityReplayInvariantError,
    build_oracle_memory_ledger_integrity_replay_certification,
    verify_oracle_memory_ledger_integrity_replay_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_015_contract(root: Path):
    fixture = load_module(
        root
        / "test_oml_015_oracle_memory_append_only_ledger_contract.py",
        "oml_015_fixture_for_oml_016",
    )

    store_certification = fixture.build_oml_014_certification(root)

    return build_oracle_memory_append_only_ledger_contract_certification(
        store_certification=store_certification,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryLedgerIntegrityReplayInvariantError:
        return

    raise AssertionError(f"tampered OML-016 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-016 TEST")
    print(" LEDGER INTEGRITY AND REPLAY CERTIFICATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    ledger_contract = build_oml_015_contract(root)

    certification = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    assert certification.schema_version == "OML-016"
    assert certification.engine_id == "OML-016"
    assert certification.upstream_schema_version == "OML-015"
    assert certification.upstream_engine_id == "OML-015"
    assert certification.partition_count == 8
    assert certification.genesis_anchor_verified
    assert certification.monotonic_sequence_verified
    assert certification.previous_hash_chain_verified
    assert certification.deterministic_entry_hashes_verified
    assert certification.deterministic_replay_verified
    assert certification.full_genesis_to_head_replay_verified
    assert certification.duplicate_record_rejection_verified
    assert certification.immutable_entries_verified
    assert certification.atomic_commit_verified
    assert certification.rollback_on_failure_verified
    assert certification.partial_commit_rejection_verified
    assert certification.destructive_updates_rejected
    assert certification.deletes_rejected
    assert certification.lineage_preserved
    assert not certification.persistence_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.database_access_enabled
    assert not certification.networking_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled
    assert certification.certification_ready
    assert certification.next_certification_authorized
    assert certification.read_only

    replay = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    assert replay == certification
    assert verify_oracle_memory_ledger_integrity_replay_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_ledger_integrity_replay_certification(
            replace(certification, previous_hash_chain_verified=False)
        ),
        "hash-chain guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_ledger_integrity_replay_certification(
            replace(certification, deterministic_replay_verified=False)
        ),
        "replay guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_ledger_integrity_replay_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_ledger_integrity_replay_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-015 ledger contract consumed")
    print("[PASS] OML-015 through OIT-050 lineage retained")
    print("[PASS] Eight ledger partitions integrity-certified")
    print("[PASS] Genesis anchors verified")
    print("[PASS] Monotonic sequence order verified")
    print("[PASS] Previous-entry hash chains verified")
    print("[PASS] Deterministic entry hashes verified")
    print("[PASS] Genesis-to-head replay verified")
    print("[PASS] Duplicate record rejection verified")
    print("[PASS] Atomic commit and rollback verified")
    print("[PASS] Partial commit rejection verified")
    print("[PASS] Immutable entries verified")
    print("[PASS] Destructive updates and deletes rejected")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Certification deterministic across replay")
    print("[PASS] Tampered replay certifications rejected")
    print("[DONE] OML-016 LEDGER INTEGRITY AND REPLAY CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
