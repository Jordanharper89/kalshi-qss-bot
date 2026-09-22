from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_multi_hop_causal_chain_memory import (
    CHAIN_STATUS_ESTABLISHED,
    OracleMemoryMultiHopCausalChainInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
    build_oracle_memory_certified_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMultiHopCausalChainInvariantError,
    build_oracle_memory_certified_multi_hop_chain_request,
    build_oracle_memory_certified_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_multi_hop_causal_chain_memory,
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
        OracleMemoryCertifiedMultiHopCausalChainInvariantError,
        OracleMemoryMultiHopCausalChainInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-037 {label} accepted")


def build_causal_patterns(root: Path):
    fixture = load_module(
        root / "test_oml_036_oracle_memory_certified_observation_causal_pattern_memory.py",
        "oml_036_fixture_for_oml_037",
    )
    calibration, certified_hashes = fixture.build_calibration(root)

    entity_a = "1" * 64
    entity_b = "2" * 64
    entity_c = "3" * 64

    requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Demand shift precedes order-flow change",
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T14:00:00-05:00",
            effect_observed_at="2026-08-02T14:15:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.82,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Demand shift precedes order-flow change",
            cause_entity_id=entity_a,
            effect_entity_id=entity_b,
            cause_observed_at="2026-08-02T15:00:00-05:00",
            effect_observed_at="2026-08-02T15:15:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Order-flow change precedes market repricing",
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T14:20:00-05:00",
            effect_observed_at="2026-08-02T14:35:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.79,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Order-flow change precedes market repricing",
            cause_entity_id=entity_b,
            effect_entity_id=entity_c,
            cause_observed_at="2026-08-02T15:20:00-05:00",
            effect_observed_at="2026-08-02T15:35:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.77,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )
    return build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-037 TEST")
    print(" CERTIFIED OBSERVATION MULTI-HOP CAUSAL CHAIN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    causal_patterns = build_causal_patterns(root)
    ordered_patterns = sorted(
        causal_patterns.causal_memory.patterns,
        key=lambda item: item.cause_entity_id,
    )
    request = build_oracle_memory_certified_multi_hop_chain_request(
        chain_name="Real-world demand to market repricing chain",
        pattern_ids=tuple(item.pattern_id for item in ordered_patterns),
    )
    result = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(request,),
    )

    assert result.schema_version == "OML-037"
    assert result.engine_id == "OML-037"
    assert result.upstream_schema_version == "OML-036"
    assert result.upstream_engine_id == "OML-036"
    assert result.chain_schema_version == "OML-025"
    assert result.chain_engine_id == "OML-025"
    assert result.chain_count == 1
    assert result.total_hop_count == 2

    chain = result.chain_memory.chains[0]
    binding = result.bindings[0]
    assert chain.chain_status == CHAIN_STATUS_ESTABLISHED
    assert chain.hop_count == 2
    assert chain.hop_continuity_verified
    assert chain.temporal_direction_verified
    assert binding.pattern_ids == tuple(hop.pattern_id for hop in chain.hops)
    assert binding.upstream_certification_hash == causal_patterns.certification_hash
    assert binding.upstream_causal_memory_hash == causal_patterns.causal_memory.memory_hash
    assert binding.chain_memory_hash == result.chain_memory.memory_hash
    assert binding.certified_observation_hashes
    assert binding.causal_observation_hashes

    assert result.certified_observation_lineage_verified
    assert result.causal_pattern_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_chain_order_verified
    assert result.hop_continuity_verified
    assert result.temporal_direction_verified
    assert result.evidence_depth_reconciled
    assert result.contradiction_depth_reconciled
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_causal_replay_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns,
        requests=(request,),
    )
    assert replay == result
    assert verify_oracle_memory_certified_multi_hop_causal_chain_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_multi_hop_chain_request(
            chain_name="Broken",
            pattern_ids=(ordered_patterns[0].pattern_id,) * 2,
        ),
        "duplicate pattern request",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, downstream_causal_replay_authorized=False)
        ),
        "replay continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_multi_hop_causal_chain_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-036 causal pattern memory consumed read-only")
    print("[PASS] Exact OML-036 causal-memory dataclass passed directly")
    print("[PASS] Actual OML-025 chain builders consumed")
    print("[PASS] Two certified causal patterns linked into one chain")
    print("[PASS] Hop continuity and temporal direction verified")
    print("[PASS] Certified observation lineage retained across every hop")
    print("[PASS] Causal observation lineage retained across every hop")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Causal replay continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-037 chain memories rejected")
    print("[DONE] OML-037 CERTIFIED OBSERVATION MULTI-HOP CAUSAL CHAIN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
