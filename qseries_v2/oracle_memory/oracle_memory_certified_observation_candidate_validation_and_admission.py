from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    STATUS_DUPLICATE,
    STATUS_VALID,
    OracleMemoryCandidateValidationBatch,
    OracleMemoryCandidateValidationResult,
    verify_oracle_memory_candidate_validation_batch,
    verify_oracle_memory_candidate_validation_result,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    MATERIALIZATION_STATUS_DUPLICATE,
    MATERIALIZATION_STATUS_READY,
    OracleMemoryObservationCandidateBinding,
    OracleMemoryObservationCandidateMaterializationBatch,
    verify_oracle_memory_observation_candidate_binding,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-029"
ENGINE_ID = "OML-029"
POLICY_ID = (
    "oracle-memory.certified-observation-candidate-validation-and-admission.v1"
)

UPSTREAM_SCHEMA_VERSION = "OML-028"
UPSTREAM_ENGINE_ID = "OML-028"

ADMISSION_STATUS_ADMITTED = "admitted"
ADMISSION_STATUS_REJECTED_DUPLICATE = "rejected_duplicate"

ALLOWED_ADMISSION_STATUSES = (
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
)


class OracleMemoryObservationCandidateAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryObservationCandidateAdmission:
    observation_hash: str
    candidate_hash: str
    validation_result_hash: str
    materialization_binding_hash: str
    admission_status: str
    duplicate_of_candidate_hash: str | None
    observation_lineage_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    evidence_lineage_verified: bool
    candidate_identity_verified: bool
    duplicate_policy_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    admission_hash: str


