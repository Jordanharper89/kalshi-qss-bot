from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory_075 import (
    OracleMemoryCertifiedMarketBehaviorCausal075InvariantError,
    build_oracle_memory_certified_market_behavior_causal_pattern_memory_075,
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
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
    except OracleMemoryCertifiedMarketBehaviorCausal075InvariantError:
        return
    raise AssertionError(f"tampered OML-075 {label} accepted")


def build_causal_memory(root: Path):
    fixture_074 = load_module(
        root
        / "test_oml_074_oracle_memory_certified_market_behavior_"
        "calibration_memory.py",
        "oml_074_fixture_for_oml_075",
    )
    calibration, reliability, forecasts = fixture_074.build_calibration(root)

    certified_hashes = tuple(
        sorted(
            {
                value
                for binding in calibration.calibration.bindings
                for value in binding.certified_observation_hashes
            }
        )
    )
    assert certified_hashes

    request = build_oracle_memory_certified_causal_observation_request(
        pattern_name="Market-behavior liquidity shift precedes repricing",
        cause_entity_id="1" * 64,
        effect_entity_id="2" * 64,
        cause_observed_at="2026-08-04T16:00:00-05:00",
        effect_observed_at="2026-08-04T16:05:00-05:00",
        certified_observation_hashes=(certified_hashes[0],),
        contradicting_certified_observation_hashes=(),
        confidence=0.82,
        calibrated_probability=0.80,
        outcome_confirmed=True,
        outcome_supported=True,
    )

    result = (
        build_oracle_memory_certified_market_behavior_causal_pattern_memory_075(
            calibration=calibration,
            requests=(request,),
        )
    )
    return result, calibration, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-075 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result, calibration, certified_hashes = build_causal_memory(root)

    assert result.schema_version == "OML-075"
    assert result.engine_id == "OML-075"
    assert result.upstream_schema_version == "OML-074"
    assert result.upstream_engine_id == "OML-074"
    assert result.causal_schema_version == "OML-036"
    assert result.causal_engine_id == "OML-036"
    assert result.pattern_count == 1
    assert result.total_observation_count == 1
    assert result.calibration_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.temporal_precedence_verified
    assert result.evidence_lineage_verified
    assert result.outcome_reconciliation_verified
    assert result.causal_memory_ready
    assert result.downstream_multi_hop_causal_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    binding = result.causal_patterns.bindings[0]
    assert set(binding.certified_observation_hashes).issubset(
        set(certified_hashes)
    )

    replay, _, _ = build_causal_memory(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory_075(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-074 calibration consumed read-only")
    print("[PASS] Exact OML-035 calibration object passed directly")
    print("[PASS] Actual OML-036 causal-pattern builder consumed")
    print("[PASS] Causal evidence bound only to certified observation hashes")
    print("[PASS] Calibration and temporal-precedence lineage retained")
    print("[PASS] Outcome reconciliation retained")
    print("[PASS] Multi-hop continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-075 causal objects rejected")
    print("[DONE] OML-075 CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
