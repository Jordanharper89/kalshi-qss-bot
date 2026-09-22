from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    DEPENDENCY_STATUS_ESTABLISHED,
    OracleMemoryCrossMarketDependencyInvariantError,
    build_oracle_memory_cross_market_dependency,
    build_oracle_memory_cross_market_dependency_memory,
    build_oracle_memory_cross_market_observation,
    verify_oracle_memory_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    build_oracle_memory_multi_hop_causal_chain,
    build_oracle_memory_multi_hop_causal_chain_memory,
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
    except OracleMemoryCrossMarketDependencyInvariantError:
        return

    raise AssertionError(f"tampered OML-026 {label} accepted")


def build_chain_memory(root: Path):
    fixture = load_module(
        root
        / "test_oml_025_oracle_memory_multi_hop_causal_chain_memory.py",
        "oml_025_fixture_for_oml_026",
    )

    causal_memory, pattern_ab, pattern_bc = fixture.build_causal_memory(
        root
    )

    chain = build_oracle_memory_multi_hop_causal_chain(
        chain_name=(
            "Demand shift to inventory pressure to market repricing"
        ),
        patterns=(pattern_ab, pattern_bc),
    )

    memory = build_oracle_memory_multi_hop_causal_chain_memory(
        causal_memory=causal_memory,
        chains=(chain,),
    )

    return memory, chain


def main() -> int:
    print("=" * 48)
    print(" OML-026 TEST")
    print(" CROSS-MARKET DEPENDENCY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    chain_memory, chain = build_chain_memory(root)

    source_market_id = "a" * 64
    target_market_id = "b" * 64

    observations = (
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="1" * 64,
            target_event_hash="2" * 64,
            source_observed_at="2026-08-02T14:00:00-05:00",
            target_observed_at="2026-08-02T14:10:00-05:00",
            lag_seconds=600,
            evidence_hashes=("3" * 64,),
            confidence=0.82,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="4" * 64,
            target_event_hash="5" * 64,
            source_observed_at="2026-08-02T15:00:00-05:00",
            target_observed_at="2026-08-02T15:15:00-05:00",
            lag_seconds=900,
            evidence_hashes=("6" * 64,),
            confidence=0.80,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
        build_oracle_memory_cross_market_observation(
            source_market_id=source_market_id,
            target_market_id=target_market_id,
            source_event_hash="7" * 64,
            target_event_hash="8" * 64,
            source_observed_at="2026-08-02T16:00:00-05:00",
            target_observed_at="2026-08-02T16:20:00-05:00",
            lag_seconds=1200,
            evidence_hashes=("9" * 64,),
            contradicting_evidence_hashes=("c" * 64,),
            confidence=0.77,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            dependency_supported=True,
        ),
    )

    dependency = build_oracle_memory_cross_market_dependency(
        dependency_name=(
            "Energy market pressure leads inflation-market repricing"
        ),
        observations=observations,
        causal_chains=(chain,),
    )

    assert dependency.dependency_status == DEPENDENCY_STATUS_ESTABLISHED
    assert dependency.observation_count == 3
    assert dependency.confirmed_count == 3
    assert dependency.supported_count == 3
    assert dependency.contradicted_count == 0
    assert dependency.unresolved_count == 0
    assert dependency.average_lag_seconds == 900.0
    assert dependency.minimum_lag_seconds == 600
    assert dependency.maximum_lag_seconds == 1200
    assert dependency.empirical_support_rate == 1.0
    assert dependency.total_evidence_depth == 3
    assert dependency.total_contradiction_depth == 1
    assert dependency.lead_lag_direction_verified
    assert dependency.unique_chain_lineage_verified
    assert dependency.deterministic_identity_verified
    assert dependency.canonical_order_verified
    assert not dependency.persistence_authorized
    assert not dependency.learning_update_authorized
    assert not dependency.runtime_activation_authorized
    assert not dependency.publication_authorized
    assert not dependency.action_authorization_enabled
    assert not dependency.qseries_execution_authorized
    assert dependency.read_only

    memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(dependency,),
    )

    assert memory.schema_version == "OML-026"
    assert memory.engine_id == "OML-026"
    assert memory.upstream_schema_version == "OML-025"
    assert memory.upstream_engine_id == "OML-025"
    assert memory.dependency_count == 1
    assert memory.total_observation_count == 3
    assert memory.source_market_count == 1
    assert memory.target_market_count == 1
    assert memory.deterministic_identity_verified
    assert memory.canonical_dependency_order_verified
    assert memory.lead_lag_direction_verified
    assert memory.causal_chain_lineage_verified
    assert memory.evidence_lineage_verified
    assert memory.contradiction_tracking_verified
    assert memory.calibration_lineage_verified
    assert memory.outcome_reconciliation_verified
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(dependency,),
    )

    assert replay == memory
    assert verify_oracle_memory_cross_market_dependency_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, dependency_count=2)
        ),
        "dependency count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_cross_market_dependency_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-025 causal-chain memory consumed")
    print("[PASS] Source and target market identities retained")
    print("[PASS] Lead-lag temporal order enforced")
    print("[PASS] Cross-market lag statistics calculated")
    print("[PASS] Causal-chain lineage retained")
    print("[PASS] Evidence and contradiction lineage retained")
    print("[PASS] Calibrated probabilities retained")
    print("[PASS] Confirmed dependency outcomes reconciled")
    print("[PASS] Established cross-market dependency detected")
    print("[PASS] Dependency memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered dependency memories rejected")
    print("[DONE] OML-026 CROSS-MARKET DEPENDENCY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
