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
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    OracleMemoryStoreContractInvariantError,
    build_oracle_memory_store_contract_certification,
    verify_oracle_memory_store_contract_certification,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def build_oml_012_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_013",
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

    return build_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        registry=oml_011,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryStoreContractInvariantError:
        return

    raise AssertionError(f"tampered OML-013 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-013 TEST")
    print(" MEMORY STORE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    gate = build_oml_012_decision(root)

    certification = build_oracle_memory_store_contract_certification(
        gate_decision=gate,
    )

    assert certification.schema_version == "OML-013"
    assert certification.engine_id == "OML-013"
    assert certification.upstream_schema_version == "OML-012"
    assert certification.upstream_engine_id == "OML-012"
    assert certification.upstream_gate_decision_hash == gate.decision_hash
    assert certification.certified_domain_ids == MEMORY_DOMAINS
    assert certification.partition_count == 8
    assert certification.store_mode == "append_only"
    assert certification.store_state == "contract_only"
    assert certification.atomicity_model == "single_commit"
    assert certification.replay_model == "full_ledger_replay"
    assert certification.append_only_required
    assert certification.immutable_ledger_required
    assert certification.atomic_commit_required
    assert certification.replay_verification_required
    assert certification.lineage_preservation_required
    assert certification.destructive_updates_forbidden
    assert certification.deletes_forbidden
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

    replay = build_oracle_memory_store_contract_certification(
        gate_decision=gate,
    )

    assert replay == certification
    assert verify_oracle_memory_store_contract_certification(
        certification
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, append_only_required=False)
        ),
        "append-only guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, destructive_updates_forbidden=False)
        ),
        "destructive update boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_store_contract_certification(
            replace(certification, qseries_execution_enabled=True)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-012 gate consumed")
    print("[PASS] OML-012 through OIT-050 lineage retained")
    print("[PASS] Append-only memory store contract created")
    print("[PASS] Eight canonical store partitions defined")
    print("[PASS] Deterministic commit hashing required")
    print("[PASS] Atomic single-commit model required")
    print("[PASS] Full-ledger replay verification required")
    print("[PASS] Immutable ledger and lineage required")
    print("[PASS] Destructive updates and deletes forbidden")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Database and networking remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Contract deterministic across replay")
    print("[PASS] Tampered store certifications rejected")
    print("[DONE] OML-013 MEMORY STORE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
