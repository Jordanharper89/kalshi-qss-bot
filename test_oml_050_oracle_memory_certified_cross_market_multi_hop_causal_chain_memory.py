from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedCrossMarketChainInvariantError,
    build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    build_oracle_memory_certified_multi_hop_chain_request,
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
    except OracleMemoryCertifiedCrossMarketChainInvariantError:
        return
    raise AssertionError(f"tampered OML-050 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-050 TEST")
    print(" CERTIFIED CROSS-MARKET MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_049_oracle_memory_certified_cross_market_causal_pattern_memory.py",
        "oml_049_fixture_for_oml_050",
    )
    calibration, certified_hashes = fixture.build_calibration(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
        build_oracle_memory_certified_causal_observation_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_causal_pattern_memory import (
        build_oracle_memory_certified_cross_market_causal_pattern_memory,
    )

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    causal_requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Liquidity shift precedes order-flow change",
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T17:00:00-05:00",
            effect_observed_at="2026-08-02T17:05:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Order-flow change precedes Bitcoin repricing",
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T17:06:00-05:00",
            effect_observed_at="2026-08-02T17:10:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    causal_patterns = (
        build_oracle_memory_certified_cross_market_causal_pattern_memory(
            calibration=calibration,
            requests=causal_requests,
        )
    )

    patterns = {
        item.normalized_pattern_name: item
        for item in causal_patterns.causal_patterns.causal_memory.patterns
    }
    ordered_pattern_ids = (
        patterns["liquidity shift precedes order-flow change"].pattern_id,
        patterns["order-flow change precedes bitcoin repricing"].pattern_id,
    )

    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Liquidity shift to Bitcoin repricing",
        pattern_ids=ordered_pattern_ids,
    )

    result = (
        build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )

    assert result.schema_version == "OML-050"
    assert result.engine_id == "OML-050"
    assert result.upstream_schema_version == "OML-049"
    assert result.upstream_engine_id == "OML-049"
    assert result.chain_schema_version == "OML-037"
    assert result.chain_engine_id == "OML-037"
    assert result.chain_count == 1
    assert result.total_hop_count == 2
    assert result.upstream_certification_hash == (
        causal_patterns.certification_hash
    )
    assert result.causal_pattern_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_chain_order_verified
    assert result.hop_continuity_verified
    assert result.temporal_direction_verified
    assert result.evidence_depth_reconciled
    assert result.contradiction_depth_reconciled
    assert result.chain_memory_ready
    assert result.downstream_cross_market_dependency_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = (
        build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            causal_patterns=causal_patterns,
            requests=(chain_request,),
        )
    )
    assert replay == result
    assert (
        verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            result
        )
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            replace(
                result,
                downstream_cross_market_dependency_authorized=False,
            )
        ),
        "cross-market continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-049 causal memory consumed read-only")
    print("[PASS] Exact OML-036 causal-pattern object passed directly")
    print("[PASS] Actual OML-037 chain builder consumed")
    print("[PASS] Two certified causal patterns linked into one chain")
    print("[PASS] Hop continuity and temporal direction verified")
    print("[PASS] Certified observation lineage retained across every hop")
    print("[PASS] Cross-market dependency continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-050 records rejected")
    print(
        "[DONE] OML-050 CERTIFIED CROSS-MARKET "
        "MULTI-HOP CAUSAL CHAIN MEMORY PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
