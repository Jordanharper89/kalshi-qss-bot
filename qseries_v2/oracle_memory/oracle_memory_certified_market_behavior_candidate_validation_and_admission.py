from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_materialization import (
    OracleMemoryCertifiedMarketBehaviorCandidateMaterialization,
    verify_oracle_memory_certified_market_behavior_candidate_materialization,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    OracleMemoryObservationCandidateAdmissionBatch,
    build_oracle_memory_observation_candidate_admission_batch,
    verify_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-055"
ENGINE_ID = "OML-055"
POLICY_ID = (
    "oracle-memory."
    "certified-market-behavior-candidate-validation-and-admission.v1"
)
UPSTREAM_SCHEMA_VERSION = "OML-054"
UPSTREAM_ENGINE_ID = "OML-054"
VALIDATION_SCHEMA_VERSION = "OML-017"
VALIDATION_ENGINE_ID = "OML-017"
ADMISSION_SCHEMA_VERSION = "OML-029"
ADMISSION_ENGINE_ID = "OML-029"
STATE_READ_ONLY = "read_only_market_behavior_candidate_validation_and_admission"


class OracleMemoryCertifiedMarketBehaviorAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedMarketBehaviorCandidateAdmission:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_materialization_batch_hash: str
    validation_schema_version: str
    validation_engine_id: str
    validation_batch_hash: str
    admission_schema_version: str
    admission_engine_id: str
    admission_batch: OracleMemoryObservationCandidateAdmissionBatch
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    admission_count: int
    admitted_count: int
    rejected_duplicate_count: int
    state: str
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    observation_candidate_lineage_verified: bool
    duplicate_policy_verified: bool
    deterministic_admission_verified: bool
    candidate_admission_authorized: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    admission_ready: bool
    downstream_entity_resolution_authorized: bool
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
    raise OracleMemoryCertifiedMarketBehaviorAdmissionInvariantError(
        "unsupported OML-055 value type"
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
    raise OracleMemoryCertifiedMarketBehaviorAdmissionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-055 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedMarketBehaviorAdmissionInvariantError(
            f"OML-055 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_market_behavior_candidate_admission(
    *,
    materialization: OracleMemoryCertifiedMarketBehaviorCandidateMaterialization,
    validation_batch: OracleMemoryCandidateValidationBatch,
) -> OracleMemoryCertifiedMarketBehaviorCandidateAdmission:
    verify_oracle_memory_certified_market_behavior_candidate_materialization(
        materialization
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if materialization.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-055 upstream schema mismatch")
    if materialization.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-055 upstream engine mismatch")
    if not materialization.materialization_ready:
        _reject("OML-055 materialization not ready")
    if not materialization.downstream_validation_authorized:
        _reject("OML-055 validation continuation not authorized")
    if not materialization.read_only:
        _reject("OML-055 materialization not read-only")
    if materialization.candidate_admission_authorized:
        _reject("OML-055 upstream bypassed admission boundary")

    if validation_batch.schema_version != VALIDATION_SCHEMA_VERSION:
        _reject("OML-055 validation schema mismatch")
    if validation_batch.engine_id != VALIDATION_ENGINE_ID:
        _reject("OML-055 validation engine mismatch")
    if not validation_batch.batch_ready:
        _reject("OML-055 validation batch not ready")
    if not validation_batch.next_certification_authorized:
        _reject("OML-055 validation continuation not authorized")
    if not validation_batch.read_only:
        _reject("OML-055 validation batch not read-only")

    materialized_hashes = tuple(
        candidate.candidate_hash
        for candidate in materialization.materialization_batch.candidates
    )
    validation_hashes = tuple(
        result.candidate_hash for result in validation_batch.results
    )
    if tuple(sorted(materialized_hashes)) != tuple(sorted(validation_hashes)):
        _reject("OML-055 materialization/validation candidate mismatch")

    forbidden_validation = (
        validation_batch.persistence_enabled,
        validation_batch.learning_updates_enabled,
        validation_batch.runtime_activation_enabled,
        validation_batch.publication_enabled,
        validation_batch.action_authorization_enabled,
        validation_batch.qseries_execution_enabled,
    )
    if any(forbidden_validation):
        _reject("OML-055 validation forbidden capability enabled")

    admission_batch = (
        build_oracle_memory_observation_candidate_admission_batch(
            materialization_batch=materialization.materialization_batch,
            validation_batch=validation_batch,
        )
    )
    verify_oracle_memory_observation_candidate_admission_batch(
        admission_batch
    )

    if admission_batch.schema_version != ADMISSION_SCHEMA_VERSION:
        _reject("OML-055 admission schema mismatch")
    if admission_batch.engine_id != ADMISSION_ENGINE_ID:
        _reject("OML-055 admission engine mismatch")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": materialization.schema_version,
        "upstream_engine_id": materialization.engine_id,
        "upstream_certification_hash": materialization.certification_hash,
        "upstream_materialization_batch_hash": (
            materialization.materialization_batch.batch_hash
        ),
        "validation_schema_version": validation_batch.schema_version,
        "validation_engine_id": validation_batch.engine_id,
        "validation_batch_hash": validation_batch.batch_hash,
        "admission_schema_version": admission_batch.schema_version,
        "admission_engine_id": admission_batch.engine_id,
        "admission_batch": admission_batch,
        "candidate_count": validation_batch.candidate_count,
        "unique_candidate_count": validation_batch.unique_candidate_count,
        "duplicate_candidate_count": validation_batch.duplicate_candidate_count,
        "admission_count": admission_batch.admission_count,
        "admitted_count": admission_batch.admitted_count,
        "rejected_duplicate_count": admission_batch.rejected_duplicate_count,
        "state": STATE_READ_ONLY,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "observation_candidate_lineage_verified": True,
        "duplicate_policy_verified": admission_batch.duplicate_policy_verified,
        "deterministic_admission_verified": (
            admission_batch.deterministic_admission_verified
        ),
        "candidate_admission_authorized": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "admission_ready": True,
        "downstream_entity_resolution_authorized": (
            admission_batch.downstream_entity_resolution_authorized
        ),
        "read_only": True,
    }
    result = OracleMemoryCertifiedMarketBehaviorCandidateAdmission(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_market_behavior_candidate_admission(result)
    return result


def verify_oracle_memory_certified_market_behavior_candidate_admission(
    result: OracleMemoryCertifiedMarketBehaviorCandidateAdmission,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-055 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-055 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-055 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-055 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-055 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-055 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-055 upstream engine lineage mismatch")
    if result.validation_schema_version != VALIDATION_SCHEMA_VERSION:
        _reject("OML-055 validation schema lineage mismatch")
    if result.validation_engine_id != VALIDATION_ENGINE_ID:
        _reject("OML-055 validation engine lineage mismatch")
    if result.admission_schema_version != ADMISSION_SCHEMA_VERSION:
        _reject("OML-055 admission schema lineage mismatch")
    if result.admission_engine_id != ADMISSION_ENGINE_ID:
        _reject("OML-055 admission engine lineage mismatch")

    for value, label in (
        (result.upstream_certification_hash, "upstream certification hash"),
        (
            result.upstream_materialization_batch_hash,
            "materialization batch hash",
        ),
        (result.validation_batch_hash, "validation batch hash"),
        (result.certification_hash, "certification hash"),
    ):
        _require_hash(value, label)

    verify_oracle_memory_observation_candidate_admission_batch(
        result.admission_batch
    )

    if result.upstream_materialization_batch_hash != (
        result.admission_batch.upstream_batch_hash
    ):
        _reject("OML-055 materialization lineage mismatch")
    if result.validation_batch_hash != (
        result.admission_batch.validation_batch_hash
    ):
        _reject("OML-055 validation lineage mismatch")
    if result.admission_count != result.admission_batch.admission_count:
        _reject("OML-055 admission count mismatch")
    if result.admitted_count != result.admission_batch.admitted_count:
        _reject("OML-055 admitted count mismatch")
    if result.rejected_duplicate_count != (
        result.admission_batch.rejected_duplicate_count
    ):
        _reject("OML-055 duplicate rejection count mismatch")
    if result.candidate_count != (
        result.unique_candidate_count + result.duplicate_candidate_count
    ):
        _reject("OML-055 candidate count reconciliation mismatch")
    if result.admission_count != result.candidate_count:
        _reject("OML-055 candidate/admission count mismatch")

    required = (
        result.materialization_lineage_verified,
        result.validation_lineage_verified,
        result.observation_candidate_lineage_verified,
        result.duplicate_policy_verified,
        result.deterministic_admission_verified,
        result.candidate_admission_authorized,
        result.admission_ready,
        result.downstream_entity_resolution_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-055 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-055 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-055 forbidden capability enabled")

    return True
