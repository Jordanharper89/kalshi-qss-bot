from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_detection_and_evolution import (
    OracleMemoryCertifiedCrossMarketNarrativeInvariantError,
    build_oracle_memory_certified_cross_market_narrative_detection,
    verify_oracle_memory_certified_cross_market_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
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
    except OracleMemoryCertifiedCrossMarketNarrativeInvariantError:
        return
    raise AssertionError(f"tampered OML-045 {label} accepted")


def build_graph(root: Path):
    fixture = load_module(
        root
        / "test_oml_044_oracle_memory_certified_cross_market_relationship_graph.py",
        "oml_044_fixture_for_oml_045",
    )
    resolution = fixture.build_resolution(root)

    entities = {
        entity.normalized_name: entity
        for entity in resolution.resolution.entities
    }
    liquidity = entities["stablecoin liquidity"]
    bitcoin = entities["bitcoin"]

    relationship_request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_relationship_graph import (
        build_oracle_memory_certified_cross_market_relationship_graph,
    )

    graph = build_oracle_memory_certified_cross_market_relationship_graph(
        resolution=resolution,
        requests=(relationship_request,),
    )
    return graph, liquidity, bitcoin


def main() -> int:
    print("=" * 48)
    print(" OML-045 TEST")
    print(" CERTIFIED CROSS-MARKET NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    graph, liquidity, bitcoin = build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "7" * 64,
            "8" * 64,
            "9" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T17:00:00-05:00",
        last_observed_at="2026-08-02T17:10:00-05:00",
        evolution_index=1,
    )

    result = build_oracle_memory_certified_cross_market_narrative_detection(
        graph=graph,
        requests=(request,),
    )

    assert result.schema_version == "OML-045"
    assert result.engine_id == "OML-045"
    assert result.upstream_schema_version == "OML-044"
    assert result.upstream_engine_id == "OML-044"
    assert result.narrative_schema_version == "OML-032"
    assert result.narrative_engine_id == "OML-032"
    assert result.upstream_certification_hash == graph.certification_hash
    assert result.upstream_graph_materialization_hash == (
        graph.graph_materialization.materialization_hash
    )
    assert result.upstream_graph_hash == graph.graph_materialization.graph.graph_hash
    assert result.narrative_count == 1
    assert result.strengthening_count == 1
    assert result.narrative_detection.narratives[0].stage == (
        NARRATIVE_STAGE_STRENGTHENING
    )
    assert result.graph_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.relationship_lineage_verified
    assert result.observation_narrative_lineage_verified
    assert result.canonical_order_verified
    assert result.deterministic_detection_verified
    assert result.contradiction_tracking_verified
    assert result.detection_ready
    assert result.downstream_lifecycle_tracking_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_narrative_detection(
        graph=graph,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_narrative_detection(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_detection(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_detection(
            replace(result, downstream_lifecycle_tracking_authorized=False)
        ),
        "lifecycle continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_detection(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_detection(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-044 relationship graph consumed read-only")
    print("[PASS] Exact OML-031 graph materialization passed directly")
    print("[PASS] Actual OML-032 narrative builders consumed")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Entity-to-relationship lineage retained")
    print("[PASS] Relationship-to-narrative lineage retained")
    print("[PASS] Strengthening narrative detected")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Lifecycle continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-045 detections rejected")
    print(
        "[DONE] OML-045 CERTIFIED CROSS-MARKET "
        "NARRATIVE DETECTION AND EVOLUTION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
