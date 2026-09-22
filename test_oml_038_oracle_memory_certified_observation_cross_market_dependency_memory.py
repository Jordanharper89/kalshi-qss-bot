from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    DEPENDENCY_STATUS_ESTABLISHED,
    OracleMemoryCrossMarketDependencyInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyInvariantError,
    build_oracle_memory_certified_cross_market_observation_request,
    build_oracle_memory_certified_cross_market_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory,
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
        OracleMemoryCertifiedCrossMarketDependencyInvariantError,
        OracleMemoryCrossMarketDependencyInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-038 {label} accepted")


def build_chains(root: Path):
    fixture = load_module(
        root / "test_oml_037_oracle_memory_certified_observation_multi_hop_causal_chain_memory.py",
        "oml_037_fixture_for_oml_038",
    )
    return fixture.build_causal_patterns(root)


def main() -> int:
    print("=" * 48)
    print(" OML-038 TEST")
    print(" CERTIFIED OBSERVATION CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    causal_patterns = build_chains(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
        build_oracle_memory_certified_multi_hop_chain_request,
        build_oracle_memory_certified_multi_hop_causal_chain_memory,
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
    binding = chains.bindings[0]
    certified_hashes = binding.certified_observation_hashes

    source_market_id = "a" * 64
    target_market_id = "b" * 64

    requests = (
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=target_market_id,
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
            source_market_id=source_market_id,
            target_market_id=target_market_id,
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
        build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Prediction market leads crypto spot repricing",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="1" * 64,
            target_event_hash="2" * 64,
            source_observed_at="2026-08-02T16:00:00-05:00",
            target_observed_at="2026-08-02T16:06:00-05:00",
            lag_seconds=360,
            certified_observation_hashes=(certified_hashes[0],),
            contradicting_certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.79,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    result = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )

    assert result.schema_version == "OML-038"
    assert result.engine_id == "OML-038"
    assert result.upstream_schema_version == "OML-037"
    assert result.upstream_engine_id == "OML-037"
    assert result.dependency_schema_version == "OML-026"
    assert result.dependency_engine_id == "OML-026"
    assert result.dependency_count == 1
    assert result.total_observation_count == 3
    assert result.source_market_count == 1
    assert result.target_market_count == 1

    dependency = result.dependency_memory.dependencies[0]
    dependency_binding = result.bindings[0]

    assert dependency.dependency_status == DEPENDENCY_STATUS_ESTABLISHED
    assert dependency.observation_count == 3
    assert dependency.confirmed_count == 3
    assert dependency.supported_count == 3
    assert dependency.contradicted_count == 0
    assert dependency.empirical_support_rate == 1.0
    assert dependency.minimum_lag_seconds == 240
    assert dependency.maximum_lag_seconds == 360
    assert dependency.average_lag_seconds == 300.0

    assert dependency_binding.dependency_id == dependency.dependency_id
    assert dependency_binding.dependency_hash == dependency.dependency_hash
    assert dependency_binding.chain_ids == (chain.chain_id,)
    assert dependency_binding.upstream_certification_hash == (
        chains.certification_hash
    )
    assert dependency_binding.upstream_chain_memory_hash == (
        chains.chain_memory.memory_hash
    )
    assert dependency_binding.dependency_memory_hash == (
        result.dependency_memory.memory_hash
    )

    assert result.certified_observation_lineage_verified
    assert result.chain_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_dependency_order_verified
    assert result.lead_lag_direction_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_lineage_verified
    assert result.outcome_reconciliation_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_market_behavior_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_dependency_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_cross_market_observation_request(
            dependency_name="Broken",
            chain_ids=(chain.chain_id,),
            source_market_id=source_market_id,
            target_market_id=source_market_id,
            source_event_hash="c" * 64,
            target_event_hash="d" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:05:00-05:00",
            lag_seconds=300,
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.50,
            calibrated_probability=0.50,
            outcome_confirmed=False,
            dependency_supported=None,
        ),
        "self-market dependency",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_dependency_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
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

    print("[PASS] Certified OML-037 chain memory consumed read-only")
    print("[PASS] Exact OML-037 chain-memory dataclass passed directly")
    print("[PASS] Actual OML-026 dependency builders consumed")
    print("[PASS] Certified chain lineage bound to every dependency")
    print("[PASS] Certified observation lineage retained")
    print("[PASS] Cross-market lead-lag direction enforced")
    print("[PASS] Lag statistics and outcomes reconciled")
    print("[PASS] Established dependency detected")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Market-behavior continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-038 dependency memories rejected")
    print("[DONE] OML-038 CERTIFIED OBSERVATION CROSS-MARKET DEPENDENCY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
