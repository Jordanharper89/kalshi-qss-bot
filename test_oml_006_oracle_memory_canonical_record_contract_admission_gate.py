from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract import (
    build_oracle_memory_canonical_record_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    ADMISSION_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordContractAdmissionInvariantError,
    build_oracle_memory_canonical_record_contract_admission_decision,
    verify_oracle_memory_canonical_record_contract_admission_decision,
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


def build_oml_005_certification(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_006",
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

    return build_oracle_memory_canonical_record_contract_certification(
        admission_decision=oml_004,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordContractAdmissionInvariantError:
        return

    raise AssertionError(f"tampered OML-006 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-006 TEST")
    print(" CANONICAL RECORD CONTRACT ADMISSION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    certification = build_oml_005_certification(root)

    decision = (
        build_oracle_memory_canonical_record_contract_admission_decision(
            certification=certification,
        )
    )

    assert decision.schema_version == "OML-006"
    assert decision.engine_id == "OML-006"
    assert decision.upstream_schema_version == "OML-005"
    assert decision.upstream_engine_id == "OML-005"
    assert decision.upstream_certification_hash == (
        certification.certification_hash
    )
    assert decision.upstream_admission_hash == (
        certification.upstream_admission_hash
    )
    assert decision.upstream_registry_hash == (
        certification.upstream_registry_hash
    )
    assert decision.certified_domain_ids == MEMORY_DOMAINS

    assert decision.contract_verified
    assert decision.upstream_identity_verified
    assert decision.upstream_lineage_verified
    assert decision.canonical_serialization_verified
    assert decision.deterministic_hashing_verified
    assert decision.immutable_identity_verified
    assert decision.evidence_lineage_verified
    assert decision.parent_lineage_verified
    assert decision.confidence_bounds_verified
    assert decision.uncertainty_bounds_verified
    assert decision.duplicate_evidence_rejection_verified
    assert decision.duplicate_parent_rejection_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.upstream_continuation_authorized
    assert decision.admission_status == ADMISSION_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None

    replay = (
        build_oracle_memory_canonical_record_contract_admission_decision(
            certification=certification,
        )
    )

    assert replay == decision
    assert (
        verify_oracle_memory_canonical_record_contract_admission_decision(
            decision
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, canonical_serialization_verified=False)
        ),
        "canonical serialization guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, persistent_storage_disabled_verified=False)
        ),
        "persistent storage boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, learning_updates_disabled_verified=False)
        ),
        "learning update boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, publication_disabled_verified=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_contract_admission_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-005 contract consumed")
    print("[PASS] OML-005 identity and policy verified")
    print("[PASS] OML-004 through OIT-050 lineage retained")
    print("[PASS] Eight certified memory domains admitted")
    print("[PASS] Canonical serialization contract admitted")
    print("[PASS] Deterministic record hashing admitted")
    print("[PASS] Immutable record identity admitted")
    print("[PASS] Evidence and parent lineage admitted")
    print("[PASS] Confidence and uncertainty bounds admitted")
    print("[PASS] Duplicate lineage rejection admitted")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission decisions rejected")
    print("[DONE] OML-006 CANONICAL RECORD CONTRACT ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
