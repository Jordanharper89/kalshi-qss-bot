from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory import (
    CAUSAL_STATUS_CONTRADICTED,
    OracleMemoryCausalPattern,
    OracleMemoryCausalPatternMemory,
    verify_oracle_memory_causal_pattern,
    verify_oracle_memory_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-025"
ENGINE_ID = "OML-025"
POLICY_ID = "oracle-memory.multi-hop-causal-chain-memory.v1"

UPSTREAM_SCHEMA_VERSION = "OML-024"
UPSTREAM_ENGINE_ID = "OML-024"

CHAIN_STATUS_HYPOTHESIS = "hypothesis"
CHAIN_STATUS_SUPPORTED = "supported"
CHAIN_STATUS_CONTRADICTED = "contradicted"
CHAIN_STATUS_ESTABLISHED = "established"

ALLOWED_CHAIN_STATUSES = (
    CHAIN_STATUS_HYPOTHESIS,
    CHAIN_STATUS_SUPPORTED,
    CHAIN_STATUS_CONTRADICTED,
    CHAIN_STATUS_ESTABLISHED,
)


class OracleMemoryMultiHopCausalChainInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCausalHop:
    hop_index: int
    pattern_id: str
    cause_entity_id: str
    effect_entity_id: str
    causal_status: str
    aggregate_confidence: float
    empirical_support_rate: float
    temporal_precedence_rate: float
    evidence_depth: int
    contradiction_depth: int
    hop_hash: str


@dataclass(frozen=True)
class OracleMemoryMultiHopCausalChain:
    chain_id: str
    chain_name: str
    normalized_chain_name: str
    chain_status: str
    hops: tuple[OracleMemoryCausalHop, ...]
    hop_count: int
    origin_entity_id: str
    terminal_entity_id: str
    intermediate_entity_ids: tuple[str, ...]
    minimum_confidence: float
    average_confidence: float
    minimum_support_rate: float
    average_support_rate: float
    minimum_temporal_precedence_rate: float
    total_evidence_depth: int
    total_contradiction_depth: int
    hop_continuity_verified: bool
    temporal_direction_verified: bool
    unique_pattern_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_order_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    chain_hash: str


@dataclass(frozen=True)
class OracleMemoryMultiHopCausalChainMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    chains: tuple[OracleMemoryMultiHopCausalChain, ...]
    chain_count: int
    total_hop_count: int
    deterministic_identity_verified: bool
    canonical_chain_order_verified: bool
    hop_continuity_verified: bool
    temporal_direction_verified: bool
    pattern_lineage_verified: bool
    evidence_depth_reconciled: bool
    contradiction_depth_reconciled: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    next_certification_authorized: bool
    read_only: bool
    memory_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryMultiHopCausalChainInvariantError(
        "unsupported OML-025 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryMultiHopCausalChainInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-025 chain name cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-025 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryMultiHopCausalChainInvariantError(
            f"OML-025 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_causal_hop(
    *,
    pattern: OracleMemoryCausalPattern,
    hop_index: int,
) -> OracleMemoryCausalHop:
    verify_oracle_memory_causal_pattern(pattern)

    if (
        not isinstance(hop_index, int)
        or isinstance(hop_index, bool)
        or hop_index < 1
    ):
        _reject("OML-025 hop index invalid")

    body = {
        "hop_index": hop_index,
        "pattern_id": pattern.pattern_id,
        "cause_entity_id": pattern.cause_entity_id,
        "effect_entity_id": pattern.effect_entity_id,
        "causal_status": pattern.causal_status,
        "aggregate_confidence": pattern.aggregate_confidence,
        "empirical_support_rate": pattern.empirical_support_rate,
        "temporal_precedence_rate": pattern.temporal_precedence_rate,
        "evidence_depth": pattern.evidence_depth,
        "contradiction_depth": pattern.contradiction_depth,
    }

    hop = OracleMemoryCausalHop(
        **body,
        hop_hash=_stable_hash(body),
    )

    verify_oracle_memory_causal_hop(hop)
    return hop


def verify_oracle_memory_causal_hop(
    hop: OracleMemoryCausalHop,
) -> bool:
    body = asdict(hop)
    supplied = body.pop("hop_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-025 hop hash mismatch")

    if hop.hop_index < 1:
        _reject("OML-025 hop index invalid")

    for value, label in (
        (hop.pattern_id, "pattern id"),
        (hop.cause_entity_id, "cause entity id"),
        (hop.effect_entity_id, "effect entity id"),
        (hop.hop_hash, "hop hash"),
    ):
        _require_hash(value, label)

    if hop.cause_entity_id == hop.effect_entity_id:
        _reject("OML-025 self-causal hop forbidden")

    for value in (
        hop.aggregate_confidence,
        hop.empirical_support_rate,
        hop.temporal_precedence_rate,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-025 hop metric outside [0, 1]")

    if hop.evidence_depth < 1:
        _reject("OML-025 hop evidence depth invalid")

    if hop.contradiction_depth < 0:
        _reject("OML-025 hop contradiction depth invalid")

    return True


def _status_for(
    *,
    hops: Sequence[OracleMemoryCausalHop],
    minimum_support_rate: float,
    minimum_confidence: float,
) -> str:
    if any(
        hop.causal_status == CAUSAL_STATUS_CONTRADICTED
        for hop in hops
    ):
        return CHAIN_STATUS_CONTRADICTED

    if len(hops) >= 2 and minimum_support_rate >= 0.75:
        if minimum_confidence >= 0.70:
            return CHAIN_STATUS_ESTABLISHED

    if any(hop.empirical_support_rate > 0.0 for hop in hops):
        return CHAIN_STATUS_SUPPORTED

    return CHAIN_STATUS_HYPOTHESIS


def build_oracle_memory_multi_hop_causal_chain(
    *,
    chain_name: str,
    patterns: Sequence[OracleMemoryCausalPattern],
) -> OracleMemoryMultiHopCausalChain:
    normalized = _normalize(chain_name)

    ordered_patterns = tuple(patterns)

    if len(ordered_patterns) < 2:
        _reject("OML-025 chain requires at least two causal patterns")

    for pattern in ordered_patterns:
        verify_oracle_memory_causal_pattern(pattern)

    pattern_ids = tuple(pattern.pattern_id for pattern in ordered_patterns)

    if len(set(pattern_ids)) != len(pattern_ids):
        _reject("OML-025 duplicate causal patterns in chain")

    hops = tuple(
        build_oracle_memory_causal_hop(
            pattern=pattern,
            hop_index=index,
        )
        for index, pattern in enumerate(ordered_patterns, start=1)
    )

    for index in range(1, len(hops)):
        if hops[index - 1].effect_entity_id != hops[index].cause_entity_id:
            _reject("OML-025 causal hop continuity broken")

    origin_entity_id = hops[0].cause_entity_id
    terminal_entity_id = hops[-1].effect_entity_id
    intermediate_entity_ids = tuple(
        hop.effect_entity_id for hop in hops[:-1]
    )

    minimum_confidence = min(
        hop.aggregate_confidence for hop in hops
    )
    average_confidence = round(
        sum(hop.aggregate_confidence for hop in hops) / len(hops),
        12,
    )

    minimum_support_rate = min(
        hop.empirical_support_rate for hop in hops
    )
    average_support_rate = round(
        sum(hop.empirical_support_rate for hop in hops) / len(hops),
        12,
    )

    minimum_temporal_precedence_rate = min(
        hop.temporal_precedence_rate for hop in hops
    )

    chain_id = _stable_hash(
        {
            "normalized_chain_name": normalized,
            "pattern_ids": pattern_ids,
            "origin_entity_id": origin_entity_id,
            "terminal_entity_id": terminal_entity_id,
        }
    )

    chain_status = _status_for(
        hops=hops,
        minimum_support_rate=minimum_support_rate,
        minimum_confidence=minimum_confidence,
    )

    body = {
        "chain_id": chain_id,
        "chain_name": chain_name.strip(),
        "normalized_chain_name": normalized,
        "chain_status": chain_status,
        "hops": hops,
        "hop_count": len(hops),
        "origin_entity_id": origin_entity_id,
        "terminal_entity_id": terminal_entity_id,
        "intermediate_entity_ids": intermediate_entity_ids,
        "minimum_confidence": minimum_confidence,
        "average_confidence": average_confidence,
        "minimum_support_rate": minimum_support_rate,
        "average_support_rate": average_support_rate,
        "minimum_temporal_precedence_rate": (
            minimum_temporal_precedence_rate
        ),
        "total_evidence_depth": sum(
            hop.evidence_depth for hop in hops
        ),
        "total_contradiction_depth": sum(
            hop.contradiction_depth for hop in hops
        ),
        "hop_continuity_verified": True,
        "temporal_direction_verified": (
            minimum_temporal_precedence_rate == 1.0
        ),
        "unique_pattern_lineage_verified": True,
        "deterministic_identity_verified": True,
        "canonical_order_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    chain = OracleMemoryMultiHopCausalChain(
        **body,
        chain_hash=_stable_hash(body),
    )

    verify_oracle_memory_multi_hop_causal_chain(chain)
    return chain


def verify_oracle_memory_multi_hop_causal_chain(
    chain: OracleMemoryMultiHopCausalChain,
) -> bool:
    body = asdict(chain)
    supplied = body.pop("chain_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-025 chain hash mismatch")

    if chain.normalized_chain_name != _normalize(chain.chain_name):
        _reject("OML-025 chain normalization mismatch")

    for value, label in (
        (chain.chain_id, "chain id"),
        (chain.origin_entity_id, "origin entity id"),
        (chain.terminal_entity_id, "terminal entity id"),
        (chain.chain_hash, "chain hash"),
    ):
        _require_hash(value, label)

    if chain.chain_status not in ALLOWED_CHAIN_STATUSES:
        _reject("OML-025 chain status invalid")

    if chain.hop_count != len(chain.hops):
        _reject("OML-025 hop count mismatch")

    if chain.hop_count < 2:
        _reject("OML-025 chain too short")

    for index, hop in enumerate(chain.hops, start=1):
        verify_oracle_memory_causal_hop(hop)

        if hop.hop_index != index:
            _reject("OML-025 non-canonical hop index")

    for index in range(1, len(chain.hops)):
        if (
            chain.hops[index - 1].effect_entity_id
            != chain.hops[index].cause_entity_id
        ):
            _reject("OML-025 hop continuity violated")

    if chain.origin_entity_id != chain.hops[0].cause_entity_id:
        _reject("OML-025 origin entity mismatch")

    if chain.terminal_entity_id != chain.hops[-1].effect_entity_id:
        _reject("OML-025 terminal entity mismatch")

    expected_intermediates = tuple(
        hop.effect_entity_id for hop in chain.hops[:-1]
    )

    if chain.intermediate_entity_ids != expected_intermediates:
        _reject("OML-025 intermediate entity lineage mismatch")

    pattern_ids = tuple(hop.pattern_id for hop in chain.hops)

    if len(set(pattern_ids)) != len(pattern_ids):
        _reject("OML-025 duplicate pattern lineage")

    for value in (
        chain.minimum_confidence,
        chain.average_confidence,
        chain.minimum_support_rate,
        chain.average_support_rate,
        chain.minimum_temporal_precedence_rate,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-025 chain metric outside [0, 1]")

    expected_chain_id = _stable_hash(
        {
            "normalized_chain_name": chain.normalized_chain_name,
            "pattern_ids": pattern_ids,
            "origin_entity_id": chain.origin_entity_id,
            "terminal_entity_id": chain.terminal_entity_id,
        }
    )

    if chain.chain_id != expected_chain_id:
        _reject("OML-025 chain identity mismatch")

    required_true = (
        chain.hop_continuity_verified,
        chain.temporal_direction_verified,
        chain.unique_pattern_lineage_verified,
        chain.deterministic_identity_verified,
        chain.canonical_order_verified,
        chain.read_only,
    )

    if not all(required_true):
        _reject("OML-025 chain guarantee missing")

    forbidden = (
        chain.persistence_authorized,
        chain.learning_update_authorized,
        chain.runtime_activation_authorized,
        chain.publication_authorized,
        chain.action_authorization_enabled,
        chain.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-025 forbidden chain capability enabled")

    return True


def build_oracle_memory_multi_hop_causal_chain_memory(
    *,
    causal_memory: OracleMemoryCausalPatternMemory,
    chains: Sequence[OracleMemoryMultiHopCausalChain],
) -> OracleMemoryMultiHopCausalChainMemory:
    verify_oracle_memory_causal_pattern_memory(causal_memory)

    if causal_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-025 upstream schema mismatch")

    if causal_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-025 upstream engine mismatch")

    if not causal_memory.memory_ready:
        _reject("OML-025 upstream causal memory not ready")

    if not causal_memory.next_certification_authorized:
        _reject("OML-025 upstream continuation not authorized")

    if not causal_memory.read_only:
        _reject("OML-025 upstream causal memory not read-only")

    upstream_pattern_ids = {
        pattern.pattern_id for pattern in causal_memory.patterns
    }

    ordered = tuple(
        sorted(
            chains,
            key=lambda item: (
                item.normalized_chain_name,
                item.origin_entity_id,
                item.terminal_entity_id,
                item.chain_id,
            ),
        )
    )

    for chain in ordered:
        verify_oracle_memory_multi_hop_causal_chain(chain)

        if any(
            hop.pattern_id not in upstream_pattern_ids
            for hop in chain.hops
        ):
            _reject("OML-025 chain references unknown causal pattern")

    chain_ids = tuple(chain.chain_id for chain in ordered)

    if len(set(chain_ids)) != len(chain_ids):
        _reject("OML-025 duplicate chain identities")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": causal_memory.schema_version,
        "upstream_engine_id": causal_memory.engine_id,
        "upstream_memory_hash": causal_memory.memory_hash,
        "chains": ordered,
        "chain_count": len(ordered),
        "total_hop_count": sum(
            chain.hop_count for chain in ordered
        ),
        "deterministic_identity_verified": True,
        "canonical_chain_order_verified": True,
        "hop_continuity_verified": all(
            chain.hop_continuity_verified for chain in ordered
        ),
        "temporal_direction_verified": all(
            chain.temporal_direction_verified for chain in ordered
        ),
        "pattern_lineage_verified": True,
        "evidence_depth_reconciled": True,
        "contradiction_depth_reconciled": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    memory = OracleMemoryMultiHopCausalChainMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_multi_hop_causal_chain_memory(memory)
    return memory


def verify_oracle_memory_multi_hop_causal_chain_memory(
    memory: OracleMemoryMultiHopCausalChainMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-025 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-025 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-025 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-025 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-025 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-025 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-025 upstream engine lineage mismatch")

    if memory.chain_count != len(memory.chains):
        _reject("OML-025 chain count mismatch")

    if memory.total_hop_count != sum(
        chain.hop_count for chain in memory.chains
    ):
        _reject("OML-025 total hop count mismatch")

    chain_ids = []

    for chain in memory.chains:
        verify_oracle_memory_multi_hop_causal_chain(chain)
        chain_ids.append(chain.chain_id)

    if len(set(chain_ids)) != len(chain_ids):
        _reject("OML-025 duplicate memory chain identities")

    required_true = (
        memory.deterministic_identity_verified,
        memory.canonical_chain_order_verified,
        memory.hop_continuity_verified,
        memory.temporal_direction_verified,
        memory.pattern_lineage_verified,
        memory.evidence_depth_reconciled,
        memory.contradiction_depth_reconciled,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-025 memory guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-025 forbidden memory capability enabled")

    return True
