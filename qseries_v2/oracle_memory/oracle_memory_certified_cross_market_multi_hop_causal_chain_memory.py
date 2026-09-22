from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_causal_pattern_memory import (
    OracleMemoryCertifiedCrossMarketCausalPatternMemory,
    verify_oracle_memory_certified_cross_market_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedMultiHopChainRequest,
    OracleMemoryCertifiedMultiHopCausalChainMemory,
    build_oracle_memory_certified_multi_hop_causal_chain_memory,
    verify_oracle_memory_certified_multi_hop_chain_request,
    verify_oracle_memory_certified_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-050"
ENGINE_ID = "OML-050"
POLICY_ID = (
    "oracle-memory."
    "certified-cross-market-multi-hop-causal-chain-memory.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-049"
UPSTREAM_ENGINE_ID = "OML-049"
CHAIN_SCHEMA_VERSION = "OML-037"
CHAIN_ENGINE_ID = "OML-037"
STATE_READ_ONLY = "read_only_cross_market_multi_hop_causal_chain_memory"


class OracleMemoryCertifiedCrossMarketChainInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_causal_certification_hash: str
    upstream_causal_memory_hash: str
    chain_schema_version: str
    chain_engine_id: str
    chains: OracleMemoryCertifiedMultiHopCausalChainMemory
    chain_count: int
    total_hop_count: int
    state: str
    causal_pattern_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_chain_order_verified: bool
    hop_continuity_verified: bool
    temporal_direction_verified: bool
    evidence_depth_reconciled: bool
    contradiction_depth_reconciled: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    chain_memory_ready: bool
    downstream_cross_market_dependency_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedCrossMarketChainInvariantError(
        "unsupported OML-050 value type"
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
    raise OracleMemoryCertifiedCrossMarketChainInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-050 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketChainInvariantError(
            f"OML-050 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
    *,
    causal_patterns: OracleMemoryCertifiedCrossMarketCausalPatternMemory,
    requests: Sequence[OracleMemoryCertifiedMultiHopChainRequest],
) -> OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory:
    verify_oracle_memory_certified_cross_market_causal_pattern_memory(
        causal_patterns
    )

    if causal_patterns.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-050 upstream schema mismatch")
    if causal_patterns.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-050 upstream engine mismatch")
    if not causal_patterns.causal_memory_ready:
        _reject("OML-050 upstream causal memory not ready")
    if not causal_patterns.downstream_multi_hop_causal_authorized:
        _reject("OML-050 multi-hop continuation not authorized")
    if not causal_patterns.read_only:
        _reject("OML-050 upstream causal memory not read-only")

    known_pattern_ids = {
        pattern.pattern_id
        for pattern in causal_patterns.causal_patterns.causal_memory.patterns
    }
    if not known_pattern_ids:
        _reject("OML-050 no certified causal patterns available")

    for request in requests:
        verify_oracle_memory_certified_multi_hop_chain_request(request)
        if not set(request.pattern_ids).issubset(known_pattern_ids):
            _reject("OML-050 chain references unknown causal pattern")

    chains = build_oracle_memory_certified_multi_hop_causal_chain_memory(
        causal_patterns=causal_patterns.causal_patterns,
        requests=tuple(requests),
    )
    verify_oracle_memory_certified_multi_hop_causal_chain_memory(chains)

    if chains.schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-050 chain schema mismatch")
    if chains.engine_id != CHAIN_ENGINE_ID:
        _reject("OML-050 chain engine mismatch")
    if chains.upstream_certification_hash != (
        causal_patterns.causal_patterns.certification_hash
    ):
        _reject("OML-050 causal certification lineage mismatch")
    if chains.upstream_causal_memory_hash != (
        causal_patterns.causal_patterns.causal_memory.memory_hash
    ):
        _reject("OML-050 causal memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": causal_patterns.schema_version,
        "upstream_engine_id": causal_patterns.engine_id,
        "upstream_certification_hash": causal_patterns.certification_hash,
        "upstream_causal_certification_hash": (
            causal_patterns.causal_patterns.certification_hash
        ),
        "upstream_causal_memory_hash": (
            causal_patterns.causal_patterns.causal_memory.memory_hash
        ),
        "chain_schema_version": chains.schema_version,
        "chain_engine_id": chains.engine_id,
        "chains": chains,
        "chain_count": chains.chain_count,
        "total_hop_count": chains.total_hop_count,
        "state": STATE_READ_ONLY,
        "causal_pattern_lineage_verified": (
            chains.causal_pattern_lineage_verified
        ),
        "certified_observation_lineage_verified": (
            chains.certified_observation_lineage_verified
        ),
        "deterministic_identity_verified": (
            chains.deterministic_identity_verified
        ),
        "canonical_chain_order_verified": (
            chains.canonical_chain_order_verified
        ),
        "hop_continuity_verified": chains.hop_continuity_verified,
        "temporal_direction_verified": chains.temporal_direction_verified,
        "evidence_depth_reconciled": chains.evidence_depth_reconciled,
        "contradiction_depth_reconciled": (
            chains.contradiction_depth_reconciled
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "chain_memory_ready": True,
        "downstream_cross_market_dependency_authorized": True,
        "read_only": True,
    }

    result = OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
        result
    )
    return result


def verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(
    result: OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-050 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-050 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-050 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-050 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-050 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-050 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-050 upstream engine lineage mismatch")
    if result.chain_schema_version != CHAIN_SCHEMA_VERSION:
        _reject("OML-050 chain schema lineage mismatch")
    if result.chain_engine_id != CHAIN_ENGINE_ID:
        _reject("OML-050 chain engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_causal_certification_hash,
        result.upstream_causal_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_multi_hop_causal_chain_memory(
        result.chains
    )

    if result.upstream_causal_certification_hash != (
        result.chains.upstream_certification_hash
    ):
        _reject("OML-050 causal certification mismatch")
    if result.upstream_causal_memory_hash != (
        result.chains.upstream_causal_memory_hash
    ):
        _reject("OML-050 causal memory mismatch")
    if result.chain_count != result.chains.chain_count:
        _reject("OML-050 chain count mismatch")
    if result.total_hop_count != result.chains.total_hop_count:
        _reject("OML-050 hop count mismatch")

    required = (
        result.causal_pattern_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_chain_order_verified,
        result.hop_continuity_verified,
        result.temporal_direction_verified,
        result.evidence_depth_reconciled,
        result.contradiction_depth_reconciled,
        result.chain_memory_ready,
        result.downstream_cross_market_dependency_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-050 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-050 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-050 forbidden capability enabled")

    return True
