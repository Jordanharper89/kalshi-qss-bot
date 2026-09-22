from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_final_freeze_readiness_certification_gate_078 import (
    FINAL_FREEZE_MILESTONE,
    NEXT_SUBSYSTEM,
    OracleMemoryFinalFreezeReadinessInvariantError,
    build_oracle_memory_final_freeze_readiness_report,
    verify_oracle_memory_final_freeze_readiness_report,
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
    except OracleMemoryFinalFreezeReadinessInvariantError:
        return
    raise AssertionError(f"tampered OML-078 {label} accepted")


def build_freeze_readiness(root: Path):
    fixture_077 = load_module(
        root
        / "test_oml_077_oracle_memory_certified_market_behavior_"
        "cross_market_dependency_memory.py",
        "oml_077_fixture_for_oml_078",
    )
    dependencies, chains, certified_hashes = (
        fixture_077.build_dependencies(root)
    )
    report = build_oracle_memory_final_freeze_readiness_report(
        root,
        dependencies=dependencies,
    )
    return report, dependencies


def main() -> int:
    print("=" * 48)
    print(" OML-078 TEST")
    print(" FINAL FREEZE READINESS CERTIFICATION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    report, dependencies = build_freeze_readiness(root)

    assert report.schema_version == "OML-078"
    assert report.engine_id == "OML-078"
    assert report.upstream_schema_version == "OML-077"
    assert report.upstream_engine_id == "OML-077"
    assert report.source_dependency_memory_ready
    assert report.complete_repository_inventory_certified
    assert report.deterministic_replay_certified
    assert report.immutable_lineage_certified
    assert report.final_freeze_ready
    assert report.downstream_final_freeze_authorized
    assert not report.further_feature_builds_allowed
    assert report.correction_builds_allowed_only_for_defects
    assert report.read_only

    manifest = report.manifest
    assert manifest.current_milestone == "OML-078"
    assert manifest.final_freeze_milestone == FINAL_FREEZE_MILESTONE
    assert manifest.next_subsystem == NEXT_SUBSYSTEM
    assert manifest.source_certification_hash == (
        dependencies.certification_hash
    )
    assert manifest.package_file_count == len(manifest.package_files)
    assert manifest.test_file_count == len(manifest.test_files)
    assert manifest.package_file_count > 0
    assert manifest.test_file_count > 0
    assert all(record.size_bytes > 0 for record in manifest.package_files)
    assert all(record.size_bytes > 0 for record in manifest.test_files)
    assert not any(
        record.relative_path.endswith(
            "test_oml_001_oracle_memory_foundation_and_"
            "certified_oit_read_only_dependency.py"
        )
        for record in manifest.test_files
    )
    assert manifest.final_freeze_ready
    assert manifest.defect_corrections_only_after_freeze

    replay, _ = build_freeze_readiness(root)
    assert replay == report
    assert verify_oracle_memory_final_freeze_readiness_report(report)

    expect_rejection(
        lambda: verify_oracle_memory_final_freeze_readiness_report(
            replace(report, further_feature_builds_allowed=True)
        ),
        "feature-build authorization",
    )
    expect_rejection(
        lambda: verify_oracle_memory_final_freeze_readiness_report(
            replace(report, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    assert not report.persistence_enabled
    assert not report.learning_updates_enabled
    assert not report.runtime_activation_enabled
    assert not report.publication_enabled
    assert not report.action_authorization_enabled
    assert not report.qseries_execution_enabled

    print("[PASS] Certified OML-077 dependency memory consumed read-only")
    print("[PASS] Complete Oracle Memory package inventory hashed")
    print("[PASS] Complete OML standalone-test inventory hashed")
    print("[PASS] Repository tree manifest created deterministically")
    print("[PASS] Immutable lineage and replay certified")
    print("[PASS] Oracle Terminal separation certified")
    print("[PASS] Active capabilities frozen disabled")
    print("[PASS] Further OML feature builds prohibited")
    print("[PASS] Defect corrections remain the only post-freeze changes")
    print("[PASS] OML-079 final freeze authorized")
    print("[PASS] Universal Market Discovery recorded as next subsystem")
    print("[PASS] Tampered readiness reports rejected")
    print("[DONE] OML-078 FINAL FREEZE READINESS CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
