from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    build_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    build_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    build_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_MARKET,
    OBSERVATION_KIND_REAL_WORLD,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    OracleMemoryObservationRelationshipGraphInvariantError,
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
    verify_oracle_memory_observation_relationship_graph_materialization,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryRelationshipGraphInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    build_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
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
    except (
        OracleMemoryObservationRelationshipGraphInvariantError,
        OracleMemoryRelationshipGraphInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-031 {label} accepted")


def build_resolution(root: Path):
    fixture_026 = load_module(
        root
        / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_031",
    )
    chain_memory, _ = fixture_026.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation_a = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Stablecoin Liquidity",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={"signal": "stablecoin_inflow_increase"},
        evidence_hashes=("1" * 64,),
        source_certification_hash="2" * 64,
        confidence=0.82,
        uncertainty=0.18,
    )

    observation_b = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_MARKET,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:10:00-05:00",
        effective_at="2026-08-02T15:10:00-05:00",
        payload={"signal": "market_repricing"},
        evidence_hashes=("3" * 64,),
        source_certification_hash="4" * 64,
        confidence=0.79,
        uncertainty=0.21,
    )

    intake = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation_a, observation_b),
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_031",
    )
    gate_decision = fixture_009.build_oml_008_decision(root)

    materialization = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake,
        )
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_031",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=materialization.candidates,
    )

    admission = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization,
        validation_batch=validation,
    )

    aliases = {
        candidate.candidate_hash: (
            ("USDT Liquidity", "Stablecoin Liquidity")
            if candidate.entity_key == "Stablecoin Liquidity"
            else ("BTC", "Bitcoin", "XBT")
        )
        for candidate in materialization.candidates
    }

    return build_oracle_memory_observation_entity_resolution(
        admission_batch=admission,
        materialization_batch=materialization,
        validation_batch=validation,
        aliases_by_candidate_hash=aliases,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-031 CORRECTION V2 TEST")
    print(" CERTIFIED OBSERVATION RELATIONSHIP GRAPH MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    resolution = build_resolution(root)

    assert resolution.resolved_entity_count == 2

    liquidity = next(
        item for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item for item in resolution.entities
        if item.normalized_name == "bitcoin"
    )

    request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )

    materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request,),
        )
    )

    assert materialization.schema_version == "OML-031"
    assert materialization.engine_id == "OML-031"
    assert materialization.upstream_schema_version == "OML-030"
    assert materialization.upstream_engine_id == "OML-030"
    assert materialization.entity_count == 2
    assert materialization.relationship_count == 1
    assert materialization.graph.entity_count == 2
    assert materialization.graph.relationship_count == 1
    assert materialization.certified_entity_lineage_verified
    assert materialization.observation_relationship_lineage_verified
    assert materialization.canonical_graph_order_verified
    assert materialization.deterministic_graph_materialization_verified
    assert materialization.dangling_relationships_rejected
    assert materialization.duplicate_relationships_rejected
    assert not materialization.persistence_enabled
    assert not materialization.learning_updates_enabled
    assert not materialization.runtime_activation_enabled
    assert not materialization.publication_enabled
    assert not materialization.action_authorization_enabled
    assert not materialization.qseries_execution_enabled
    assert materialization.graph_ready
    assert materialization.downstream_narrative_detection_authorized
    assert materialization.read_only

    replay = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request,),
        )
    )

    assert replay == materialization
    assert (
        verify_oracle_memory_observation_relationship_graph_materialization(
            materialization
        )
    )

    expect_rejection(
        lambda: build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(request, request),
        ),
        "duplicate relationship",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(materialization, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(
                materialization,
                downstream_narrative_detection_authorized=False,
            )
        ),
        "narrative authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_relationship_graph_materialization(
            replace(materialization, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-030 entity resolution consumed")
    print("[PASS] Certified OML-019 relationship engine consumed")
    print("[PASS] OML-018 entity batch contract adapted exactly")
    print("[PASS] Entity dataclass identities preserved")
    print("[PASS] Evidence-backed observation relationship created")
    print("[PASS] Observation-to-relationship lineage retained")
    print("[PASS] Dangling relationships rejected")
    print("[PASS] Duplicate relationships rejected")
    print("[PASS] Relationship graph deterministic across replay")
    print("[PASS] Narrative continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered graph materializations rejected")
    print(
        "[DONE] OML-031 CORRECTION V2 CERTIFIED OBSERVATION "
        "RELATIONSHIP GRAPH MATERIALIZATION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
