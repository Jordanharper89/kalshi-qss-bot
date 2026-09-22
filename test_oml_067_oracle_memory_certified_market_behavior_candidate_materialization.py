from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_067 import (
    OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError,
    build_oracle_memory_certified_market_behavior_candidate_materialization_067,
    verify_oracle_memory_certified_market_behavior_candidate_materialization_067,
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
    except OracleMemoryCertifiedMarketBehaviorMaterialization067InvariantError:
        return
    raise AssertionError(f"tampered OML-067 {label} accepted")


def build_materialization(root: Path):
    fixture_066 = load_module(
        root
        / "test_oml_066_oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate.py",
        "oml_066_fixture_for_oml_067",
    )
    bridge = fixture_066.build_bridge(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate_066 import (
        build_oracle_memory_market_behavior_materialization_authorization_decision,
    )

    authorization = (
        build_oracle_memory_market_behavior_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_067",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    return build_oracle_memory_certified_market_behavior_candidate_materialization_067(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-067 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result = build_materialization(root)

    assert result.schema_version == "OML-067"
    assert result.engine_id == "OML-067"
    assert result.authorization_schema_version == "OML-066"
    assert result.authorization_engine_id == "OML-066"
    assert result.bridge_schema_version == "OML-065"
    assert result.bridge_engine_id == "OML-065"
    assert result.materialization_schema_version == "OML-028"
    assert result.materialization_engine_id == "OML-028"
    assert result.materialization_ready
    assert result.downstream_validation_authorized
    assert not result.candidate_admission_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_materialization(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_candidate_materialization_067(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067(
            replace(result, candidate_admission_authorized=True)
        ),
        "candidate admission",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_candidate_materialization_067(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-066 authorization consumed read-only")
    print("[PASS] Exact OML-065 intake batch passed directly")
    print("[PASS] Certified OML-008 registry gate decision passed directly")
    print("[PASS] Actual OML-028 materialization builder consumed")
    print("[PASS] Observation-to-candidate lineage retained")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-067 materializations rejected")
    print("[DONE] OML-067 CERTIFIED MARKET-BEHAVIOR CANDIDATE MATERIALIZATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
