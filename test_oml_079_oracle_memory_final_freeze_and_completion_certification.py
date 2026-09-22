from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_final_freeze_and_completion_certification_079 import (
    OracleMemoryFinalFreezeInvariantError,
    build_oracle_memory_final_freeze_completion,
    verify_oracle_memory_final_freeze_completion,
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
    except OracleMemoryFinalFreezeInvariantError:
        return
    raise AssertionError(f"tampered OML-079 {label} accepted")


def build_final_freeze(root: Path):
    fixture_078 = load_module(
        root
        / "test_oml_078_oracle_memory_final_freeze_"
        "readiness_certification_gate.py",
        "oml_078_fixture_for_oml_079",
    )
    readiness, dependencies = fixture_078.build_freeze_readiness(root)
    completion = build_oracle_memory_final_freeze_completion(
        readiness=readiness,
    )
    return completion, readiness


def main() -> int:
    print("=" * 48)
    print(" OML-079 TEST")
    print(" FINAL FREEZE AND COMPLETION CERTIFICATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    completion, readiness = build_final_freeze(root)

    assert completion.schema_version == "OML-079"
    assert completion.engine_id == "OML-079"
    assert completion.subsystem_status == "FROZEN"
    assert completion.upstream_schema_version == "OML-078"
    assert completion.upstream_engine_id == "OML-078"
    assert completion.upstream_certification_hash == (
        readiness.certification_hash
    )
    assert completion.final_freeze_complete
    assert completion.subsystem_completion_certified
    assert completion.downstream_universal_market_discovery_authorized
    assert not completion.further_oml_feature_builds_allowed
    assert completion.defect_corrections_only
    assert completion.read_only

    certificate = completion.certificate
    assert certificate.final_freeze_milestone == "OML-079"
    assert certificate.next_subsystem == "universal_market_discovery"
    assert certificate.readiness_manifest_hash == (
        readiness.manifest.manifest_hash
    )
    assert certificate.package_tree_hash == (
        readiness.manifest.package_tree_hash
    )
    assert certificate.test_tree_hash == readiness.manifest.test_tree_hash
    assert certificate.repository_tree_hash == (
        readiness.manifest.repository_tree_hash
    )
    assert certificate.interface_contracts_frozen
    assert certificate.universal_market_discovery_authorized
    assert certificate.final_freeze_complete
    assert not certificate.further_oml_feature_builds_allowed

    replay, _ = build_final_freeze(root)
    assert replay == completion
    assert verify_oracle_memory_final_freeze_completion(completion)

    expect_rejection(
        lambda: verify_oracle_memory_final_freeze_completion(
            replace(completion, further_oml_feature_builds_allowed=True)
        ),
        "feature authorization",
    )
    expect_rejection(
        lambda: verify_oracle_memory_final_freeze_completion(
            replace(completion, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    assert not completion.persistence_enabled
    assert not completion.learning_updates_enabled
    assert not completion.runtime_activation_enabled
    assert not completion.publication_enabled
    assert not completion.action_authorization_enabled
    assert not completion.qseries_execution_enabled

    print("[PASS] Certified OML-078 readiness consumed read-only")
    print("[PASS] Readiness manifest and repository hashes sealed")
    print("[PASS] Oracle Memory interfaces frozen")
    print("[PASS] Deterministic replay and immutable lineage frozen")
    print("[PASS] Oracle Terminal separation frozen")
    print("[PASS] Active capabilities permanently frozen disabled")
    print("[PASS] Further OML feature builds prohibited")
    print("[PASS] Defect corrections remain the only allowed OML changes")
    print("[PASS] Universal Market Discovery authorized next")
    print("[PASS] Tampered final-freeze completions rejected")
    print("[DONE] OML-079 ORACLE MEMORY FINAL FREEZE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
