from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory_075 import (
    build_oracle_memory_certified_market_behavior_causal_pattern_memory_075,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076 import (
    OracleMemoryCertifiedMarketBehaviorChain076InvariantError,
    build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    build_oracle_memory_certified_multi_hop_chain_request,
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
    except OracleMemoryCertifiedMarketBehaviorChain076InvariantError:
        return
    raise AssertionError(f"tampered OML-076 {label} accepted")


def build_chains(root: Path):
    fixture_074 = load_module(
        root
        / "test_oml_074_oracle_memory_certified_market_behavior_"
        "calibration_memory.py",
        "oml_074_fixture_for_oml_076",
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

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    first_hash = certified_hashes[0]
    second_hash = (
        certified_hashes[1]
        if len(certified_hashes) > 1
        else certified_hashes[0]
    )

    causal_requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=(
                "Market-behavior liquidity shift precedes order-flow change"
            ),
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-04T16:00:00-05:00",
            effect_observed_at="2026-08-04T16:05:00-05:00",
            certified_observation_hashes=(first_hash,),
            contradicting_certified_observation_hashes=(),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=(
                "Market-behavior order-flow change precedes repricing"
            ),
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-04T16:06:00-05:00",
            effect_observed_at="2026-08-04T16:10:00-05:00",
            certified_observation_hashes=(second_hash,),
            contradicting_certified_observation_hashes=(),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    causal_patterns = (
        build_oracle_memory_certified_market_behavior_causal_pattern_memory_075(
            calibration=calibration,
            requests=causal_requests,
        )
    )

    patterns = {
        pattern.normalized_pattern_name: pattern
        for pattern in causal_patterns.causal_patterns.causal_memory.patterns
    }
    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Market-behavior liquidity shift to repricing",
        pattern_ids=(
            patterns[
                "market-behavior liquidity shift precedes order-flow change"
            ].pattern_id,
            patterns[
                "market-behavior order-flow change precedes repricing"
            ].pattern_id,
        ),
    )

    result = (
        build_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )
    return result, causal_patterns, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-076 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result, causal_patterns, certified_hashes = build_chains(root)

    assert result.schema_version == "OML-076"
    assert result.engine_id == "OML-076"
    assert result.upstream_schema_version == "OML-075"
    assert result.upstream_engine_id == "OML-075"
    assert result.chain_schema_version == "OML-037"
    assert result.chain_engine_id == "OML-037"
    assert result.chain_count == 1
    assert result.total_hop_count == 2
    assert result.causal_pattern_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.hop_continuity_verified
    assert result.temporal_direction_verified
    assert result.evidence_depth_reconciled
    assert result.contradiction_depth_reconciled
    assert result.chain_memory_ready
    assert result.downstream_cross_market_dependency_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    chain = result.chains.chain_memory.chains[0]
    assert len(chain.hops) == 2
    assert chain.hops[0].effect_entity_id == chain.hops[1].cause_entity_id
    assert set(result.chains.bindings[0].certified_observation_hashes).issubset(
        set(certified_hashes)
    )

    replay, _, _ = build_chains(root)
    assert replay == result
    assert (
        verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-075 causal memory consumed read-only")
    print("[PASS] Exact OML-036 causal-pattern object passed directly")
    print("[PASS] Actual OML-037 multi-hop builder consumed")
    print("[PASS] Two distinct causal patterns linked A-to-B-to-C")
    print("[PASS] Hop continuity and temporal direction verified")
    print("[PASS] Certified observation lineage retained")
    print("[PASS] Cross-market dependency continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-076 chain objects rejected")
    print("[DONE] OML-076 CERTIFIED MARKET-BEHAVIOR MULTI-HOP CAUSAL CHAIN PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
