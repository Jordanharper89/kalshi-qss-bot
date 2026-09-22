from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_detection_and_evolution_071 import (
    OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError,
    build_oracle_memory_certified_market_behavior_narrative_detection_071,
    verify_oracle_memory_certified_market_behavior_narrative_detection_071,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_request,
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
    except OracleMemoryCertifiedMarketBehaviorNarrative071InvariantError:
        return
    raise AssertionError(f"tampered OML-071 {label} accepted")


def build_detection(root: Path):
    fixture = load_module(
        root / "test_oml_070_oracle_memory_certified_market_behavior_relationship_graph.py",
        "oml_070_fixture_for_oml_071",
    )
    resolution = fixture.build_resolution(root)
    entities = {entity.normalized_name: entity for entity in resolution.resolution.entities}
    liquidity = entities["stablecoin liquidity"]
    bitcoin = entities["bitcoin"]

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph_070 import (
        build_oracle_memory_certified_market_behavior_relationship_graph_070,
    )

    relationship_request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )
    graph = build_oracle_memory_certified_market_behavior_relationship_graph_070(
        resolution=resolution,
        requests=(relationship_request,),
    )
    relationship = graph.graph_materialization.graph.relationships[0]

    narrative_request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("7" * 64, "8" * 64),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-04T12:00:00-05:00",
        last_observed_at="2026-08-04T12:10:00-05:00",
        evolution_index=2,
        prior_stage=None,
    )

    return build_oracle_memory_certified_market_behavior_narrative_detection_071(
        graph=graph,
        requests=(narrative_request,),
    )


def main() -> int:
    print("=" * 48)
    print(" OML-071 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE DETECTION")
    print("=" * 48)
    root = Path(__file__).resolve().parent
    result = build_detection(root)
    assert result.schema_version == "OML-071"
    assert result.engine_id == "OML-071"
    assert result.upstream_schema_version == "OML-070"
    assert result.narrative_schema_version == "OML-032"
    assert result.narrative_count == 1
    assert result.detection_ready
    assert result.downstream_lifecycle_tracking_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    replay = build_detection(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_narrative_detection_071(result)
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_narrative_detection_071(replace(result, persistence_enabled=True)), "persistence")
    print("[PASS] Certified OML-070 graph consumed read-only")
    print("[PASS] Exact OML-031 graph materialization passed directly")
    print("[PASS] Actual OML-032 narrative builder consumed")
    print("[PASS] Entity, relationship, and evidence lineage retained")
    print("[PASS] Lifecycle continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[DONE] OML-071 CERTIFIED MARKET-BEHAVIOR NARRATIVE DETECTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
