from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationInvariantError,
    build_oracle_memory_candidate_validation_batch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCandidateValidationInvariantError:
        return
    raise AssertionError(f"tampered OML-017 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-017 TEST")
    print(" CANDIDATE VALIDATION AND DEDUPLICATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_017",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_017",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:observation:btc:001",
        entity_key="BTC",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={
            "observation": (
                "Real-world activity changed before market reaction"
            ),
            "observation_type": "consumer_behavior",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        contradiction_count=0,
    )

    batch = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate, candidate),
    )

    assert batch.schema_version == "OML-017"
    assert batch.candidate_count == 2
    assert batch.unique_candidate_count == 1
    assert batch.duplicate_candidate_count == 1
    assert batch.results[0].status == "valid"
    assert batch.results[1].status == "duplicate"
    assert batch.results[1].duplicate_detected
    assert batch.results[1].duplicate_of_candidate_hash == (
        candidate.candidate_hash
    )
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.batch_ready
    assert batch.next_certification_authorized
    assert batch.read_only

    replay = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate, candidate),
    )
    assert replay == batch
    assert verify_oracle_memory_candidate_validation_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_candidate_validation_batch(
            replace(batch, duplicate_candidate_count=0)
        ),
        "duplicate count",
    )
    expect_rejection(
        lambda: verify_oracle_memory_candidate_validation_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_candidate_validation_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-016 ledger certification consumed")
    print("[PASS] Canonical OML-009 candidate contract consumed")
    print("[PASS] Candidate identity and domain validated")
    print("[PASS] Evidence and parent lineage validated")
    print("[PASS] Confidence and uncertainty bounds validated")
    print("[PASS] Deterministic candidate ordering verified")
    print("[PASS] Duplicate candidate detected")
    print("[PASS] Duplicate persistence remained forbidden")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Validation deterministic across replay")
    print("[PASS] Tampered validation batches rejected")
    print("[DONE] OML-017 CANDIDATE VALIDATION AND DEDUPLICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
