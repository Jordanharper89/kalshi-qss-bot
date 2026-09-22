from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076 import (
    OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076,
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyMemory,
    OracleMemoryCertifiedCrossMarketObservationRequest,
    build_oracle_memory_certified_cross_market_dependency_memory,
    verify_oracle_memory_certified_cross_market_dependency_memory,
    verify_oracle_memory_certified_cross_market_observation_request,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-077"
ENGINE_ID = "OML-077"
POLICY_ID = (
    "oracle-memory.certified-market-behavior-"
    "cross-market-dependency-memory-077.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-076"
UPSTREAM_ENGINE_ID = "OML-076"
DEPENDENCY_SCHEMA_VERSION = "OML-038"
DEPENDENCY_ENGINE_ID = "OML-038"
STATE_READ_ONLY = (
    "read_only_market_behavior_cross_market_dependency_memory_077"
)


class OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077:
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
    dependencies: OracleMemoryCertifiedCrossMarketDependencyMemory
    dependency_count: int
    total_observation_count: int
    source_market_count: int
    target_market_count: int
    state: str
    chain_lineage_verified: bool
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
    downstream_freeze_certification_authorized: bool
    read_only: bool
    certification_hash: str


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
    raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(
        "unsupported OML-077 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(
        reason
    )


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-077 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorDependency077InvariantError(
            f"OML-077 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
    *,
    chains: OracleMemoryCertifiedMarketBehaviorMultiHopCausalChainMemory076,
    requests: Sequence[OracleMemoryCertifiedCrossMarketObservationRequest],
) -> OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077:
    verify_oracle_memory_certified_market_behavior_multi_hop_causal_chain_memory_076(
        chains
    )

    if chains.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-077 upstream schema mismatch")
    if chains.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-077 upstream engine mismatch")
    if not chains.chain_memory_ready:
        _reject("OML-077 upstream chain memory not ready")
    if not chains.downstream_cross_market_dependency_authorized:
        _reject("OML-077 dependency continuation not authorized")
    if not chains.read_only:
        _reject("OML-077 upstream chain memory not read-only")

    for request in requests:
        verify_oracle_memory_certified_cross_market_observation_request(
            request
        )

    dependencies = build_oracle_memory_certified_cross_market_dependency_memory(
        chains=chains.chains,
        requests=tuple(requests),
    )
    verify_oracle_memory_certified_cross_market_dependency_memory(
        dependencies
    )

    if dependencies.schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-077 dependency schema mismatch")
    if dependencies.engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-077 dependency engine mismatch")
    if dependencies.upstream_certification_hash != (
        chains.chains.certification_hash
    ):
        _reject("OML-077 chain certification lineage mismatch")
    if dependencies.upstream_chain_memory_hash != (
        chains.chains.chain_memory.memory_hash
    ):
        _reject("OML-077 chain memory lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": chains.schema_version,
        "upstream_engine_id": chains.engine_id,
        "upstream_certification_hash": chains.certification_hash,
        "upstream_chain_certification_hash": (
            chains.chains.certification_hash
        ),
        "upstream_chain_memory_hash": (
            chains.chains.chain_memory.memory_hash
        ),
        "dependency_schema_version": dependencies.schema_version,
        "dependency_engine_id": dependencies.engine_id,
        "dependencies": dependencies,
        "dependency_count": dependencies.dependency_count,
        "total_observation_count": dependencies.total_observation_count,
        "source_market_count": dependencies.source_market_count,
        "target_market_count": dependencies.target_market_count,
        "state": STATE_READ_ONLY,
        "chain_lineage_verified": dependencies.chain_lineage_verified,
        "certified_observation_lineage_verified": (
            dependencies.certified_observation_lineage_verified
        ),
        "deterministic_identity_verified": (
            dependencies.deterministic_identity_verified
        ),
        "canonical_dependency_order_verified": (
            dependencies.canonical_dependency_order_verified
        ),
        "lead_lag_direction_verified": (
            dependencies.lead_lag_direction_verified
        ),
        "evidence_lineage_verified": (
            dependencies.evidence_lineage_verified
        ),
        "contradiction_tracking_verified": (
            dependencies.contradiction_tracking_verified
        ),
        "calibration_lineage_verified": (
            dependencies.calibration_lineage_verified
        ),
        "outcome_reconciliation_verified": (
            dependencies.outcome_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "dependency_memory_ready": dependencies.memory_ready,
        "downstream_freeze_certification_authorized": True,
        "read_only": True,
    }

    result = (
        OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077(
            **body,
            certification_hash=_stable_hash(body),
        )
    )
    verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
        result
    )
    return result


def verify_oracle_memory_certified_market_behavior_cross_market_dependency_memory_077(
    result: OracleMemoryCertifiedMarketBehaviorCrossMarketDependencyMemory077,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-077 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-077 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-077 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-077 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-077 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-077 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-077 upstream engine lineage mismatch")
    if result.dependency_schema_version != DEPENDENCY_SCHEMA_VERSION:
        _reject("OML-077 dependency schema lineage mismatch")
    if result.dependency_engine_id != DEPENDENCY_ENGINE_ID:
        _reject("OML-077 dependency engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_chain_certification_hash,
        result.upstream_chain_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_certified_cross_market_dependency_memory(
        result.dependencies
    )

    if result.upstream_chain_certification_hash != (
        result.dependencies.upstream_certification_hash
    ):
        _reject("OML-077 chain certification mismatch")
    if result.upstream_chain_memory_hash != (
        result.dependencies.upstream_chain_memory_hash
    ):
        _reject("OML-077 chain memory mismatch")
    if result.dependency_count != result.dependencies.dependency_count:
        _reject("OML-077 dependency count mismatch")
    if result.total_observation_count != (
        result.dependencies.total_observation_count
    ):
        _reject("OML-077 observation count mismatch")
    if result.source_market_count != (
        result.dependencies.source_market_count
    ):
        _reject("OML-077 source market count mismatch")
    if result.target_market_count != (
        result.dependencies.target_market_count
    ):
        _reject("OML-077 target market count mismatch")

    required = (
        result.chain_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_dependency_order_verified,
        result.lead_lag_direction_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.calibration_lineage_verified,
        result.outcome_reconciliation_verified,
        result.dependency_memory_ready,
        result.downstream_freeze_certification_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-077 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-077 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-077 forbidden capability enabled")

    return True
