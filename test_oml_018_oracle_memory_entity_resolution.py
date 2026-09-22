from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionInvariantError,
    build_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_entity_resolution_batch,
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
    except OracleMemoryEntityResolutionInvariantError:
        return

    raise AssertionError(f"tampered OML-018 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-018 TEST")
    print(" ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_018",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_018",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:btc:001",
        entity_key="Bitcoin",
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

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate, candidate),
    )

    batch = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate.candidate_hash: (
                "BTC",
                "Bitcoin",
                "XBT",
            )
        },
    )

    assert batch.schema_version == "OML-018"
    assert batch.engine_id == "OML-018"
    assert batch.upstream_schema_version == "OML-017"
    assert batch.upstream_engine_id == "OML-017"
    assert batch.resolved_entity_count == 1
    assert batch.rejected_duplicate_count == 1

    entity = batch.entities[0]

    assert entity.canonical_name == "Bitcoin"
    assert entity.normalized_name == "bitcoin"
    assert tuple(
        alias.normalized_alias for alias in entity.aliases
    ) == ("bitcoin", "btc", "xbt")
    assert entity.resolution_status == "resolved"
    assert entity.deterministic_identity_verified
    assert entity.alias_uniqueness_verified
    assert entity.canonical_name_verified
    assert entity.duplicate_candidate_rejected
    assert not entity.persistence_authorized
    assert not entity.learning_update_authorized
    assert not entity.runtime_activation_authorized
    assert not entity.publication_authorized
    assert not entity.action_authorization_enabled
    assert not entity.qseries_execution_authorized
    assert entity.read_only

    assert batch.canonical_order_verified
    assert batch.deterministic_resolution_verified
    assert batch.alias_normalization_verified
    assert batch.entity_identity_uniqueness_verified
    assert batch.duplicate_candidates_excluded
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.batch_ready
    assert batch.next_certification_authorized
    assert batch.read_only

    replay = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate.candidate_hash: (
                "XBT",
                "Bitcoin",
                "BTC",
            )
        },
    )

    assert replay == batch
    assert verify_oracle_memory_entity_resolution_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, resolved_entity_count=2)
        ),
        "entity count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_entity_resolution_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-017 validation batch consumed")
    print("[PASS] Valid candidates resolved to canonical entities")
    print("[PASS] Duplicate candidates excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Alias normalization completed")
    print("[PASS] Alias uniqueness verified")
    print("[PASS] Canonical entity ordering verified")
    print("[PASS] Entity resolution deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered entity batches rejected")
    print("[DONE] OML-018 ENTITY RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
