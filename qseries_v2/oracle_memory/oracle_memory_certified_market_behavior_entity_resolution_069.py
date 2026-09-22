from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission_068 import (
    OracleMemoryCertifiedMarketBehaviorCandidateAdmission068,
    verify_oracle_memory_certified_market_behavior_candidate_admission_068,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    OracleMemoryObservationEntityResolution,
    build_oracle_memory_observation_entity_resolution,
    verify_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-069"
ENGINE_ID = "OML-069"
POLICY_ID = "oracle-memory.certified-market-behavior-entity-resolution-069.v1"
UPSTREAM_SCHEMA_VERSION = "OML-068"
UPSTREAM_ENGINE_ID = "OML-068"
RESOLUTION_SCHEMA_VERSION = "OML-030"
RESOLUTION_ENGINE_ID = "OML-030"
STATE_READ_ONLY = "read_only_market_behavior_entity_resolution_069"


class OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorEntityResolution069:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_admission_batch_hash: str
    upstream_materialization_batch_hash: str
    upstream_validation_batch_hash: str
    resolution_schema_version: str
    resolution_engine_id: str
    resolution: OracleMemoryObservationEntityResolution
    admitted_candidate_count: int
    rejected_duplicate_count: int
    resolved_entity_count: int
    state: str
    admission_lineage_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    observation_entity_lineage_verified: bool
    duplicate_candidates_excluded: bool
    deterministic_resolution_verified: bool
    entity_identity_uniqueness_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    resolution_ready: bool
    downstream_relationship_graph_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError(
        "unsupported OML-069 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-069 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorEntityResolution069InvariantError(
            f"OML-069 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_entity_resolution_069(
    *,
    admission: OracleMemoryCertifiedMarketBehaviorCandidateAdmission068,
    materialization_batch: OracleMemoryObservationCandidateMaterializationBatch,
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryCertifiedMarketBehaviorEntityResolution069:
    verify_oracle_memory_certified_market_behavior_candidate_admission_068(admission)
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if admission.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-069 upstream schema mismatch")
    if admission.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-069 upstream engine mismatch")
    if not admission.admission_ready:
        _reject("OML-069 upstream admission not ready")
    if not admission.downstream_entity_resolution_authorized:
        _reject("OML-069 entity-resolution continuation not authorized")
    if not admission.read_only:
        _reject("OML-069 upstream admission not read-only")

    if materialization_batch.batch_hash != (
        admission.upstream_materialization_batch_hash
    ):
        _reject("OML-069 materialization batch lineage mismatch")
    if validation_batch.batch_hash != admission.validation_batch_hash:
        _reject("OML-069 validation batch lineage mismatch")
    resolution = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission.admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash=aliases_by_candidate_hash,
    )
    verify_oracle_memory_observation_entity_resolution(resolution)

    if resolution.schema_version != RESOLUTION_SCHEMA_VERSION:
        _reject("OML-069 resolution schema mismatch")
    if resolution.engine_id != RESOLUTION_ENGINE_ID:
        _reject("OML-069 resolution engine mismatch")
    if resolution.upstream_admission_batch_hash != (
        admission.admission_batch.batch_hash
    ):
        _reject("OML-069 admission-to-resolution lineage mismatch")
    if resolution.upstream_materialization_batch_hash != (
        materialization_batch.batch_hash
    ):
        _reject("OML-069 materialization-to-resolution lineage mismatch")
    if resolution.upstream_validation_batch_hash != validation_batch.batch_hash:
        _reject("OML-069 validation-to-resolution lineage mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission.schema_version,
        "upstream_engine_id": admission.engine_id,
        "upstream_certification_hash": admission.certification_hash,
        "upstream_admission_batch_hash": admission.admission_batch.batch_hash,
        "upstream_materialization_batch_hash": materialization_batch.batch_hash,
        "upstream_validation_batch_hash": validation_batch.batch_hash,
        "resolution_schema_version": resolution.schema_version,
        "resolution_engine_id": resolution.engine_id,
        "resolution": resolution,
        "admitted_candidate_count": resolution.admitted_candidate_count,
        "rejected_duplicate_count": resolution.rejected_duplicate_count,
        "resolved_entity_count": resolution.resolved_entity_count,
        "state": STATE_READ_ONLY,
        "admission_lineage_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "observation_entity_lineage_verified": (
            resolution.observation_entity_lineage_verified
        ),
        "duplicate_candidates_excluded": resolution.duplicate_candidates_excluded,
        "deterministic_resolution_verified": (
            resolution.deterministic_resolution_verified
        ),
        "entity_identity_uniqueness_verified": (
            resolution.entity_identity_uniqueness_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "resolution_ready": True,
        "downstream_relationship_graph_authorized": (
            resolution.downstream_relationship_graph_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorEntityResolution069(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_entity_resolution_069(result)
    return result


def verify_oracle_memory_certified_market_behavior_entity_resolution_069(
    result: OracleMemoryCertifiedMarketBehaviorEntityResolution069,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-069 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-069 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-069 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-069 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-069 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-069 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-069 upstream engine lineage mismatch")
    if result.resolution_schema_version != RESOLUTION_SCHEMA_VERSION:
        _reject("OML-069 resolution schema lineage mismatch")
    if result.resolution_engine_id != RESOLUTION_ENGINE_ID:
        _reject("OML-069 resolution engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_admission_batch_hash,
        result.upstream_materialization_batch_hash,
        result.upstream_validation_batch_hash,
        result.certification_hash,
    ):
        _require_hash(value, "lineage hash")

    verify_oracle_memory_observation_entity_resolution(result.resolution)

    if result.upstream_admission_batch_hash != (
        result.resolution.upstream_admission_batch_hash
    ):
        _reject("OML-069 admission lineage mismatch")
    if result.upstream_materialization_batch_hash != (
        result.resolution.upstream_materialization_batch_hash
    ):
        _reject("OML-069 materialization lineage mismatch")
    if result.upstream_validation_batch_hash != (
        result.resolution.upstream_validation_batch_hash
    ):
        _reject("OML-069 validation lineage mismatch")
    if result.admitted_candidate_count != result.resolution.admitted_candidate_count:
        _reject("OML-069 admitted count mismatch")
    if result.rejected_duplicate_count != result.resolution.rejected_duplicate_count:
        _reject("OML-069 duplicate count mismatch")
    if result.resolved_entity_count != result.resolution.resolved_entity_count:
        _reject("OML-069 entity count mismatch")

    required = (
        result.admission_lineage_verified,
        result.materialization_lineage_verified,
        result.validation_lineage_verified,
        result.observation_entity_lineage_verified,
        result.duplicate_candidates_excluded,
        result.deterministic_resolution_verified,
        result.entity_identity_uniqueness_verified,
        result.resolution_ready,
        result.downstream_relationship_graph_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-069 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-069 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-069 forbidden capability enabled")

    return True
