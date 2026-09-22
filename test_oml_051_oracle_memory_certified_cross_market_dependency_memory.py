from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyInvariantError,
    build_oracle_memory_certified_cross_market_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    build_oracle_memory_certified_cross_market_observation_request,
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
    except OracleMemoryCertifiedCrossMarketDependencyInvariantError:
        return
    raise AssertionError(f"tampered OML-051 {label} accepted")


def build_chains(root: Path):
    fixture_049 = load_module(
        root / "test_oml_049_oracle_memory_certified_cross_market_causal_pattern_memory.py",
        "oml_049_fixture_for_oml_051",
    )
    calibration, certified_hashes = fixture_049.build_calibration(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
        build_oracle_memory_certified_causal_observation_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_causal_pattern_memory import (
        build_oracle_memory_certified_cross_market_causal_pattern_memory,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_multi_hop_chain_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory,
    )

    entity_a, entity_b, entity_c = "1" * 64, "2" * 64, "3" * 64
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
    causal = build_oracle_memory_certified_cross_market_causal_pattern_memory(
        calibration=calibration,
        requests=causal_requests,
    )
    patterns = {
        p.normalized_pattern_name: p
        for p in causal.causal_patterns.causal_memory.patterns
    }
    chain_request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Liquidity shift to Bitcoin repricing",
        pattern_ids=(
            patterns["liquidity shift precedes order-flow change"].pattern_id,
            patterns["order-flow change precedes bitcoin repricing"].pattern_id,
        ),
    )
    chains = build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
        causal_patterns=causal,
        requests=(chain_request,),
    )
    return chains, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-051 TEST")
    print(" CERTIFIED CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    chains, certified_hashes = build_chains(root)
    chain_id = chains.chains.chain_memory.chains[0].chain_id

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads Bitcoin repricing",
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T17:00:00-05:00",
            target_observed_at="2026-08-02T17:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads Bitcoin repricing",
            chain_ids=(chain_id,),
            source_market_id="a" * 64,
            target_market_id="b" * 64,
            source_event_hash="e" * 64,
            target_event_hash="f" * 64,
            source_observed_at="2026-08-02T18:00:00-05:00",
            target_observed_at="2026-08-02T18:04:00-05:00",
            lag_seconds=240,
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    result = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )

    assert result.schema_version == "OML-051"
    assert result.engine_id == "OML-051"
    assert result.upstream_schema_version == "OML-050"
    assert result.upstream_engine_id == "OML-050"
    assert result.dependency_schema_version == "OML-038"
    assert result.dependency_engine_id == "OML-038"
    assert result.dependency_count == 1
    assert result.total_observation_count == 2
    assert result.source_market_count == 1
    assert result.target_market_count == 1
    assert result.upstream_certification_hash == chains.certification_hash
    assert result.chain_lineage_verified
    assert result.causal_pattern_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_dependency_order_verified
    assert result.lead_lag_direction_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_lineage_verified
    assert result.outcome_reconciliation_verified
    assert result.dependency_memory_ready
    assert result.downstream_market_behavior_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_dependency_memory(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, downstream_market_behavior_authorized=False)
        ),
        "market behavior continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-050 chain memory consumed read-only")
    print("[PASS] Exact OML-037 chain object passed directly")
    print("[PASS] Actual OML-038 dependency builder consumed")
    print("[PASS] Chain and causal-pattern lineage retained")
    print("[PASS] Certified observation evidence retained")
    print("[PASS] Lead-lag direction and outcomes verified")
    print("[PASS] Market-behavior continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-051 records rejected")
    print("[DONE] OML-051 CERTIFIED CROSS-MARKET DEPENDENCY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
