from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory import (
    build_oracle_memory_causal_observation,
    build_oracle_memory_causal_pattern,
    build_oracle_memory_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    CHAIN_STATUS_ESTABLISHED,
    OracleMemoryMultiHopCausalChainInvariantError,
    build_oracle_memory_multi_hop_causal_chain,
    build_oracle_memory_multi_hop_causal_chain_memory,
    verify_oracle_memory_multi_hop_causal_chain_memory,
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
    except OracleMemoryMultiHopCausalChainInvariantError:
        return

    raise AssertionError(f"tampered OML-025 {label} accepted")


def build_causal_memory(root: Path):
    fixture = load_module(
        root / "test_oml_024_oracle_memory_causal_pattern_memory.py",
        "oml_024_fixture_for_oml_025",
    )

    calibration_memory = fixture.build_calibration_memory(root)

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    observations_ab = (
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T14:00:00-05:00",
            effect_observed_at="2026-08-02T14:20:00-05:00",
            evidence_hashes=("4" * 64,),
            confidence=0.82,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T15:00:00-05:00",
            effect_observed_at="2026-08-02T15:20:00-05:00",
            evidence_hashes=("5" * 64,),
            confidence=0.80,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T16:00:00-05:00",
            effect_observed_at="2026-08-02T16:20:00-05:00",
            evidence_hashes=("6" * 64,),
            confidence=0.79,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    observations_bc = (
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T14:20:00-05:00",
            effect_observed_at="2026-08-02T14:40:00-05:00",
            evidence_hashes=("7" * 64,),
            confidence=0.81,
            calibrated_probability=0.77,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T15:20:00-05:00",
            effect_observed_at="2026-08-02T15:40:00-05:00",
            evidence_hashes=("8" * 64,),
            confidence=0.78,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T16:20:00-05:00",
            effect_observed_at="2026-08-02T16:40:00-05:00",
            evidence_hashes=("9" * 64,),
            confidence=0.76,
            calibrated_probability=0.73,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    pattern_ab = build_oracle_memory_causal_pattern(
        pattern_name="Demand shift causes inventory pressure",
        observations=observations_ab,
    )

    pattern_bc = build_oracle_memory_causal_pattern(
        pattern_name="Inventory pressure causes market repricing",
        observations=observations_bc,
    )

    causal_memory = build_oracle_memory_causal_pattern_memory(
        calibration_memory=calibration_memory,
        patterns=(pattern_ab, pattern_bc),
    )

    return causal_memory, pattern_ab, pattern_bc


def main() -> int:
    print("=" * 48)
    print(" OML-025 TEST")
    print(" MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    causal_memory, pattern_ab, pattern_bc = build_causal_memory(root)

    chain = build_oracle_memory_multi_hop_causal_chain(
        chain_name=(
            "Demand shift to inventory pressure to market repricing"
        ),
        patterns=(pattern_ab, pattern_bc),
    )

    assert chain.chain_status == CHAIN_STATUS_ESTABLISHED
    assert chain.hop_count == 2
    assert chain.origin_entity_id == pattern_ab.cause_entity_id
    assert chain.terminal_entity_id == pattern_bc.effect_entity_id
    assert chain.intermediate_entity_ids == (
        pattern_ab.effect_entity_id,
    )
    assert chain.hop_continuity_verified
    assert chain.temporal_direction_verified
    assert chain.unique_pattern_lineage_verified
    assert chain.deterministic_identity_verified
    assert chain.canonical_order_verified
    assert chain.minimum_confidence >= 0.70
    assert chain.minimum_support_rate == 1.0
    assert chain.minimum_temporal_precedence_rate == 1.0
    assert chain.total_evidence_depth == 6
    assert chain.total_contradiction_depth == 0
    assert not chain.persistence_authorized
    assert not chain.learning_update_authorized
    assert not chain.runtime_activation_authorized
    assert not chain.publication_authorized
    assert not chain.action_authorization_enabled
    assert not chain.qseries_execution_authorized
    assert chain.read_only

    memory = build_oracle_memory_multi_hop_causal_chain_memory(
        causal_memory=causal_memory,
        chains=(chain,),
    )

    assert memory.schema_version == "OML-025"
    assert memory.engine_id == "OML-025"
    assert memory.upstream_schema_version == "OML-024"
    assert memory.upstream_engine_id == "OML-024"
    assert memory.chain_count == 1
    assert memory.total_hop_count == 2
    assert memory.deterministic_identity_verified
    assert memory.canonical_chain_order_verified
    assert memory.hop_continuity_verified
    assert memory.temporal_direction_verified
    assert memory.pattern_lineage_verified
    assert memory.evidence_depth_reconciled
    assert memory.contradiction_depth_reconciled
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_multi_hop_causal_chain_memory(
        causal_memory=causal_memory,
        chains=(chain,),
    )

    assert replay == memory
    assert verify_oracle_memory_multi_hop_causal_chain_memory(memory)

    expect_rejection(
        lambda: build_oracle_memory_multi_hop_causal_chain(
            chain_name="Broken causal chain",
            patterns=(pattern_bc, pattern_ab),
        ),
        "broken hop continuity",
    )

    expect_rejection(
        lambda: verify_oracle_memory_multi_hop_causal_chain_memory(
            replace(memory, chain_count=2)
        ),
        "chain count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_multi_hop_causal_chain_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_multi_hop_causal_chain_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-024 causal pattern memory consumed")
    print("[PASS] Two causal patterns linked into one chain")
    print("[PASS] Hop continuity verified")
    print("[PASS] Temporal direction verified")
    print("[PASS] Pattern lineage retained")
    print("[PASS] Origin, intermediate, and terminal entities retained")
    print("[PASS] Confidence and support rates aggregated")
    print("[PASS] Evidence and contradiction depths reconciled")
    print("[PASS] Established multi-hop causal chain detected")
    print("[PASS] Multi-hop memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered multi-hop memories rejected")
    print("[DONE] OML-025 MULTI-HOP CAUSAL CHAIN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
