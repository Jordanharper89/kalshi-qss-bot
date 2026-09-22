from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    build_oracle_memory_canonical_record_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    GATE_STATUS_ADMITTED,
    OracleMemoryCanonicalRecordAdmissionRegistryGateInvariantError,
    build_oracle_memory_canonical_record_admission_registry_gate_decision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
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


def build_oml_007_registry(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_008",
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

    return build_oracle_memory_canonical_record_admission_registry(
        admission_decision=oml_006,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordAdmissionRegistryGateInvariantError:
        return

    raise AssertionError(f"tampered OML-008 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-008 TEST")
    print(" CANONICAL RECORD ADMISSION REGISTRY GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    registry = build_oml_007_registry(root)

    decision = (
        build_oracle_memory_canonical_record_admission_registry_gate_decision(
            registry=registry,
        )
    )

    assert decision.schema_version == "OML-008"
    assert decision.engine_id == "OML-008"
    assert decision.upstream_schema_version == "OML-007"
    assert decision.upstream_engine_id == "OML-007"
    assert decision.upstream_registry_hash == registry.registry_hash
    assert decision.admitted_domain_ids == MEMORY_DOMAINS
    assert decision.admitted_entry_count == 8
    assert decision.admitted_entry_hashes == tuple(
        entry.entry_hash for entry in registry.entries
    )

    assert decision.registry_verified
    assert decision.registry_status_verified
    assert decision.upstream_identity_verified
    assert decision.upstream_lineage_verified
    assert decision.domain_count_verified
    assert decision.domain_order_verified
    assert decision.domain_uniqueness_verified
    assert decision.entry_hashes_verified
    assert decision.contracts_admitted_verified
    assert decision.entries_inactive_verified
    assert decision.entries_non_writing_verified
    assert decision.entries_read_only_verified
    assert decision.persistent_storage_disabled_verified
    assert decision.learning_updates_disabled_verified
    assert decision.runtime_activation_disabled_verified
    assert decision.publication_disabled_verified
    assert decision.action_authorization_disabled_verified
    assert decision.qseries_execution_disabled_verified
    assert decision.upstream_continuation_authorized
    assert decision.gate_status == GATE_STATUS_ADMITTED
    assert decision.admitted
    assert decision.next_certification_authorized
    assert decision.read_only
    assert decision.failure_reason is None

    replay = (
        build_oracle_memory_canonical_record_admission_registry_gate_decision(
            registry=registry,
        )
    )

    assert replay == decision
    assert (
        verify_oracle_memory_canonical_record_admission_registry_gate_decision(
            decision
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry_gate_decision(
            replace(decision, admitted_entry_count=7)
        ),
        "entry count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry_gate_decision(
            replace(decision, entries_non_writing_verified=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry_gate_decision(
            replace(decision, publication_disabled_verified=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry_gate_decision(
            replace(decision, qseries_execution_disabled_verified=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-007 registry consumed")
    print("[PASS] OML-007 through OIT-050 lineage retained")
    print("[PASS] Eight record-admission entries admitted")
    print("[PASS] Domain order and entry hashes admitted")
    print("[PASS] Every canonical record contract remained admitted")
    print("[PASS] Every registry entry remained inactive")
    print("[PASS] Persistent storage remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Gate deterministic across replay")
    print("[PASS] Tampered gate decisions rejected")
    print("[DONE] OML-008 CANONICAL RECORD ADMISSION REGISTRY GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
