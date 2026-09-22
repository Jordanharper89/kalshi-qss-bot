from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    REGISTRY_STATUS_CERTIFIED,
    OracleMemoryDomainRegistryInvariantError,
    build_oracle_memory_certified_domain_registry,
    verify_oracle_memory_certified_domain_registry,
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


def build_oml_002_decision(root: Path):
    fixture = load_module(
        root
        / "test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        "oit_050_fixture_for_oml_003",
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

    return build_oracle_memory_learner_foundation_admission_decision(
        root,
        foundation_report=oml_001,
    )


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryDomainRegistryInvariantError:
        return

    raise AssertionError(f"tampered OML-003 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-003 TEST")
    print(" CERTIFIED MEMORY DOMAIN REGISTRY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    admission = build_oml_002_decision(root)

    registry = build_oracle_memory_certified_domain_registry(
        admission_decision=admission,
    )

    assert registry.schema_version == "OML-003"
    assert registry.engine_id == "OML-003"
    assert registry.upstream_schema_version == "OML-002"
    assert registry.upstream_engine_id == "OML-002"
    assert registry.upstream_decision_hash == admission.decision_hash
    assert registry.upstream_foundation_report_hash == (
        admission.upstream_report_hash
    )
    assert registry.upstream_oit_report_hash == (
        admission.upstream_oit_report_hash
    )
    assert registry.upstream_oit_runner_sha256 == (
        admission.upstream_oit_runner_sha256
    )

    assert registry.registry_status == REGISTRY_STATUS_CERTIFIED
    assert registry.domain_count == 8
    assert tuple(item.domain_id for item in registry.domains) == MEMORY_DOMAINS
    assert registry.registry_complete
    assert registry.domain_order_canonical
    assert registry.identities_unique
    assert registry.all_domains_inactive
    assert registry.all_domains_non_writing
    assert registry.all_domains_read_only
    assert registry.no_database_access_authorized
    assert registry.no_networking_authorized
    assert registry.publication_disabled
    assert registry.action_authorization_disabled
    assert registry.qseries_execution_disabled
    assert registry.next_certification_authorized

    for index, definition in enumerate(registry.domains, start=1):
        assert definition.ordinal == index
        assert definition.domain_id == MEMORY_DOMAINS[index - 1]
        assert definition.domain_kind == "memory"
        assert not definition.persistent_storage_authorized
        assert not definition.learning_update_authorized
        assert not definition.runtime_activation_authorized
        assert not definition.database_access_authorized
        assert not definition.networking_authorized
        assert not definition.publication_authorized
        assert not definition.action_authorization_enabled
        assert not definition.qseries_execution_authorized
        assert definition.read_only

    replay = build_oracle_memory_certified_domain_registry(
        admission_decision=admission,
    )

    assert replay == registry
    assert verify_oracle_memory_certified_domain_registry(registry)

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, domain_count=7)
        ),
        "domain count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, all_domains_non_writing=False)
        ),
        "non-writing guarantee",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, publication_disabled=False)
        ),
        "publication boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_domain_registry(
            replace(registry, qseries_execution_disabled=False)
        ),
        "Q Series execution boundary",
    )

    print("[PASS] Certified OML-002 admission decision consumed")
    print("[PASS] OML-002 identity and lineage retained")
    print("[PASS] Eight production memory domains registered")
    print("[PASS] Domain identities unique and canonically ordered")
    print("[PASS] Domain definitions deterministic across replay")
    print("[PASS] Every domain remained inactive")
    print("[PASS] Persistent storage remained unauthorized")
    print("[PASS] Learning updates remained unauthorized")
    print("[PASS] Database and networking remained unauthorized")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Every domain remained read-only")
    print("[PASS] Tampered registry states rejected")
    print("[DONE] OML-003 CERTIFIED MEMORY DOMAIN REGISTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
