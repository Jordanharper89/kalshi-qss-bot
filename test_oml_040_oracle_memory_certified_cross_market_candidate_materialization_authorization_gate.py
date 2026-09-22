from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
    OracleMemoryCrossMarketMaterializationAuthorizationInvariantError,
    build_oracle_memory_cross_market_materialization_authorization_decision,
    verify_oracle_memory_cross_market_materialization_authorization_decision,
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
    except OracleMemoryCrossMarketMaterializationAuthorizationInvariantError:
        return
    raise AssertionError(f"tampered OML-040 {label} accepted")


def build_bridge(root: Path):
    fixture = load_module(
        root
        / "test_oml_039_oracle_memory_certified_cross_market_observation_intake_bridge.py",
        "oml_039_fixture_for_oml_040",
    )
    dependencies = fixture.build_dependencies(root)
    dependency = dependencies.dependency_memory.dependencies[0]

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_observation_intake_bridge import (
        build_oracle_memory_certified_cross_market_intake_request,
        build_oracle_memory_certified_cross_market_intake_bridge,
    )
    from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
        MEMORY_DOMAINS,
    )

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

    return build_oracle_memory_certified_cross_market_intake_bridge(
        dependencies=dependencies,
        requests=(request,),
    )


def main() -> int:
    print("=" * 48)
    print(" OML-040 TEST")
    print(" CROSS-MARKET CANDIDATE MATERIALIZATION AUTHORIZATION GATE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    bridge = build_bridge(root)

    result = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    assert result.schema_version == "OML-040"
    assert result.engine_id == "OML-040"
    assert result.upstream_schema_version == "OML-039"
    assert result.upstream_engine_id == "OML-039"
    assert result.upstream_certification_hash == bridge.certification_hash
    assert result.upstream_intake_batch_hash == bridge.intake_batch.batch_hash
    assert result.upstream_observation_count == bridge.observation_count
    assert result.upstream_unique_observation_count == (
        bridge.unique_observation_count
    )
    assert result.candidate_materialization_authorized
    assert not result.candidate_admission_authorized
    assert not result.persistence_authorized
    assert not result.learning_update_authorized
    assert not result.runtime_activation_authorized
    assert not result.publication_authorized
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_authorized
    assert result.downstream_materialization_ready
    assert result.read_only

    replay = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )
    assert replay == result
    assert (
        verify_oracle_memory_cross_market_materialization_authorization_decision(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, candidate_admission_authorized=True)
        ),
        "candidate admission",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, persistence_authorized=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, qseries_execution_authorized=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_cross_market_materialization_authorization_decision(
            replace(result, decision_hash="f" * 64)
        ),
        "decision hash",
    )

    print("[PASS] Certified OML-039 bridge consumed read-only")
    print("[PASS] OML-039 certification and intake-batch lineage retained")
    print("[PASS] Dependency, chain, and observation guarantees verified")
    print("[PASS] Deterministic candidate materialization authorized")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Tampered OML-040 decisions rejected")
    print(
        "[DONE] OML-040 CROSS-MARKET CANDIDATE "
        "MATERIALIZATION AUTHORIZATION GATE PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
