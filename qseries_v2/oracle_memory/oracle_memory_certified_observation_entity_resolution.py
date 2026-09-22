from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    OracleMemoryCandidateValidationBatch,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
    OracleMemoryObservationCandidateAdmissionBatch,
    verify_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    OracleMemoryEntityResolutionBatch,
    OracleMemoryResolvedEntity,
    build_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_entity_resolution_batch,
    verify_oracle_memory_resolved_entity,
)

SCHEMA_VERSION = "OML-030"
ENGINE_ID = "OML-030"
POLICY_ID = (
    "oracle-memory.certified-observation-entity-resolution.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-029"
UPSTREAM_ENGINE_ID = "OML-029"

RESOLUTION_STATE_READ_ONLY = "read_only_resolution"


class OracleMemoryObservationEntityResolutionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationEntityBinding:
    observation_hash: str
    candidate_hash: str
    admission_hash: str
    canonical_entity_id: str
    entity_hash: str
    domain_id: str
    canonical_name: str
    normalized_name: str
    observation_lineage_verified: bool
    candidate_lineage_verified: bool
    admission_lineage_verified: bool
    entity_lineage_verified: bool
    duplicate_rejection_verified: bool
    deterministic_binding_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationEntityResolution:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_admission_batch_hash: str
    upstream_materialization_batch_hash: str
    upstream_validation_batch_hash: str
    entity_resolution_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    bindings: tuple[OracleMemoryObservationEntityBinding, ...]
    admitted_candidate_count: int
    rejected_duplicate_count: int
    resolved_entity_count: int
    resolution_state: str
    canonical_order_verified: bool
    deterministic_resolution_verified: bool
    observation_entity_lineage_verified: bool
    duplicate_candidates_excluded: bool
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
    resolution_hash: str


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

    raise OracleMemoryObservationEntityResolutionInvariantError(
        "unsupported OML-030 value type: "
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
    raise OracleMemoryObservationEntityResolutionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-030 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationEntityResolutionInvariantError(
            f"OML-030 invalid {label} hexadecimal value"
        ) from exc


def _build_binding(
    *,
    observation_hash: str,
    candidate_hash: str,
    admission_hash: str,
    entity: OracleMemoryResolvedEntity,
) -> OracleMemoryObservationEntityBinding:
    verify_oracle_memory_resolved_entity(entity)

    body = {
        "observation_hash": observation_hash,
        "candidate_hash": candidate_hash,
        "admission_hash": admission_hash,
        "canonical_entity_id": entity.canonical_entity_id,
        "entity_hash": entity.entity_hash,
        "domain_id": entity.domain_id,
        "canonical_name": entity.canonical_name,
        "normalized_name": entity.normalized_name,
        "observation_lineage_verified": True,
        "candidate_lineage_verified": True,
        "admission_lineage_verified": True,
        "entity_lineage_verified": True,
        "duplicate_rejection_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryObservationEntityBinding(
        **body,
        binding_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_entity_binding(binding)
    return binding


def verify_oracle_memory_observation_entity_binding(
    binding: OracleMemoryObservationEntityBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-030 binding hash mismatch")

    for value, label in (
        (binding.observation_hash, "observation hash"),
        (binding.candidate_hash, "candidate hash"),
        (binding.admission_hash, "admission hash"),
        (binding.canonical_entity_id, "canonical entity id"),
        (binding.entity_hash, "entity hash"),
        (binding.binding_hash, "binding hash"),
    ):
        _require_hash(value, label)

    required_true = (
        binding.observation_lineage_verified,
        binding.candidate_lineage_verified,
        binding.admission_lineage_verified,
        binding.entity_lineage_verified,
        binding.duplicate_rejection_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )

    if not all(required_true):
        _reject("OML-030 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-030 forbidden binding capability enabled")

    return True


def build_oracle_memory_observation_entity_resolution(
    *,
    admission_batch: OracleMemoryObservationCandidateAdmissionBatch,
    materialization_batch: (
        OracleMemoryObservationCandidateMaterializationBatch
    ),
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryObservationEntityResolution:
    verify_oracle_memory_observation_candidate_admission_batch(
        admission_batch
    )
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if admission_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-030 upstream schema mismatch")

    if admission_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-030 upstream engine mismatch")

    if not admission_batch.admission_ready:
        _reject("OML-030 admission batch not ready")

    if not admission_batch.downstream_entity_resolution_authorized:
        _reject("OML-030 entity resolution not authorized")

    if not admission_batch.read_only:
        _reject("OML-030 upstream admission not read-only")

    admitted_admissions = tuple(
        item
        for item in admission_batch.admissions
        if item.admission_status == ADMISSION_STATUS_ADMITTED
    )

    rejected_admissions = tuple(
        item
        for item in admission_batch.admissions
        if item.admission_status
        == ADMISSION_STATUS_REJECTED_DUPLICATE
    )

    candidates_by_hash = {
        candidate.candidate_hash: candidate
        for candidate in materialization_batch.candidates
    }

    validation_results_by_hash = {
        result.result_hash: result
        for result in validation_batch.results
    }

    admitted_candidates = []
    admitted_results = []

    for admission in admitted_admissions:
        candidate = candidates_by_hash.get(admission.candidate_hash)
        validation_result = validation_results_by_hash.get(
            admission.validation_result_hash
        )

        if candidate is None:
            _reject("OML-030 admitted candidate missing")

        if validation_result is None:
            _reject("OML-030 admitted validation result missing")

        if validation_result.candidate_hash != admission.candidate_hash:
            _reject("OML-030 admission validation lineage mismatch")

        if validation_result.status != "valid":
            _reject("OML-030 admitted validation result not valid")

        admitted_candidates.append(candidate)
        admitted_results.append(validation_result)

    admitted_candidates = tuple(admitted_candidates)
    admitted_results = tuple(admitted_results)

    if len(admitted_candidates) != admission_batch.admitted_count:
        _reject("OML-030 admitted candidate reconciliation mismatch")

    if len(admitted_results) != admission_batch.admitted_count:
        _reject("OML-030 admitted validation reconciliation mismatch")

    filtered_body = {
        "schema_version": validation_batch.schema_version,
        "engine_id": validation_batch.engine_id,
        "policy_id": validation_batch.policy_id,
        "subsystem_id": validation_batch.subsystem_id,
        "upstream_schema_version": (
            validation_batch.upstream_schema_version
        ),
        "upstream_engine_id": validation_batch.upstream_engine_id,
        "upstream_certification_hash": (
            validation_batch.upstream_certification_hash
        ),
        "results": admitted_results,
        "candidate_count": len(admitted_results),
        "unique_candidate_count": len(admitted_results),
        "duplicate_candidate_count": 0,
        "canonical_ordering_verified": True,
        "deterministic_validation_verified": True,
        "duplicate_detection_verified": True,
        "duplicate_persistence_forbidden": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "batch_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    filtered_validation = OracleMemoryCandidateValidationBatch(
        **filtered_body,
        batch_hash=_stable_hash(filtered_body),
    )

    if any(
        not hasattr(result, "__dataclass_fields__")
        for result in filtered_validation.results
    ):
        _reject(
            "OML-030 filtered validation results lost dataclass identity"
        )

    verify_oracle_memory_candidate_validation_batch(filtered_validation)

    entity_batch = build_oracle_memory_entity_resolution_batch(
        validation_batch=filtered_validation,
        aliases_by_candidate_hash=aliases_by_candidate_hash or {},
    )

    candidate_by_hash = {
        item.candidate_hash: item
        for item in admitted_candidates
    }

    entities_by_candidate = {
        entity.source_candidate_hash: entity
        for entity in entity_batch.entities
    }

    bindings = []

    for admission in sorted(
        admitted_admissions,
        key=lambda item: (
            item.candidate_hash,
            item.validation_result_hash,
            item.admission_hash,
        ),
    ):
        candidate = candidate_by_hash.get(admission.candidate_hash)
        entity = entities_by_candidate.get(admission.candidate_hash)

        if candidate is None or entity is None:
            _reject("OML-030 entity binding lineage incomplete")

        observation_hash = candidate.payload.get("observation_hash")

        if not isinstance(observation_hash, str):
            _reject("OML-030 observation hash missing from candidate")

        bindings.append(
            _build_binding(
                observation_hash=observation_hash,
                candidate_hash=admission.candidate_hash,
                admission_hash=admission.admission_hash,
                entity=entity,
            )
        )

    ordered_bindings = tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.domain_id,
                item.normalized_name,
                item.canonical_entity_id,
                item.binding_hash,
            ),
        )
    )

    entity_ids = tuple(
        item.canonical_entity_id for item in entity_batch.entities
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_batch.schema_version,
        "upstream_engine_id": admission_batch.engine_id,
        "upstream_admission_batch_hash": admission_batch.batch_hash,
        "upstream_materialization_batch_hash": (
            materialization_batch.batch_hash
        ),
        "upstream_validation_batch_hash": validation_batch.batch_hash,
        "entity_resolution_batch_hash": entity_batch.batch_hash,
        "entities": entity_batch.entities,
        "bindings": ordered_bindings,
        "admitted_candidate_count": admission_batch.admitted_count,
        "rejected_duplicate_count": (
            admission_batch.rejected_duplicate_count
        ),
        "resolved_entity_count": len(entity_batch.entities),
        "resolution_state": RESOLUTION_STATE_READ_ONLY,
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "observation_entity_lineage_verified": True,
        "duplicate_candidates_excluded": (
            len(rejected_admissions)
            == admission_batch.rejected_duplicate_count
            and all(
                item.admission_status
                == ADMISSION_STATUS_REJECTED_DUPLICATE
                for item in rejected_admissions
            )
        ),
        "entity_identity_uniqueness_verified": (
            len(set(entity_ids)) == len(entity_ids)
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "resolution_ready": True,
        "downstream_relationship_graph_authorized": True,
        "read_only": True,
    }

    resolution = OracleMemoryObservationEntityResolution(
        **body,
        resolution_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_entity_resolution(resolution)
    return resolution


def verify_oracle_memory_observation_entity_resolution(
    resolution: OracleMemoryObservationEntityResolution,
) -> bool:
    body = asdict(resolution)
    supplied = body.pop("resolution_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-030 resolution hash mismatch")

    if resolution.schema_version != SCHEMA_VERSION:
        _reject("OML-030 schema mismatch")

    if resolution.engine_id != ENGINE_ID:
        _reject("OML-030 engine mismatch")

    if resolution.policy_id != POLICY_ID:
        _reject("OML-030 policy mismatch")

    if resolution.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-030 subsystem mismatch")

    if resolution.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-030 upstream schema lineage mismatch")

    if resolution.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-030 upstream engine lineage mismatch")

    if resolution.resolved_entity_count != len(resolution.entities):
        _reject("OML-030 entity count mismatch")

    if resolution.resolved_entity_count != len(resolution.bindings):
        _reject("OML-030 binding count mismatch")

    if resolution.resolution_state != RESOLUTION_STATE_READ_ONLY:
        _reject("OML-030 resolution state invalid")

    entity_ids = []

    for entity in resolution.entities:
        verify_oracle_memory_resolved_entity(entity)
        entity_ids.append(entity.canonical_entity_id)

    for binding in resolution.bindings:
        verify_oracle_memory_observation_entity_binding(binding)

    if len(set(entity_ids)) != len(entity_ids):
        _reject("OML-030 duplicate entity identities")

    required_true = (
        resolution.canonical_order_verified,
        resolution.deterministic_resolution_verified,
        resolution.observation_entity_lineage_verified,
        resolution.duplicate_candidates_excluded,
        resolution.entity_identity_uniqueness_verified,
        resolution.resolution_ready,
        resolution.downstream_relationship_graph_authorized,
        resolution.read_only,
    )

    if not all(required_true):
        _reject("OML-030 resolution guarantee missing")

    forbidden = (
        resolution.persistence_enabled,
        resolution.learning_updates_enabled,
        resolution.runtime_activation_enabled,
        resolution.publication_enabled,
        resolution.action_authorization_enabled,
        resolution.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-030 forbidden resolution capability enabled")

    return True
