from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization import (
    OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError,
    build_oracle_memory_certified_market_behavior_candidate_materialization,
    verify_oracle_memory_certified_market_behavior_candidate_materialization,
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
    except OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError:
        return
    raise AssertionError(f"tampered OML-054 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-054 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture_040 = load_module(
        root / "test_oml_053_oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate.py",
        "oml_040_fixture_for_oml_041",
    )
    bridge = fixture_040.build_bridge(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate import build_oracle_memory_market_behavior_materialization_authorization_decision
    authorization = build_oracle_memory_market_behavior_materialization_authorization_decision(bridge=bridge)

    fixture_028 = load_module(
        root / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_041",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    result = build_oracle_memory_certified_market_behavior_candidate_materialization(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )

    assert result.schema_version == "OML-054"
    assert result.engine_id == "OML-054"
    assert result.authorization_schema_version == "OML-053"
    assert result.bridge_schema_version == "OML-052"
    assert result.materialization_schema_version == "OML-028"
    assert result.authorization_decision_hash == authorization.decision_hash
    assert result.bridge_certification_hash == bridge.certification_hash
    assert result.intake_batch_hash == bridge.intake_batch.batch_hash
    assert result.registry_gate_decision_hash == registry_gate_decision.decision_hash
    assert result.observation_count == bridge.observation_count
    assert result.candidate_count == bridge.observation_count
    assert result.materialization_batch.materialization_ready
    assert not result.candidate_admission_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.downstream_validation_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_candidate_materialization(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_candidate_materialization(result)

    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization(replace(result, candidate_admission_authorized=True)), "candidate admission")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization(replace(result, persistence_enabled=True)), "persistence")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization(replace(result, qseries_execution_enabled=True)), "Q Series execution")
    expect_rejection(lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization(replace(result, certification_hash="f" * 64)), "certification hash")

    print("[PASS] Certified OML-053 authorization consumed read-only")
    print("[PASS] Exact OML-052 intake batch passed directly")
    print("[PASS] Certified OML-008 registry gate decision passed directly")
    print("[PASS] Actual OML-028 materialization builder consumed")
    print("[PASS] Observation-to-candidate lineage retained")
    print("[PASS] Source-certification lineage retained")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-054 materializations rejected")
    print("[DONE] OML-054 CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
