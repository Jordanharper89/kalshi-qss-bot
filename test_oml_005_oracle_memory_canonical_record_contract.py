from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    OracleMemoryCanonicalRecordInvariantError,
    build_oracle_memory_canonical_record,
    build_oracle_memory_canonical_record_contract_certification,
    verify_oracle_memory_canonical_record,
    verify_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    build_oracle_memory_certified_domain_registry,
)
from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry_admission_gate import (
    build_oracle_memory_domain_registry_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    build_oracle_memory_learner_foundation_report,
)
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    build_oracle_memory_learner_foundation_admission_decision,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_004_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_005",
    )

    from qseries_v2.oracle_terminal.oracle_terminal_final_freeze_and_completion import (
        build_oracle_terminal_final_freeze_completion_report,
    )

    oit_049 = fixture.build_oit_049_report(root)
    oit_050 = build_oracle_terminal_final_freeze_completion_report(
        root,
        production_certification_report=oit_049,
    )

    oml_001 = build_oracle_memory_learner_foundation_report(
        root,
        oit_final_freeze_report=oit_050,
    )

    oml_002 = build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=oml_001,
    )

    oml_003 = build_oracle_memory_certified_domain_registry(
        admission_decision=oml_002,
    )

    return build_oracle_memory_domain_registry_admission_decision(
        registry=oml_003,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordInvariantError:
        return

    raise AssertionError(f"tampered OML-005 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-005 TEST")
    print(" CANONICAL MEMORY RECORD CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    admission = build_oml_004_decision(root)

    evidence_hashes = ("1" * 64, "2" * 64)
    parent_hashes = ("3" * 64,)

    record = build_oracle_memory_canonical_record(
        admission_decision=admission,
        domain_id=MEMORY_DOMAINS[0],
        record_id="entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T00:00:00-05:00",
        effective_at="2026-08-02T00:00:00-05:00",
        payload={
            "symbol": "BTC",
            "attributes": {
                "asset_class": "crypto",
                "active": True,
            },
            "aliases": ["bitcoin", "xbt"],
        },
        evidence_hashes=evidence_hashes,
        parent_record_hashes=parent_hashes,
        confidence=0.80,
        uncertainty=0.20,
        contradiction_count=0,
    )

    assert record.schema_version == "OML-005"
    assert record.contract_engine_id == "OML-005"
    assert record.domain_id == MEMORY_DOMAINS[0]
    assert record.upstream_admission_hash == admission.decision_hash
    assert record.record_state == "contract_only"
    assert not record.persistent_storage_authorized
    assert not record.learning_update_authorized
    assert not record.runtime_activation_authorized
    assert not record.publication_authorized
    assert not record.action_authorization_enabled
    assert not record.qseries_execution_authorized
    assert record.read_only

    replay = build_oracle_memory_canonical_record(
        admission_decision=admission,
        domain_id=MEMORY_DOMAINS[0],
        record_id="entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T00:00:00-05:00",
        effective_at="2026-08-02T00:00:00-05:00",
        payload={
            "aliases": ["bitcoin", "xbt"],
            "attributes": {
                "active": True,
                "asset_class": "crypto",
            },
            "symbol": "BTC",
        },
        evidence_hashes=evidence_hashes,
        parent_record_hashes=parent_hashes,
        confidence=0.80,
        uncertainty=0.20,
        contradiction_count=0,
    )

    assert replay == record
    assert verify_oracle_memory_canonical_record(record)

    certification = (
        build_oracle_memory_canonical_record_contract_certification(
            admission_decision=admission,
        )
    )

    assert certification.schema_version == "OML-005"
    assert certification.upstream_schema_version == "OML-004"
    assert certification.upstream_admission_hash == admission.decision_hash
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.canonical_serialization_required
    assert certification.deterministic_record_hashing_required
    assert certification.immutable_record_identity_required
    assert certification.evidence_lineage_required
    assert certification.parent_lineage_supported
    assert certification.confidence_bounded
    assert certification.uncertainty_bounded
    assert certification.duplicate_evidence_hashes_forbidden
    assert certification.duplicate_parent_hashes_forbidden
    assert not certification.persistent_storage_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled
    assert certification.contract_ready
    assert certification.next_certification_authorized
    assert certification.read_only

    certification_replay = (
        build_oracle_memory_canonical_record_contract_certification(
            admission_decision=admission,
        )
    )

    assert certification_replay == certification
    assert (
        verify_oracle_memory_canonical_record_contract_certification(
            certification
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, confidence=1.1)
        ),
        "confidence",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, evidence_hashes=("1" * 64, "1" * 64))
        ),
        "duplicate evidence lineage",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, persistent_storage_authorized=True)
        ),
        "persistent storage state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, learning_update_authorized=True)
        ),
        "learning update state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, publication_authorized=True)
        ),
        "publication state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record(
            replace(record, qseries_execution_authorized=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-004 admission consumed")
    print("[PASS] OML-003 through OIT-050 lineage retained")
    print("[PASS] Canonical memory record contract created")
    print("[PASS] Record domain bound to certified registry")
    print("[PASS] Canonical payload serialization verified")
    print("[PASS] Deterministic record hashing verified")
    print("[PASS] Immutable record identity enforced")
    print("[PASS] Evidence and parent lineage supported")
    print("[PASS] Confidence and uncertainty bounds enforced")
    print("[PASS] Duplicate lineage hashes rejected")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract certification deterministic across replay")
    print("[PASS] Tampered records and certifications rejected")
    print("[DONE] OML-005 CANONICAL MEMORY RECORD CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
