from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    REGISTRY_STATUS_CERTIFIED,
    OracleMemoryCanonicalRecordAdmissionRegistryInvariantError,
    build_oracle_memory_canonical_record_admission_registry,
    verify_oracle_memory_canonical_record_admission_registry,
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


def build_oml_006_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_007",
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

    return build_oracle_memory_canonical_record_contract_admission_decision(
        certification=oml_005,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCanonicalRecordAdmissionRegistryInvariantError:
        return

    raise AssertionError(f"tampered OML-007 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-007 TEST")
    print(" CANONICAL RECORD ADMISSION REGISTRY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    admission = build_oml_006_decision(root)

    registry = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=admission,
    )

    assert registry.schema_version == "OML-007"
    assert registry.engine_id == "OML-007"
    assert registry.upstream_schema_version == "OML-006"
    assert registry.upstream_engine_id == "OML-006"
    assert registry.upstream_decision_hash == admission.decision_hash
    assert registry.entry_count == 8
    assert tuple(entry.domain_id for entry in registry.entries) == (
        MEMORY_DOMAINS
    )
    assert registry.registry_status == REGISTRY_STATUS_CERTIFIED
    assert registry.domain_order_canonical
    assert registry.identities_unique
    assert registry.all_contracts_admitted
    assert registry.all_entries_inactive
    assert registry.all_entries_non_writing
    assert registry.all_entries_read_only
    assert registry.publication_disabled
    assert registry.action_authorization_disabled
    assert registry.qseries_execution_disabled
    assert registry.next_certification_authorized

    for index, entry in enumerate(registry.entries, start=1):
        assert entry.ordinal == index
        assert entry.domain_id == MEMORY_DOMAINS[index - 1]
        assert entry.upstream_contract_admission_hash == (
            admission.decision_hash
        )
        assert entry.canonical_record_contract_admitted
        assert not entry.persistent_storage_authorized
        assert not entry.learning_update_authorized
        assert not entry.runtime_activation_authorized
        assert not entry.publication_authorized
        assert not entry.action_authorization_enabled
        assert not entry.qseries_execution_authorized
        assert entry.read_only

    replay = build_oracle_memory_canonical_record_admission_registry(
        admission_decision=admission,
    )

    assert replay == registry
    assert verify_oracle_memory_canonical_record_admission_registry(
        registry
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, entry_count=7)
        ),
        "entry count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, all_entries_non_writing=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, publication_disabled=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_canonical_record_admission_registry(
            replace(registry, qseries_execution_disabled=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-006 admission consumed")
    print("[PASS] OML-006 through OIT-050 lineage retained")
    print("[PASS] Eight canonical record admissions registered")
    print("[PASS] Domain identities unique and canonically ordered")
    print("[PASS] Every record contract remained admitted")
    print("[PASS] Every registry entry remained inactive")
    print("[PASS] Persistent storage remained unauthorized")
    print("[PASS] Learning updates remained unauthorized")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Registry deterministic across replay")
    print("[PASS] Tampered registry states rejected")
    print("[DONE] OML-007 CANONICAL RECORD ADMISSION REGISTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
