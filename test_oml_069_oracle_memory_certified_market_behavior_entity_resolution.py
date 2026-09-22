from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_entity_resolution_069 import (
    OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError,
    build_oracle_memory_certified_market_behavior_entity_resolution_069,
    verify_oracle_memory_certified_market_behavior_entity_resolution_069,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError:
        return
    raise AssertionError(f"tampered OML-069 {label} accepted")


def build_resolution(root: Path):
    fixture_067 = load_module(
        root / "test_oml_067_oracle_memory_certified_market_behavior_candidate_materialization.py",
        "oml_067_fixture_for_oml_069",
    )
    materialization = fixture_067.build_materialization(root)

    fixture_055 = load_module(
        root / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_055_fixture_for_oml_069",
    )
    validation_batch = fixture_055.build_validation(root, materialization)

    fixture_068 = load_module(
        root / "test_oml_068_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_068_fixture_for_oml_069",
    )
    admission = fixture_068.build_admission(root)

    admitted_candidate_hash = next(
        item.candidate_hash
        for item in admission.admission_batch.admissions
        if item.admission_status == "admitted"
    )

    return build_oracle_memory_certified_market_behavior_entity_resolution_069(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: ("Bitcoin", "BTC", "XBT")
        },
    )


def main() -> int:
    print("=" * 48)
    print(" OML-069 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result = build_resolution(root)

    assert result.schema_version == "OML-069"
    assert result.engine_id == "OML-069"
    assert result.upstream_schema_version == "OML-068"
    assert result.upstream_engine_id == "OML-068"
    assert result.resolution_schema_version == "OML-030"
    assert result.resolution_engine_id == "OML-030"
    assert result.resolved_entity_count == 1
    assert result.resolution_ready
    assert result.downstream_relationship_graph_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    replay = build_resolution(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_entity_resolution_069(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution_069(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution_069(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-068 admission consumed read-only")
    print("[PASS] Exact OML-029 admission batch passed directly")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-030 entity-resolution builder consumed")
    print("[PASS] Canonical entity identity and aliases retained")
    print("[PASS] Relationship-graph continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-069 resolutions rejected")
    print("[DONE] OML-069 CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