@dataclass(frozen=True)
class OracleMemoryObservationCandidateAdmissionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    validation_batch_hash: str
    admissions: tuple[OracleMemoryObservationCandidateAdmission, ...]
    admission_count: int
    admitted_count: int
    rejected_duplicate_count: int
    canonical_order_verified: bool
    deterministic_admission_verified: bool
    materialization_lineage_verified: bool
    validation_lineage_verified: bool
    duplicate_policy_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    admission_ready: bool
    downstream_entity_resolution_authorized: bool
    read_only: bool
    batch_hash: str


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

    raise OracleMemoryObservationCandidateAdmissionInvariantError(
        "unsupported OML-029 value type: "
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
    raise OracleMemoryObservationCandidateAdmissionInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-029 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryObservationCandidateAdmissionInvariantError(
            f"OML-029 invalid {label} hexadecimal value"
        ) from exc


def _build_admission(
    *,
    binding: OracleMemoryObservationCandidateBinding,
    validation_result: OracleMemoryCandidateValidationResult,
) -> OracleMemoryObservationCandidateAdmission:
    verify_oracle_memory_observation_candidate_binding(binding)
    verify_oracle_memory_candidate_validation_result(validation_result)

    if binding.candidate_hash != validation_result.candidate_hash:
        _reject("OML-029 candidate hash lineage mismatch")

    if binding.candidate_id != validation_result.candidate_id:
        _reject("OML-029 candidate id lineage mismatch")

    if binding.domain_id != validation_result.domain_id:
        _reject("OML-029 candidate domain lineage mismatch")

    duplicate = (
        binding.materialization_status == MATERIALIZATION_STATUS_DUPLICATE
        or validation_result.status == STATUS_DUPLICATE
    )

    if duplicate:
        admission_status = ADMISSION_STATUS_REJECTED_DUPLICATE
        duplicate_of = (
            validation_result.duplicate_of_candidate_hash
            or binding.duplicate_of_candidate_hash
        )
    else:
        admission_status = ADMISSION_STATUS_ADMITTED
        duplicate_of = None

    body = {
        "observation_hash": binding.observation_hash,
        "candidate_hash": binding.candidate_hash,
        "validation_result_hash": validation_result.result_hash,
        "materialization_binding_hash": binding.binding_hash,
        "admission_status": admission_status,
        "duplicate_of_candidate_hash": duplicate_of,
        "observation_lineage_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "evidence_lineage_verified": (
            binding.evidence_lineage_verified
        ),
        "candidate_identity_verified": True,
        "duplicate_policy_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    admission = OracleMemoryObservationCandidateAdmission(
        **body,
        admission_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_admission(admission)
    return admission


def verify_oracle_memory_observation_candidate_admission(
    admission: OracleMemoryObservationCandidateAdmission,
) -> bool:
    body = asdict(admission)
    supplied = body.pop("admission_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-029 admission hash mismatch")

    for value, label in (
        (admission.observation_hash, "observation hash"),
        (admission.candidate_hash, "candidate hash"),
        (admission.validation_result_hash, "validation result hash"),
        (
            admission.materialization_binding_hash,
            "materialization binding hash",
        ),
        (admission.admission_hash, "admission hash"),
    ):
        _require_hash(value, label)

    if admission.admission_status not in ALLOWED_ADMISSION_STATUSES:
        _reject("OML-029 admission status invalid")

    if admission.admission_status == (
        ADMISSION_STATUS_REJECTED_DUPLICATE
    ):
        if admission.duplicate_of_candidate_hash is None:
            _reject("OML-029 duplicate admission lineage missing")
        _require_hash(
            admission.duplicate_of_candidate_hash,
            "duplicate candidate hash",
        )
    elif admission.duplicate_of_candidate_hash is not None:
        _reject("OML-029 unexpected duplicate lineage")

    required_true = (
        admission.observation_lineage_verified,
        admission.materialization_lineage_verified,
        admission.validation_lineage_verified,
        admission.evidence_lineage_verified,
        admission.candidate_identity_verified,
        admission.duplicate_policy_verified,
        admission.read_only,
    )

    if not all(required_true):
        _reject("OML-029 admission guarantee missing")

    forbidden = (
        admission.persistence_authorized,
        admission.learning_update_authorized,
        admission.runtime_activation_authorized,
        admission.publication_authorized,
        admission.action_authorization_enabled,
        admission.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-029 forbidden admission capability enabled")

    return True


def build_oracle_memory_observation_candidate_admission_batch(
    *,
    materialization_batch: (
        OracleMemoryObservationCandidateMaterializationBatch
    ),
    validation_batch: OracleMemoryCandidateValidationBatch,
) -> OracleMemoryObservationCandidateAdmissionBatch:
    verify_oracle_memory_observation_candidate_materialization_batch(
        materialization_batch
    )
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if materialization_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-029 upstream schema mismatch")

    if materialization_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-029 upstream engine mismatch")

    if not materialization_batch.materialization_ready:
        _reject("OML-029 materialization batch not ready")

    if not materialization_batch.downstream_validation_authorized:
        _reject("OML-029 downstream validation not authorized")

    if not materialization_batch.read_only:
        _reject("OML-029 materialization batch not read-only")

    if validation_batch.candidate_count != (
        materialization_batch.candidate_count
    ):
        _reject("OML-029 validation/materialization count mismatch")

    bindings_by_candidate_hash = {
        binding.candidate_hash: binding
        for binding in materialization_batch.bindings
    }

    results_by_candidate_hash: dict[
        str,
        list[OracleMemoryCandidateValidationResult],
    ] = {}

    for result in validation_batch.results:
        results_by_candidate_hash.setdefault(
            result.candidate_hash,
            [],
        ).append(result)

    admissions = []

    for binding in materialization_batch.bindings:
        candidates = results_by_candidate_hash.get(
            binding.candidate_hash,
            [],
        )

        if not candidates:
            _reject("OML-029 missing validation result")

        validation_result = candidates.pop(0)

        admissions.append(
            _build_admission(
                binding=binding,
                validation_result=validation_result,
            )
        )

    ordered = tuple(
        sorted(
            admissions,
            key=lambda item: (
                item.admission_status,
                item.observation_hash,
                item.candidate_hash,
                item.admission_hash,
            ),
        )
    )

    admitted_count = sum(
        item.admission_status == ADMISSION_STATUS_ADMITTED
        for item in ordered
    )
    rejected_count = sum(
        item.admission_status
        == ADMISSION_STATUS_REJECTED_DUPLICATE
        for item in ordered
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": materialization_batch.schema_version,
        "upstream_engine_id": materialization_batch.engine_id,
        "upstream_batch_hash": materialization_batch.batch_hash,
        "validation_batch_hash": validation_batch.batch_hash,
        "admissions": ordered,
        "admission_count": len(ordered),
        "admitted_count": admitted_count,
        "rejected_duplicate_count": rejected_count,
        "canonical_order_verified": True,
        "deterministic_admission_verified": True,
        "materialization_lineage_verified": True,
        "validation_lineage_verified": True,
        "duplicate_policy_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "admission_ready": True,
        "downstream_entity_resolution_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryObservationCandidateAdmissionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_observation_candidate_admission_batch(batch)
    return batch


def verify_oracle_memory_observation_candidate_admission_batch(
    batch: OracleMemoryObservationCandidateAdmissionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-029 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-029 schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-029 engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-029 policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-029 subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-029 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-029 upstream engine lineage mismatch")

    if batch.admission_count != len(batch.admissions):
        _reject("OML-029 admission count mismatch")

    if (
        batch.admitted_count
        + batch.rejected_duplicate_count
        != batch.admission_count
    ):
        _reject("OML-029 admission reconciliation mismatch")

    for admission in batch.admissions:
        verify_oracle_memory_observation_candidate_admission(admission)

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_admission_verified,
        batch.materialization_lineage_verified,
        batch.validation_lineage_verified,
        batch.duplicate_policy_verified,
        batch.admission_ready,
        batch.downstream_entity_resolution_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-029 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-029 forbidden batch capability enabled")

    return True
