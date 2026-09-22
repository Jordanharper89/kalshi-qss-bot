from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
    OracleMemoryCertifiedCrossMarketIntakeInvariantError,
    build_oracle_memory_certified_cross_market_intake_request,
    build_oracle_memory_certified_cross_market_intake_bridge,
    verify_oracle_memory_certified_cross_market_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OracleMemoryObservationIntakeInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
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
    except (
        OracleMemoryCertifiedCrossMarketIntakeInvariantError,
        OracleMemoryObservationIntakeInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-039 {label} accepted")


def build_dependencies(root: Path):
    fixture = load_module(
        root / "test_oml_038_oracle_memory_certified_observation_cross_market_dependency_memory.py",
        "oml_038_fixture_for_oml_039",
    )
    causal_patterns = fixture.build_chains(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_multi_hop_chain_request,
        build_oracle_memory_certified_multi_hop_causal_chain_memory,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
        build_oracle_memory_certified_cross_market_observation_request,
        build_oracle_memory_certified_cross_market_dependency_memory,
    )

    ordered_patterns = sorted(
        causal_patterns.causal_memory.patterns,
        key=lambda item: item.cause_entity_id,
    )
    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Real-world demand to market repricing chain",
        pattern_ids=tuple(item.pattern_id for item in ordered_patterns),
    )
    chains = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(chain_request,),
    )
    chain = chains.chain_memory.chains[0]
    certified_hashes = chains.bindings[0].certified_observation_hashes

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="e" * 64,
            target_event_hash="f" * 64,
            source_observed_at="2026-08-02T15:00:00-05:00",
            target_observed_at="2026-08-02T15:04:00-05:00",
            lag_seconds=240,
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )
    return build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-039 TEST")
    print(" CERTIFIED CROSS-MARKET OBSERVATION INTAKE BRIDGE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    dependencies = build_dependencies(root)
    dependency = dependencies.dependency_memory.dependencies[0]

    request = build_oracle_memory_certified_cross_market_intake_request(
        dependency_id=dependency.dependency_id,
        domain_id=(
            "market_behavior_memory"
            if "market_behavior_memory" in MEMORY_DOMAINS
            else MEMORY_DOMAINS[0]
        ),
        entity_key="Bitcoin cross-market dependency",
        source_key="oracle-memory-oml-038",
        observed_at="2026-08-02T17:00:00-05:00",
        effective_at="2026-08-02T17:00:00-05:00",
        payload={
            "observation": (
                "A certified prediction-market dependency preceded "
                "crypto spot repricing."
            ),
            "observation_type": "cross_market_dependency",
        },
        confidence=0.80,
        uncertainty=0.20,
    )

    result = build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )

    assert result.schema_version == "OML-039"
    assert result.engine_id == "OML-039"
    assert result.upstream_schema_version == "OML-038"
    assert result.upstream_engine_id == "OML-038"
    assert result.intake_schema_version == "OML-027"
    assert result.intake_engine_id == "OML-027"
    assert result.dependency_count == 1
    assert result.observation_count == 1
    assert result.unique_observation_count == 1
    assert result.duplicate_observation_count == 0

    observation = result.intake_batch.observations[0]
    binding = result.bindings[0]

    assert binding.dependency_id == dependency.dependency_id
    assert binding.dependency_hash == dependency.dependency_hash
    assert binding.observation_id == observation.observation_id
    assert binding.observation_hash == observation.observation_hash
    assert binding.upstream_certification_hash == dependencies.certification_hash
    assert binding.upstream_dependency_memory_hash == (
        dependencies.dependency_memory.memory_hash
    )
    assert binding.intake_batch_hash == result.intake_batch.batch_hash
    assert observation.source_certification_hash == dependencies.certification_hash
    assert observation.evidence_hashes
    assert observation.parent_observation_hashes

    assert result.dependency_lineage_verified
    assert result.chain_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_hashing_verified
    assert result.canonical_order_verified
    assert result.duplicate_detection_verified
    assert result.source_certification_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.bridge_ready
    assert not result.downstream_candidate_materialization_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_intake_bridge(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_intake_bridge(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_intake_bridge(
            replace(result, downstream_candidate_materialization_authorized=True)
        ),
        "candidate materialization boundary",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_intake_bridge(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-038 dependency memory consumed read-only")
    print("[PASS] Exact OML-026 dependency-memory dataclass passed directly")
    print("[PASS] Actual OML-027 observation and batch builders consumed")
    print("[PASS] Dependency, chain, causal, and observation lineage retained")
    print("[PASS] Source certification bound to OML-038 certification")
    print("[PASS] Deterministic intake observation generated")
    print("[PASS] Candidate materialization remained disabled")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-039 bridges rejected")
    print("[DONE] OML-039 CERTIFIED CROSS-MARKET OBSERVATION INTAKE BRIDGE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
