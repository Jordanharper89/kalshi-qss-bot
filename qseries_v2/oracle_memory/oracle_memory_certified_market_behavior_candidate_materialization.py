from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry_gate import (
    OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization_authorization_gate import (
    OracleMemoryMarketBehaviorMaterializationAuthorizationDecision,
    verify_oracle_memory_market_behavior_materialization_authorization_decision,
)
from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_market_behavior_intake_bridge import (
    OracleMemoryCertifiedCrossMarketMarketBehaviorIntakeBridge,
    verify_oracle_memory_certified_cross_market_market_behavior_intake_bridge,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    build_oracle_memory_observation_candidate_materialization_batch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import SUBSYSTEM_ID

SCHEMA_VERSION = "OML-054"
ENGINE_ID = "OML-054"
POLICY_ID = "oracle-memory.certified-market-behavior-candidate-materialization.v1"
AUTH_SCHEMA_VERSION = "OML-053"
AUTH_ENGINE_ID = "OML-053"
BRIDGE_SCHEMA_VERSION = "OML-052"
BRIDGE_ENGINE_ID = "OML-052"
MATERIALIZATION_SCHEMA_VERSION = "OML-028"
MATERIALIZATION_ENGINE_ID = "OML-028"
STATE_READ_ONLY = "read_only_market_behavior_candidate_materialization"


class OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCandidateMaterialization:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    authorization_schema_version: str
    authorization_engine_id: str
    authorization_decision_hash: str
    bridge_schema_version: str
    bridge_engine_id: str
    bridge_certification_hash: str
    intake_batch_hash: str
    registry_gate_decision_hash: str
    materialization_schema_version: str
    materialization_engine_id: str
    materialization_batch: OracleMemoryObservationCandidateMaterializationBatch
    observation_count: int
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    state: str
    authorization_lineage_verified: bool
    bridge_lineage_verified: bool
    registry_gate_lineage_verified: bool
    observation_candidate_lineage_verified: bool
    source_certification_lineage_verified: bool
    deterministic_materialization_verified: bool
    duplicate_detection_verified: bool
    candidate_admission_authorized: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    materialization_ready: bool
    downstream_validation_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError("unsupported OML-054 value type")


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-054 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorMaterializationInvariantError(f"OML-054 invalid {label} hexadecimal value") from exc


def build_oracle_memory_certified_market_behavior_candidate_materialization(
    *,
    authorization: OracleMemoryMarketBehaviorMaterializationAuthorizationDecision,
    bridge: OracleMemoryCertifiedCrossMarketMarketBehaviorIntakeBridge,
    registry_gate_decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
) -> OracleMemoryCertifiedMarketBehaviorCandidateMaterialization:
    verify_oracle_memory_market_behavior_materialization_authorization_decision(authorization)
    verify_oracle_memory_certified_cross_market_market_behavior_intake_bridge(bridge)
    verify_oracle_memory_canonical_record_admission_registry_gate_decision(registry_gate_decision)

    if authorization.schema_version != AUTH_SCHEMA_VERSION or authorization.engine_id != AUTH_ENGINE_ID:
        _reject("OML-054 authorization identity mismatch")
    if bridge.schema_version != BRIDGE_SCHEMA_VERSION or bridge.engine_id != BRIDGE_ENGINE_ID:
        _reject("OML-054 bridge identity mismatch")
    if authorization.upstream_certification_hash != bridge.certification_hash:
        _reject("OML-054 authorization-to-bridge certification mismatch")
    if authorization.upstream_intake_batch_hash != bridge.intake_batch.batch_hash:
        _reject("OML-054 authorization-to-intake lineage mismatch")
    if not authorization.candidate_materialization_authorized:
        _reject("OML-054 candidate materialization not authorized")
    if authorization.candidate_admission_authorized:
        _reject("OML-054 candidate admission unexpectedly authorized")
    if not authorization.read_only or not bridge.read_only:
        _reject("OML-054 upstream read-only guarantee missing")

    batch = build_oracle_memory_observation_candidate_materialization_batch(
        gate_decision=registry_gate_decision,
        intake_batch=bridge.intake_batch,
    )
    verify_oracle_memory_observation_candidate_materialization_batch(batch)

    if batch.schema_version != MATERIALIZATION_SCHEMA_VERSION or batch.engine_id != MATERIALIZATION_ENGINE_ID:
        _reject("OML-054 OML-028 materialization identity mismatch")
    if batch.upstream_batch_hash != bridge.intake_batch.batch_hash:
        _reject("OML-054 bridge-to-materialization batch mismatch")
    if batch.upstream_gate_decision_hash != registry_gate_decision.decision_hash:
        _reject("OML-054 registry gate lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "authorization_schema_version": authorization.schema_version,
        "authorization_engine_id": authorization.engine_id,
        "authorization_decision_hash": authorization.decision_hash,
        "bridge_schema_version": bridge.schema_version,
        "bridge_engine_id": bridge.engine_id,
        "bridge_certification_hash": bridge.certification_hash,
        "intake_batch_hash": bridge.intake_batch.batch_hash,
        "registry_gate_decision_hash": registry_gate_decision.decision_hash,
        "materialization_schema_version": batch.schema_version,
        "materialization_engine_id": batch.engine_id,
        "materialization_batch": batch,
        "observation_count": batch.observation_count,
        "candidate_count": batch.candidate_count,
        "unique_candidate_count": batch.unique_candidate_count,
        "duplicate_candidate_count": batch.duplicate_candidate_count,
        "state": STATE_READ_ONLY,
        "authorization_lineage_verified": True,
        "bridge_lineage_verified": True,
        "registry_gate_lineage_verified": True,
        "observation_candidate_lineage_verified": batch.observation_candidate_lineage_verified,
        "source_certification_lineage_verified": batch.source_certification_lineage_verified,
        "deterministic_materialization_verified": batch.deterministic_materialization_verified,
        "duplicate_detection_verified": batch.duplicate_detection_verified,
        "candidate_admission_authorized": False,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "materialization_ready": True,
        "downstream_validation_authorized": True,
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorCandidateMaterialization(**body, certification_hash=_stable_hash(body))
    verify_oracle_memory_certified_market_behavior_candidate_materialization(result)
    return result


def verify_oracle_memory_certified_market_behavior_candidate_materialization(
    result: OracleMemoryCertifiedMarketBehaviorCandidateMaterialization,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-054 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION or result.engine_id != ENGINE_ID or result.policy_id != POLICY_ID:
        _reject("OML-054 identity mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-054 subsystem mismatch")
    if result.authorization_schema_version != AUTH_SCHEMA_VERSION or result.authorization_engine_id != AUTH_ENGINE_ID:
        _reject("OML-054 authorization lineage mismatch")
    if result.bridge_schema_version != BRIDGE_SCHEMA_VERSION or result.bridge_engine_id != BRIDGE_ENGINE_ID:
        _reject("OML-054 bridge lineage mismatch")
    if result.materialization_schema_version != MATERIALIZATION_SCHEMA_VERSION or result.materialization_engine_id != MATERIALIZATION_ENGINE_ID:
        _reject("OML-054 materialization lineage mismatch")
    for value, label in (
        (result.authorization_decision_hash, "authorization decision hash"),
        (result.bridge_certification_hash, "bridge certification hash"),
        (result.intake_batch_hash, "intake batch hash"),
        (result.registry_gate_decision_hash, "registry gate decision hash"),
        (result.certification_hash, "certification hash"),
    ):
        _require_hash(value, label)
    verify_oracle_memory_observation_candidate_materialization_batch(result.materialization_batch)
    batch = result.materialization_batch
    if batch.upstream_batch_hash != result.intake_batch_hash:
        _reject("OML-054 intake batch lineage mismatch")
    if batch.upstream_gate_decision_hash != result.registry_gate_decision_hash:
        _reject("OML-054 gate decision lineage mismatch")
    if result.observation_count != batch.observation_count or result.candidate_count != batch.candidate_count:
        _reject("OML-054 count mismatch")
    if result.unique_candidate_count != batch.unique_candidate_count or result.duplicate_candidate_count != batch.duplicate_candidate_count:
        _reject("OML-054 duplicate count mismatch")
    if result.state != STATE_READ_ONLY:
        _reject("OML-054 state invalid")
    if not all((result.authorization_lineage_verified, result.bridge_lineage_verified, result.registry_gate_lineage_verified, result.observation_candidate_lineage_verified, result.source_certification_lineage_verified, result.deterministic_materialization_verified, result.duplicate_detection_verified, result.materialization_ready, result.downstream_validation_authorized, result.read_only)):
        _reject("OML-054 guarantee missing")
    if any((result.candidate_admission_authorized, result.persistence_enabled, result.learning_updates_enabled, result.runtime_activation_enabled, result.publication_enabled, result.action_authorization_enabled, result.qseries_execution_enabled)):
        _reject("OML-054 forbidden capability enabled")
    return True
