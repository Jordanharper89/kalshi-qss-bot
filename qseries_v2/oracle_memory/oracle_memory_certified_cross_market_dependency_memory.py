from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_multi_hop_causal_chain_memory import (
    OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory,
    verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyMemory as InnerDependencyMemory,
    OracleMemoryCertifiedCrossMarketObservationRequest,
    build_oracle_memory_certified_cross_market_dependency_memory as build_inner_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory as verify_inner_dependency_memory,
    verify_oracle_memory_certified_cross_market_observation_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID

SCHEMA_VERSION = "OML-051"
ENGINE_ID = "OML-051"
POLICY_ID = "oracle-memory.certified-cross-market-dependency-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-050"
UPSTREAM_ENGINE_ID = "OML-050"
DEPENDENCY_SCHEMA_VERSION = "OML-038"
DEPENDENCY_ENGINE_ID = "OML-038"
STATE_READ_ONLY = "read_only_cross_market_dependency_memory"


class OracleMemoryCertifiedCrossMarketDependencyInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketDependencyMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_chain_certification_hash: str
    upstream_chain_memory_hash: str
    dependency_schema_version: str
    dependency_engine_id: str
    dependencies: InnerDependencyMemory
    dependency_count: int
    total_observation_count: int
    source_market_count: int
    target_market_count: int
    state: str
    chain_lineage_verified: bool
    causal_pattern_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_dependency_order_verified: bool
    lead_lag_direction_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    calibration_lineage_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    dependency_memory_ready: bool
    downstream_market_behavior_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedCrossMarketDependencyInvariantError("unsupported OML-051 value type")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedCrossMarketDependencyInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-051 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketDependencyInvariantError(
            f"OML-051 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_dependency_memory(
    *,
    chains: OracleMemoryCertifiedCrossMarketMultiHopCausalChainMemory,
    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],
) -> OracleMemoryCertifiedCrossMarketDependencyMemory:
    verify_oracle_memory_certified_cross_market_multi_hop_causal_chain_memory(chains)

    if chains.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-051 upstream schema mismatch")
    if chains.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-051 upstream engine mismatch")
    if not chains.chain_memory_ready:
        _reject("OML-051 upstream chain memory not ready")
    if not chains.downstream_cross_market_dependency_authorized:
        _reject("OML-051 dependency continuation not authorized")
    if not chains.read_only:
        _reject("OML-051 upstream chain memory not read-only")

    known_chain_ids = {item.chain_id for item in chains.chains.chain_memory.chains}
    if not known_chain_ids:
        _reject("OML-051 no certified chains available")

    for request in requests:
        verify_oracle_memory_certified_cross_market_observation_request(request)
        if not set(request.chain_ids).issubset(known_chain_ids):
            _reject("OML-051 request references unknown certified chain")

    dependencies = build_inner_dependency_memory(
        chains=chains.chains,
        requests=tuple(requests),
    )
    verify_inner_dependency_memory(dependencies)

    if dependencies.schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-051 dependency schema mismatch")
    if dependencies.engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-051 dependency engine mismatch")
    if dependencies.upstream_certification_hash != chains.chains.certification_hash:
        _reject("OML-051 chain certification lineage mismatch")
    if dependencies.upstream_chain_memory_hash != chains.chains.chain_memory.memory_hash:
        _reject("OML-051 chain memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": chains.schema_version,
        "upstream_engine_id": chains.engine_id,
        "upstream_certification_hash": chains.certification_hash,
        "upstream_chain_certification_hash": chains.chains.certification_hash,
        "upstream_chain_memory_hash": chains.chains.chain_memory.memory_hash,
        "dependency_schema_version": dependencies.schema_version,
        "dependency_engine_id": dependencies.engine_id,
        "dependencies": dependencies,
        "dependency_count": dependencies.dependency_count,
        "total_observation_count": dependencies.total_observation_count,
        "source_market_count": dependencies.source_market_count,
        "target_market_count": dependencies.target_market_count,
        "state": STATE_READ_ONLY,
        "chain_lineage_verified": dependencies.chain_lineage_verified,
        "causal_pattern_lineage_verified": chains.causal_pattern_lineage_verified,
        "certified_observation_lineage_verified": dependencies.certified_observation_lineage_verified,
        "deterministic_identity_verified": dependencies.deterministic_identity_verified,
        "canonical_dependency_order_verified": dependencies.canonical_dependency_order_verified,
        "lead_lag_direction_verified": dependencies.lead_lag_direction_verified,
        "evidence_lineage_verified": dependencies.evidence_lineage_verified,
        "contradiction_tracking_verified": dependencies.contradiction_tracking_verified,
        "calibration_lineage_verified": dependencies.calibration_lineage_verified,
        "outcome_reconciliation_verified": dependencies.outcome_reconciliation_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "dependency_memory_ready": True,
        "downstream_market_behavior_authorized": dependencies.downstream_market_behavior_authorized,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketDependencyMemory(
        **body, certification_hash=_stable_hash(body)
    )
    verify_oracle_memory_certified_cross_market_dependency_memory(result)
    return result


def verify_oracle_memory_certified_cross_market_dependency_memory(
    result: OracleMemoryCertifiedCrossMarketDependencyMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-051 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID:
        _reject("OML-051 identity mismatch")
    if result.policy_id != POLICY_ID or result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-051 policy or subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-051 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-051 upstream engine lineage mismatch")
    if result.dependency_schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-051 dependency schema lineage mismatch")
    if result.dependency_engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-051 dependency engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_chain_certification_hash,
        result.upstream_chain_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_inner_dependency_memory(result.dependencies)

    if result.upstream_chain_certification_hash != result.dependencies.upstream_certification_hash:
        _reject("OML-051 chain certification mismatch")
    if result.upstream_chain_memory_hash != result.dependencies.upstream_chain_memory_hash:
        _reject("OML-051 chain memory mismatch")
    if result.dependency_count != result.dependencies.dependency_count:
        _reject("OML-051 dependency count mismatch")
    if result.total_observation_count != result.dependencies.total_observation_count:
        _reject("OML-051 observation count mismatch")
    if result.source_market_count != result.dependencies.source_market_count:
        _reject("OML-051 source market count mismatch")
    if result.target_market_count != result.dependencies.target_market_count:
        _reject("OML-051 target market count mismatch")

    required = (
        result.chain_lineage_verified,
        result.causal_pattern_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_dependency_order_verified,
        result.lead_lag_direction_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.calibration_lineage_verified,
        result.outcome_reconciliation_verified,
        result.dependency_memory_ready,
        result.downstream_market_behavior_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-051 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-051 state invalid")

    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-051 forbidden capability enabled")

    return True
