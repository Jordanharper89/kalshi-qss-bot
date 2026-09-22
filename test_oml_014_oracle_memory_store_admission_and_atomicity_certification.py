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
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry import (
    build_oracle_memory_canonical_record_candidate_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry_gate import (
    build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate_contract_certification,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract_admission_gate import (
    build_oracle_memory_canonical_record_candidate_contract_admission_decision,
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
from qseries_v2.oracle_memory.oracle_memory_store_admission_and_atomicity_certification import (
    OracleMemoryStoreAdmissionAtomicityInvariantError,
    build_oracle_memory_store_admission_atomicity_certification,
    verify_oracle_memory_store_admission_atomicity_certification,
)
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    build_oracle_memory_store_contract_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_013_contract(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_014",
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
    oml_008 = build_oracle_memory_canonical_record_admission_registry_gate_decision(
        registry=oml_007,
    )
    oml_009 = build_oracle_memory_canonical_record_candidate_contract_certification(
        gate_decision=oml_008,
    )
    oml_010 = build_oracle_memory_canonical_record_candidate_contract_admission_decision(
        certification=oml_009,
    )
    oml_011 = build_oracle_memory_canonical_record_candidate_admission_registry(
        admission_decision=oml_010,
    )
    oml_012 = build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        registry=oml_011,
    )

    return build_oracle_memory_store_contract_certification(
        gate_decision=oml_012,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryStoreAdmissionAtomicityInvariantError:
        return

    raise AssertionError(f"tampered OML-014 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-014 TEST")
    print(" STORE ADMISSION AND ATOMICITY CERTIFICATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    store_contract = build_oml_013_contract(root)

    certification = (
        build_oracle_memory_store_admission_atomicity_certification(
            store_contract=store_contract,
        )
    )

    assert certification.schema_version == "OML-014"
    assert certification.engine_id == "OML-014"
    assert certification.upstream_schema_version == "OML-013"
    assert certification.upstream_engine_id == "OML-013"
    assert certification.upstream_certification_hash == (
        store_contract.certification_hash
    )
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.partition_count == 8
    assert certification.admission_status == "certified"
    assert (
        certification.atomicity_status
        == "single_commit_atomicity_certified"
    )
    assert certification.append_only_admitted
    assert certification.deterministic_commit_hashing_admitted
    assert certification.immutable_ledger_admitted
    assert certification.atomic_single_commit_admitted
    assert certification.full_replay_admitted
    assert certification.lineage_preservation_admitted
    assert certification.duplicate_record_rejection_admitted
    assert certification.destructive_updates_rejected
    assert certification.deletes_rejected
    assert certification.rollback_on_failure_required
    assert certification.partial_commit_forbidden
    assert certification.commit_order_canonical
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

    replay = build_oracle_memory_store_admission_atomicity_certification(
        store_contract=store_contract,
    )

    assert replay == certification
    assert verify_oracle_memory_store_admission_atomicity_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, atomic_single_commit_admitted=False)
        ),
        "atomicity guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, partial_commit_forbidden=False)
        ),
        "partial commit boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_admission_atomicity_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-013 store contract consumed")
    print("[PASS] OML-013 through OIT-050 lineage retained")
    print("[PASS] Eight store partitions admitted")
    print("[PASS] Append-only store architecture admitted")
    print("[PASS] Deterministic commit hashing admitted")
    print("[PASS] Atomic single-commit model certified")
    print("[PASS] Rollback on failure required")
    print("[PASS] Partial commits forbidden")
    print("[PASS] Full-ledger replay admitted")
    print("[PASS] Immutable lineage admitted")
    print("[PASS] Destructive updates and deletes rejected")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Certification deterministic across replay")
    print("[PASS] Tampered certifications rejected")
    print("[DONE] OML-014 STORE ADMISSION AND ATOMICITY CERTIFICATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
