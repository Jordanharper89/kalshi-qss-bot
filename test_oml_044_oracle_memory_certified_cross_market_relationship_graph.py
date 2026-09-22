from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_relationship_graph import (
    OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError,
    build_oracle_memory_certified_cross_market_relationship_graph,
    verify_oracle_memory_certified_cross_market_relationship_graph,
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
    except OracleMemoryCertifiedCrossMarketRelationshipGraphInvariantError:
        return
    raise AssertionError(f"tampered OML-044 {label} accepted")


def build_resolution(root: Path):
    fixture_039 = load_module(
        root
        / "test_oml_039_oracle_memory_certified_cross_market_observation_intake_bridge.py",
        "oml_039_fixture_for_oml_044",
    )
    dependencies = fixture_039.build_dependencies(root)
    dependency = dependencies.dependency_memory.dependencies[0]

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
        build_oracle_memory_certified_cross_market_intake_request,
        build_oracle_memory_certified_cross_market_intake_bridge,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
        build_oracle_memory_cross_market_materialization_authorization_decision,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization import (
        build_oracle_memory_certified_cross_market_candidate_materialization,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_validation_and_admission import (
        build_oracle_memory_certified_cross_market_candidate_admission,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_entity_resolution import (
        build_oracle_memory_certified_cross_market_entity_resolution,
    )
    from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
        MEMORY_DOMAINS,
    )

    domain_id = (
        "market_behavior_memory"
        if "market_behavior_memory" in MEMORY_DOMAINS
        else MEMORY_DOMAINS[0]
    )

    intake_requests = (
        build_oracle_memory_certified_cross_market_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Stablecoin Liquidity",
            source_key="oracle-memory-oml-038",
            observed_at="2026-08-02T17:00:00-05:00",
            effective_at="2026-08-02T17:00:00-05:00",
            payload={
                "observation": "Stablecoin inflows increased before repricing.",
                "observation_type": "real_world_liquidity_shift",
            },
            confidence=0.82,
            uncertainty=0.18,
        ),
        build_oracle_memory_certified_cross_market_intake_request(
            dependency_id=dependency.dependency_id,
            domain_id=domain_id,
            entity_key="Bitcoin",
            source_key="oracle-memory-oml-038",
            observed_at="2026-08-02T17:10:00-05:00",
            effective_at="2026-08-02T17:10:00-05:00",
            payload={
                "observation": "Bitcoin repriced after the liquidity shift.",
                "observation_type": "market_repricing",
            },
            confidence=0.79,
            uncertainty=0.21,
        ),
    )

    bridge = build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=intake_requests,
    )
    authorization = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_044",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    materialization = (
        build_oracle_memory_certified_cross_market_candidate_materialization(
            authorization=authorization,
            bridge=bridge,
            registry_gate_decision=registry_gate_decision,
        )
    )

    fixture_042 = load_module(
        root
        / "test_oml_042_oracle_memory_certified_cross_market_candidate_validation_and_admission.py",
        "oml_042_fixture_for_oml_044",
    )
    validation_batch = fixture_042.build_validation(root, materialization)

    admission = build_oracle_memory_certified_cross_market_candidate_admission(
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
            aliases[item.candidate_hash] = (
                "Stablecoin Liquidity",
                "USDT Liquidity",
            )
        elif candidate.entity_key == "Bitcoin":
            aliases[item.candidate_hash] = (
                "Bitcoin",
                "BTC",
                "XBT",
            )

    resolution = build_oracle_memory_certified_cross_market_entity_resolution(
        admission=admission,
        materialization_batch=materialization.materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash=aliases,
    )

    assert resolution.resolved_entity_count == 2
    assert {
        entity.normalized_name
        for entity in resolution.resolution.entities
    } == {"bitcoin", "stablecoin liquidity"}

    return resolution


def main() -> int:
    print("=" * 48)
    print(" OML-044 TEST")
    print(" CERTIFIED CROSS-MARKET RELATIONSHIP GRAPH")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    resolution = build_resolution(root)

    assert resolution.resolved_entity_count >= 2
    entities = tuple(resolution.resolution.entities)
    source = entities[0]
    target = entities[1]

    request = build_oracle_memory_observation_relationship_request(
        source_entity_id=source.canonical_entity_id,
        target_entity_id=target.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    result = build_oracle_memory_certified_cross_market_relationship_graph(
        resolution=resolution,
        requests=(request,),
    )

    assert result.schema_version == "OML-044"
    assert result.engine_id == "OML-044"
    assert result.upstream_schema_version == "OML-043"
    assert result.upstream_engine_id == "OML-043"
    assert result.graph_schema_version == "OML-031"
    assert result.graph_engine_id == "OML-031"
    assert result.entity_count >= 2
    assert result.relationship_count == 1
    assert result.graph_materialization.relationship_count == 1
    assert result.upstream_certification_hash == resolution.certification_hash
    assert result.upstream_resolution_hash == resolution.resolution.resolution_hash
    assert result.resolution_lineage_verified
    assert result.observation_entity_lineage_verified
    assert result.relationship_lineage_verified
    assert result.canonical_graph_order_verified
    assert result.deterministic_graph_materialization_verified
    assert result.dangling_relationships_rejected
    assert result.duplicate_relationships_rejected
    assert result.graph_ready
    assert result.downstream_narrative_detection_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_relationship_graph(
        resolution=resolution,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_relationship_graph(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, downstream_narrative_detection_authorized=False)
        ),
        "narrative continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_relationship_graph(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-043 entity resolution consumed read-only")
    print("[PASS] Exact OML-030 resolution dataclass passed directly")
    print("[PASS] Actual OML-031 relationship request builder consumed")
    print("[PASS] Actual OML-031 graph materialization builder consumed")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Entity-to-relationship lineage retained")
    print("[PASS] Dangling and duplicate relationships rejected")
    print("[PASS] Narrative-detection continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-044 graphs rejected")
    print("[DONE] OML-044 CERTIFIED CROSS-MARKET RELATIONSHIP GRAPH PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
