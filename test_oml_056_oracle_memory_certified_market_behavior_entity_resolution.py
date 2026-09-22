from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_entity_resolution import (
    OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError,
    build_oracle_memory_certified_market_behavior_entity_resolution,
    verify_oracle_memory_certified_market_behavior_entity_resolution,
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
    except OracleMemoryCertifiedMarketBehaviorEntityResolutionInvariantError:
        return
    raise AssertionError(f"tampered OML-056 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-056 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_055_fixture_for_oml_056",
    )

    materialization = fixture.build_materialization(root)
    validation_batch = fixture.build_validation(root, materialization)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission import (
        build_oracle_memory_certified_market_behavior_candidate_admission,
    )

    admission = build_oracle_memory_certified_market_behavior_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    admitted_candidate_hash = next(
        item.candidate_hash
        for item in admission.admission_batch.admissions
        if item.admission_status == "admitted"
    )

    result = build_oracle_memory_certified_market_behavior_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: ("BTC", "Bitcoin", "XBT")
        },
    )

    assert result.schema_version == "OML-056"
    assert result.engine_id == "OML-056"
    assert result.upstream_schema_version == "OML-055"
    assert result.upstream_engine_id == "OML-055"
    assert result.resolution_schema_version == "OML-030"
    assert result.resolution_engine_id == "OML-030"
    assert result.resolved_entity_count == 1
    admitted_candidate = next(
        candidate
        for candidate in materialization.materialization_batch.candidates
        if candidate.candidate_hash == admitted_candidate_hash
    )
    resolved_entity = next(
        entity
        for entity in result.resolution.entities
        if entity.source_candidate_hash == admitted_candidate_hash
    )
    expected_canonical_name = admitted_candidate.entity_key.strip()
    expected_normalized_name = " ".join(
        expected_canonical_name.lower().split()
    )
    normalized_aliases = {
        alias.normalized_alias
        for alias in resolved_entity.aliases
    }

    assert resolved_entity.canonical_name == expected_canonical_name
    assert resolved_entity.normalized_name == expected_normalized_name
    assert expected_normalized_name in normalized_aliases
    assert {"btc", "bitcoin", "xbt"}.issubset(normalized_aliases)
    assert result.admission_lineage_verified
    assert result.materialization_lineage_verified
    assert result.validation_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.duplicate_candidates_excluded
    assert result.deterministic_resolution_verified
    assert result.entity_identity_uniqueness_verified
    assert result.resolution_ready
    assert result.downstream_relationship_graph_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: ("XBT", "Bitcoin", "BTC")
        },
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_entity_resolution(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, downstream_relationship_graph_authorized=False)
        ),
        "relationship graph continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_entity_resolution(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-055 admission consumed read-only")
    print("[PASS] Exact OML-029 admission batch passed directly")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-030 entity-resolution builder consumed")
    print("[PASS] Duplicate-rejected candidates excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Relationship-graph continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-056 resolutions rejected")
    print("[DONE] OML-056 CERTIFIED MARKET-BEHAVIOR ENTITY RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
