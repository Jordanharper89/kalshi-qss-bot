from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_observation_intake_bridge import (
    OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge,
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-066"
ENGINE_ID = "OML-066"
POLICY_ID = (
    "oracle-memory."
    "certified-market-behavior-candidate-materialization-authorization-gate.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-065"
UPSTREAM_ENGINE_ID = "OML-065"

DECISION_AUTHORIZED = "authorized_read_only_materialization"
STATE_CONTRACT_ONLY = "contract_only"


class OracleMemoryMarketBehaviorMaterializationAuthorizationInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryMarketBehaviorMaterializationAuthorizationDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_intake_batch_hash: str
    upstream_dependency_memory_hash: str
    upstream_observation_count: int
    upstream_unique_observation_count: int
    upstream_duplicate_observation_count: int
    decision: str
    state: str
    upstream_bridge_verified: bool
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_hashing_verified: bool
    canonical_order_verified: bool
    duplicate_detection_verified: bool
    source_certification_verified: bool
    candidate_materialization_authorized: bool
    candidate_admission_authorized: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    downstream_materialization_ready: bool
    read_only: bool
    decision_hash: str


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
    raise OracleMemoryMarketBehaviorMaterializationAuthorizationInvariantError(
        "unsupported OML-066 value type"
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
    raise OracleMemoryMarketBehaviorMaterializationAuthorizationInvariantError(
        reason
    )


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-066 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryMarketBehaviorMaterializationAuthorizationInvariantError(
            f"OML-066 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_market_behavior_materialization_authorization_decision(
    *,
    bridge: OracleMemoryCertifiedMarketBehaviorObservationIntakeBridge,
) -> OracleMemoryMarketBehaviorMaterializationAuthorizationDecision:
    verify_oracle_memory_certified_market_behavior_observation_intake_bridge(
        bridge
    )

    if bridge.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-066 upstream schema mismatch")
    if bridge.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-066 upstream engine mismatch")
    if not bridge.bridge_ready:
        _reject("OML-066 upstream bridge not ready")
    if not bridge.read_only:
        _reject("OML-066 upstream bridge not read-only")
    if bridge.observation_count <= 0:
        _reject("OML-066 upstream bridge contains no observations")
    if bridge.unique_observation_count <= 0:
        _reject("OML-066 upstream bridge contains no unique observations")
    if bridge.downstream_candidate_materialization_authorized:
        _reject("OML-066 upstream bridge bypassed authorization gate")

    required_upstream = (
        bridge.dependency_lineage_verified,
        bridge.chain_lineage_verified,
        bridge.certified_observation_lineage_verified,
        bridge.deterministic_hashing_verified,
        bridge.canonical_order_verified,
        bridge.duplicate_detection_verified,
        bridge.source_certification_verified,
    )
    if not all(required_upstream):
        _reject("OML-066 upstream guarantees incomplete")

    forbidden_upstream = (
        bridge.persistence_enabled,
        bridge.learning_updates_enabled,
        bridge.runtime_activation_enabled,
        bridge.publication_enabled,
        bridge.action_authorization_enabled,
        bridge.qseries_execution_enabled,
    )
    if any(forbidden_upstream):
        _reject("OML-066 upstream forbidden capability enabled")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": bridge.schema_version,
        "upstream_engine_id": bridge.engine_id,
        "upstream_certification_hash": bridge.certification_hash,
        "upstream_intake_batch_hash": bridge.intake_batch.batch_hash,
        "upstream_dependency_memory_hash": (
            bridge.upstream_dependency_memory_hash
        ),
        "upstream_observation_count": bridge.observation_count,
        "upstream_unique_observation_count": bridge.unique_observation_count,
        "upstream_duplicate_observation_count": (
            bridge.duplicate_observation_count
        ),
        "decision": DECISION_AUTHORIZED,
        "state": STATE_CONTRACT_ONLY,
        "upstream_bridge_verified": True,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_hashing_verified": True,
        "canonical_order_verified": True,
        "duplicate_detection_verified": True,
        "source_certification_verified": True,
        "candidate_materialization_authorized": True,
        "candidate_admission_authorized": False,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "downstream_materialization_ready": True,
        "read_only": True,
    }

    result = OracleMemoryMarketBehaviorMaterializationAuthorizationDecision(
        **body,
        decision_hash=_stable_hash(body),
    )
    verify_oracle_memory_market_behavior_materialization_authorization_decision(
        result
    )
    return result


def verify_oracle_memory_market_behavior_materialization_authorization_decision(
    decision: OracleMemoryMarketBehaviorMaterializationAuthorizationDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-066 decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-066 schema mismatch")
    if decision.engine_id != ENGINE_ID:
        _reject("OML-066 engine mismatch")
    if decision.policy_id != POLICY_ID:
        _reject("OML-066 policy mismatch")
    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-066 subsystem mismatch")
    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-066 upstream schema lineage mismatch")
    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-066 upstream engine lineage mismatch")

    for value, label in (
        (decision.upstream_certification_hash, "upstream certification hash"),
        (decision.upstream_intake_batch_hash, "upstream intake batch hash"),
        (
            decision.upstream_dependency_memory_hash,
            "upstream dependency memory hash",
        ),
        (decision.decision_hash, "decision hash"),
    ):
        _require_hash(value, label)

    if decision.decision != DECISION_AUTHORIZED:
        _reject("OML-066 decision invalid")
    if decision.state != STATE_CONTRACT_ONLY:
        _reject("OML-066 contract state invalid")
    if decision.upstream_observation_count <= 0:
        _reject("OML-066 observation count invalid")
    if decision.upstream_unique_observation_count <= 0:
        _reject("OML-066 unique observation count invalid")
    if decision.upstream_duplicate_observation_count < 0:
        _reject("OML-066 duplicate observation count invalid")
    if decision.upstream_observation_count != (
        decision.upstream_unique_observation_count
        + decision.upstream_duplicate_observation_count
    ):
        _reject("OML-066 observation-count reconciliation mismatch")

    required = (
        decision.upstream_bridge_verified,
        decision.dependency_lineage_verified,
        decision.chain_lineage_verified,
        decision.certified_observation_lineage_verified,
        decision.deterministic_hashing_verified,
        decision.canonical_order_verified,
        decision.duplicate_detection_verified,
        decision.source_certification_verified,
        decision.candidate_materialization_authorized,
        decision.downstream_materialization_ready,
        decision.read_only,
    )
    if not all(required):
        _reject("OML-066 authorization guarantee missing")

    forbidden = (
        decision.candidate_admission_authorized,
        decision.persistence_authorized,
        decision.learning_update_authorized,
        decision.runtime_activation_authorized,
        decision.publication_authorized,
        decision.action_authorization_enabled,
        decision.qseries_execution_authorized,
    )
    if any(forbidden):
        _reject("OML-066 forbidden capability enabled")

    return True
