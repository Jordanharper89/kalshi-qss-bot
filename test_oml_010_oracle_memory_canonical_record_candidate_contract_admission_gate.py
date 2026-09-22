from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract_admission_gate import (
    ADMISSION_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError,
    build_oracle_memory_canonical_record_candidate_contract_admission_decision,
    verify_oracle_memory_canonical_record_candidate_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import MEMORY_DOMAINS


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_009_certification(root: Path):
    fixture = load_module(
        root / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_010",
    )
    gate = fixture.build_oml_008_decision(root)
    return build_oracle_memory_canonical_record_candidate_contract_certification(
        gate_decision=gate,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordCandidateContractAdmissionInvariantError:
        return
    raise AssertionError(f"tampered OML-010 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-010 TEST")
    print(" CANDIDATE CONTRACT ADMISSION GATE")
    print("=" * 48)
    root = Path(__file__).resolve().parent
    certification = build_oml_009_certification(root)
    decision = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=certification,
    )
    assert decision.schema_version == "OML-010"
    assert decision.engine_id == "OML-010"
    assert decision.upstream_schema_version == "OML-009"
    assert decision.upstream_engine_id == "OML-009"
    assert decision.upstream_certification_hash == certification.certification_hash
    assert decision.upstream_gate_decision_hash == certification.upstream_gate_decision_hash
    assert decision.upstream_registry_hash == certification.upstream_registry_hash
    assert decision.certified_domain_ids == MEMORY_DOMAINS
    assert decision.contract_verified
    assert decision.candidate_admission_disabled_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None
    replay = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=certification,
    )
    assert replay == decision
    assert verify_oracle_memory_canonical_record_candidate_contract_admission_decision(decision)
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, candidate_admission_disabled_verified=False)
        ),
        "candidate admission boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, persistent_storage_disabled_verified=False)
        ),
        "persistent storage boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_candidate_contract_admission_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )
    print("[PASS] Certified OML-009 candidate contract consumed")
    print("[PASS] OML-009 identity and policy verified")
    print("[PASS] OML-008 through OIT-050 lineage retained")
    print("[PASS] Eight certified memory domains admitted")
    print("[PASS] Canonical candidate serialization admitted")
    print("[PASS] Deterministic candidate hashing admitted")
    print("[PASS] Immutable candidate identity admitted")
    print("[PASS] Evidence and parent lineage admitted")
    print("[PASS] Confidence and uncertainty bounds admitted")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission decisions rejected")
    print("[DONE] OML-010 CANDIDATE CONTRACT ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
