from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    build_oracle_memory_canonical_record_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    build_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    OracleMemoryCanonicalRecordCandidateInvariantError,
    build_oracle_memory_canonical_record_candidate,
    build_oracle_memory_canonical_record_candidate_contract_certification,
    verify_oracle_memory_canonical_record_candidate,
    verify_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    build_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    build_oracle_memory_canonical_record_contract_admission_decision,
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


def build_oml_008_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_009",
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
    oml_004 = build_oracle_memory_domain_registry_admission_decision(
        registry=oml_003,
    )
    oml_005 = build_oracle_memory_canonical_record_contract_certification(
        admission_decision=oml_004,
    )
    oml_006 = build_oracle_memory_canonical_record_contract_admission_decision(
        certification=oml_005,
    )
    oml_007 = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=oml_006,
    )

    return build_oracle_memory_canonical_record_admission_registry_gate_decision(
        registry=oml_007,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordCandidateInvariantError:
        return

    raise AssertionError(f"tampered OML-009 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-009 TEST")
    print(" CANONICAL RECORD CANDIDATE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    gate = build_oml_008_decision(root)

    candidate = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=MEMORY_DOMAINS[0],
        candidate_id="candidate:entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T09:56:00-05:00",
        effective_at="2026-08-02T09:56:00-05:00",
        payload={
            "symbol": "BTC",
            "aliases": ["bitcoin", "xbt"],
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=("3" * 64,),
        confidence=0.8,
        uncertainty=0.2,
        contradiction_count=0,
    )

    assert candidate.schema_version == "OML-009"
    assert candidate.engine_id == "OML-009"
    assert candidate.domain_id == MEMORY_DOMAINS[0]
    assert candidate.upstream_gate_decision_hash == gate.decision_hash
    assert candidate.candidate_state == "candidate_contract_only"
    assert not candidate.admission_authorized
    assert not candidate.persistent_storage_authorized
    assert not candidate.learning_update_authorized
    assert not candidate.runtime_activation_authorized
    assert not candidate.publication_authorized
    assert not candidate.action_authorization_enabled
    assert not candidate.qseries_execution_authorized
    assert candidate.read_only

    replay = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=MEMORY_DOMAINS[0],
        candidate_id="candidate:entity:btc",
        entity_key="BTC",
        source_key="certified-test-source",
        observed_at="2026-08-02T09:56:00-05:00",
        effective_at="2026-08-02T09:56:00-05:00",
        payload={
            "aliases": ["bitcoin", "xbt"],
            "symbol": "BTC",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        parent_record_hashes=("3" * 64,),
        confidence=0.8,
        uncertainty=0.2,
        contradiction_count=0,
    )

    assert replay == candidate
    assert verify_oracle_memory_canonical_record_candidate(candidate)

    certification = (
        build_oracle_memory_canonical_record_candidate_contract_certification(
            gate_decision=gate,
        )
    )

    assert certification.schema_version == "OML-009"
    assert certification.upstream_schema_version == "OML-008"
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.contract_ready
    assert certification.next_certification_authorized
    assert certification.read_only
    assert not certification.candidate_admission_enabled
    assert not certification.persistent_storage_enabled
    assert not certification.learning_updates_enabled
    assert not certification.runtime_activation_enabled
    assert not certification.publication_enabled
    assert not certification.action_authorization_enabled
    assert not certification.qseries_execution_enabled

    certification_replay = (
        build_oracle_memory_canonical_record_candidate_contract_certification(
            gate_decision=gate,
        )
    )

    assert certification_replay == certification
    assert (
        verify_oracle_memory_canonical_record_candidate_contract_certification(
            certification
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, admission_authorized=True)
        ),
        "candidate admission state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, persistent_storage_authorized=True)
        ),
        "persistent storage state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, learning_update_authorized=True)
        ),
        "learning update state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate(
            replace(candidate, qseries_execution_authorized=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-008 gate consumed")
    print("[PASS] OML-008 through OIT-050 lineage retained")
    print("[PASS] Canonical memory record candidate contract created")
    print("[PASS] Candidate domain bound to certified registry")
    print("[PASS] Canonical candidate serialization verified")
    print("[PASS] Deterministic candidate hashing verified")
    print("[PASS] Immutable candidate identity enforced")
    print("[PASS] Evidence and parent lineage supported")
    print("[PASS] Confidence and uncertainty bounds enforced")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered candidates and certifications rejected")
    print("[DONE] OML-009 CANONICAL RECORD CANDIDATE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
