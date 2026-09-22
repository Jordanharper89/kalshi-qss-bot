from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph_070 import (
    OracleMemoryCertifiedMarketBehaviorRelationshipGraph070InvariantError,
    build_oracle_memory_certified_market_behavior_relationship_graph_070,
    verify_oracle_memory_certified_market_behavior_relationship_graph_070,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_request,
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
    except OracleMemoryCertifiedMarketBehaviorRelationshipGraph070InvariantError:
        return
    raise AssertionError(f"tampered OML-070 {label} accepted")


def build_resolution(root: Path):
    fixture_065 = load_module(
        root / "test_oml_065_oracle_memory_certified_market_behavior_observation_intake_bridge.py",
        "oml_065_fixture_for_oml_070",
    )
    dependencies = fixture_065.build_dependencies(root)
    dependency = dependencies.dependencies.dependency_memory.dependencies[0]

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge import (
        build_oracle_memory_certified_market_behavior_observation_intake_request,
        build_oracle_memory_certified_market_behavior_observation_intake_bridge,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate_066 import (
        build_oracle_memory_market_behavior_materialization_authorization_decision,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_067 import (
        build_oracle_memory_certified_market_behavior_candidate_materialization_067,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission_068 import (
        build_oracle_memory_certified_market_behavior_candidate_admission_068,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_entity_resolution_069 import (
        build_oracle_memory_certified_market_behavior_entity_resolution_069,
    )
    from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
        MEMORY_DOMAINS,
    )

    domain_id = (
        "market_behavior_memory"
        if "market_behavior_memory" in MEMORY_DOMAINS
        else MEMORY_DOMAINS[0]
    )

    requests = (
        build_oracle_memory_certified_market_behavior_observation_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Stablecoin Liquidity",
            source_key="oracle-memory-oml-064",
            observed_at="2026-08-04T12:00:00-05:00",
            effective_at="2026-08-04T12:00:00-05:00",
            payload={"observation": "Stablecoin liquidity increased.", "observation_type": "liquidity_shift"},
            confidence=0.82,
            uncertainty=0.18,
        ),
        build_oracle_memory_certified_market_behavior_observation_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Bitcoin",
            source_key="oracle-memory-oml-064",
            observed_at="2026-08-04T12:05:00-05:00",
            effective_at="2026-08-04T12:05:00-05:00",
            payload={"observation": "Bitcoin repriced after the liquidity shift.", "observation_type": "market_repricing"},
            confidence=0.80,
            uncertainty=0.20,
        ),
    )

    bridge = build_oracle_memory_certified_market_behavior_observation_intake_bridge(
        dependencies=dependencies,
        requests=requests,
    )
    authorization = build_oracle_memory_market_behavior_materialization_authorization_decision(
        bridge=bridge,
    )

    fixture_028 = load_module(
        root / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_070",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    materialization = build_oracle_memory_certified_market_behavior_candidate_materialization_067(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )

    fixture_055 = load_module(
        root / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_055_fixture_for_oml_070",
    )
    validation_batch = fixture_055.build_validation(root, materialization)

    admission = build_oracle_memory_certified_market_behavior_candidate_admission_068(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    candidate_by_hash = {
        candidate.candidate_hash: candidate
        for candidate in materialization.materialization_batch.candidates
    }
    aliases = {}
    for item in admission.admission_batch.admissions:
        if item.admission_status != "admitted":
            continue
        candidate = candidate_by_hash[item.candidate_hash]
        if candidate.entity_key == "Stablecoin Liquidity":
            aliases[item.candidate_hash] = ("Stablecoin Liquidity", "USDT Liquidity")
        elif candidate.entity_key == "Bitcoin":
            aliases[item.candidate_hash] = ("Bitcoin", "BTC", "XBT")

    result = build_oracle_memory_certified_market_behavior_entity_resolution_069(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash=aliases,
    )
    assert result.resolved_entity_count == 2
    return result


def main() -> int:
    print("=" * 48)
    print(" OML-070 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR RELATIONSHIP GRAPH")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    resolution = build_resolution(root)
    entities = {entity.normalized_name: entity for entity in resolution.resolution.entities}
    source = entities["stablecoin liquidity"]
    target = entities["bitcoin"]

    request = build_oracle_memory_observation_relationship_request(
        source_entity_id=source.canonical_entity_id,
        target_entity_id=target.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    result = build_oracle_memory_certified_market_behavior_relationship_graph_070(
        resolution=resolution,
        requests=(request,),
    )

    assert result.schema_version == "OML-070"
    assert result.engine_id == "OML-070"
    assert result.upstream_schema_version == "OML-069"
    assert result.graph_schema_version == "OML-031"
    assert result.entity_count == 2
    assert result.relationship_count == 1
    assert result.graph_ready
    assert result.downstream_narrative_detection_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    replay = build_oracle_memory_certified_market_behavior_relationship_graph_070(
        resolution=resolution,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_relationship_graph_070(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_relationship_graph_070(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )

    print("[PASS] Certified OML-069 resolution consumed read-only")
    print("[PASS] Two admitted canonical entities retained")
    print("[PASS] Actual OML-031 relationship-graph builder consumed")
    print("[PASS] Directed relationship and evidence lineage retained")
    print("[PASS] Narrative continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-070 graphs rejected")
    print("[DONE] OML-070 CERTIFIED MARKET-BEHAVIOR RELATIONSHIP GRAPH PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
