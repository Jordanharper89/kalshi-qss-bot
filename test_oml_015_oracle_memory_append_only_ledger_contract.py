from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_append_only_ledger_contract import (
    GENESIS_PARENT_HASH,
    OracleMemoryAppendOnlyLedgerInvariantError,
    build_oracle_memory_append_only_ledger_contract_certification,
    verify_oracle_memory_append_only_ledger_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)
from qseries_v2.oracle_memory.oracle_memory_store_admission_and_atomicity_certification import (
    build_oracle_memory_store_admission_atomicity_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_014_certification(root: Path):
    fixture = load_module(
        root
        / "test_oml_014_oracle_memory_store_admission_and_atomicity_certification.py",
        "oml_014_fixture_for_oml_015",
    )

    store_contract = fixture.build_oml_013_contract(root)

    return build_oracle_memory_store_admission_atomicity_certification(
        store_contract=store_contract,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryAppendOnlyLedgerInvariantError:
        return

    raise AssertionError(f"tampered OML-015 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-015 TEST")
    print(" APPEND-ONLY MEMORY LEDGER CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    store_certification = build_oml_014_certification(root)

    certification = (
        build_oracle_memory_append_only_ledger_contract_certification(
            store_certification=store_certification,
        )
    )

    assert certification.schema_version == "OML-015"
    assert certification.engine_id == "OML-015"
    assert certification.upstream_schema_version == "OML-014"
    assert certification.upstream_engine_id == "OML-014"
    assert certification.upstream_certification_hash == (
        store_certification.certification_hash
    )
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.entry_contract_count == 8
    assert certification.ledger_mode == "append_only"
    assert certification.ledger_state == "contract_only"
    assert certification.commit_model == "atomic_single_commit"
    assert certification.replay_model == "genesis_to_head"
    assert certification.genesis_parent_hash == GENESIS_PARENT_HASH
    assert certification.monotonic_sequence_required
    assert certification.previous_hash_chain_required
    assert certification.genesis_anchor_required
    assert certification.atomic_commit_required
    assert certification.rollback_on_failure_required
    assert certification.partial_commit_forbidden
    assert certification.duplicate_record_hashes_forbidden
    assert certification.immutable_after_commit_required
    assert certification.destructive_updates_forbidden
    assert certification.deletes_forbidden
    assert certification.full_replay_required
    assert certification.lineage_preservation_required
    assert not certification.persistence_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.database_access_enabled
    assert not certification.networking_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled
    assert certification.contract_ready
    assert certification.next_certification_authorized
    assert certification.read_only

    for index, entry in enumerate(
        certification.entry_contracts,
        start=1,
    ):
        assert entry.domain_id == MEMORY_DOMAINS[index - 1]
        assert entry.ordinal == index
        assert entry.sequence_number == 1
        assert entry.previous_entry_hash == GENESIS_PARENT_HASH
        assert entry.append_only_required
        assert entry.immutable_after_commit
        assert entry.deterministic_sequence_required
        assert entry.previous_hash_link_required
        assert entry.record_hash_uniqueness_required
        assert not entry.destructive_update_allowed
        assert not entry.delete_allowed
        assert not entry.persistence_authorized
        assert not entry.learning_update_authorized
        assert not entry.runtime_activation_authorized
        assert not entry.publication_authorized
        assert not entry.action_authorization_enabled
        assert not entry.qseries_execution_authorized
        assert entry.read_only

    replay = (
        build_oracle_memory_append_only_ledger_contract_certification(
            store_certification=store_certification,
        )
    )

    assert replay == certification
    assert verify_oracle_memory_append_only_ledger_contract_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, previous_hash_chain_required=False)
        ),
        "hash-chain guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, partial_commit_forbidden=False)
        ),
        "partial commit boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_append_only_ledger_contract_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-014 store certification consumed")
    print("[PASS] OML-014 through OIT-050 lineage retained")
    print("[PASS] Append-only ledger contract created")
    print("[PASS] Eight domain ledger-entry contracts defined")
    print("[PASS] Genesis anchors defined")
    print("[PASS] Monotonic sequence numbers required")
    print("[PASS] Previous-entry hash chaining required")
    print("[PASS] Deterministic entry hashing required")
    print("[PASS] Atomic commit and rollback required")
    print("[PASS] Partial commits forbidden")
    print("[PASS] Duplicate record hashes forbidden")
    print("[PASS] Destructive updates and deletes forbidden")
    print("[PASS] Full genesis-to-head replay required")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered ledger certifications rejected")
    print("[DONE] OML-015 APPEND-ONLY MEMORY LEDGER CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
