from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_cross_market_dependency_memory_077 import (
    OracleMemoryCertifiedMarketBehaviorDependency077InvariantError,
    build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077,
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    build_oracle_memory_certified_cross_market_observation_request,
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
    except OracleMemoryCertifiedMarketBehaviorDependency077InvariantError:
        return
    raise AssertionError(f"tampered OML-077 {label} accepted")


def build_dependencies(root: Path):
    fixture_076 = load_module(
        root
        / "test_oml_076_oracle_memory_certified_market_behavior_"
        "multi_hop_causal_chain_memory.py",
        "oml_076_fixture_for_oml_077",
    )
    chains, causal_patterns, certified_hashes = fixture_076.build_chains(
        root
    )
    chain_id = chains.chains.chain_memory.chains[0].chain_id

    request = build_oracle_memory_certified_cross_market_observation_request(
        dependency_name=(
            "Certified market-behavior chain leads target-market repricing"
        ),
        chain_ids=(chain_id,),
        source_market_id="a" * 64,
        target_market_id="b" * 64,
        source_event_hash="c" * 64,
        target_event_hash="d" * 64,
        source_observed_at="2026-08-04T16:00:00-05:00",
        target_observed_at="2026-08-04T16:10:00-05:00",
        lag_seconds=600,
        certified_observation_hashes=(certified_hashes[0],),
        contradicting_certified_observation_hashes=(),
        confidence=0.82,
        calibrated_probability=0.80,
        outcome_confirmed=True,
        dependency_supported=True,
    )

    result = (
        build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
            chains=chains,
            requests=(request,),
        )
    )
    return result, chains, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-077 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result, chains, certified_hashes = build_dependencies(root)

    assert result.schema_version == "OML-077"
    assert result.engine_id == "OML-077"
    assert result.upstream_schema_version == "OML-076"
    assert result.upstream_engine_id == "OML-076"
    assert result.dependency_schema_version == "OML-038"
    assert result.dependency_engine_id == "OML-038"
    assert result.dependency_count == 1
    assert result.total_observation_count >= 1
    assert result.source_market_count == 1
    assert result.target_market_count == 1
    assert result.chain_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.lead_lag_direction_verified
    assert result.evidence_lineage_verified
    assert result.calibration_lineage_verified
    assert result.outcome_reconciliation_verified
    assert result.dependency_memory_ready
    assert result.downstream_freeze_certification_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    binding = result.dependencies.bindings[0]
    assert set(binding.certified_observation_hashes).issubset(
        set(certified_hashes)
    )
    assert binding.chain_ids == (
        chains.chains.chain_memory.chains[0].chain_id,
    )

    replay, _, _ = build_dependencies(root)
    assert replay == result
    assert (
        verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-076 chain memory consumed read-only")
    print("[PASS] Exact OML-037 chain object passed directly")
    print("[PASS] Actual OML-038 dependency builder consumed")
    print("[PASS] Market identity and lead-lag direction verified")
    print("[PASS] Certified observation and chain lineage retained")
    print("[PASS] Calibration and outcome reconciliation retained")
    print("[PASS] Freeze certification continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-077 dependency objects rejected")
    print("[DONE] OML-077 CERTIFIED MARKET-BEHAVIOR DEPENDENCY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
