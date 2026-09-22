from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_materialization_contract import (
    MATERIALIZATION_STATUS as ORR_006_MATERIALIZATION_STATUS,
    MATERIALIZATION_TYPE as ORR_006_MATERIALIZATION_TYPE,
    OracleResearchResponseEvidenceRequirementMaterialization,
)

SCHEMA_VERSION = "ORR-007"
ENGINE_ID = "ORR-007"
POLICY_ID = "oracle.research-response.evidence-requirement-admission-gate.v1"
EVIDENCE_ADMISSION_TYPE = "oracle_research_response_evidence_requirement_admission"
EVIDENCE_ADMISSION_STATUS = "oracle_research_response_evidence_requirements_admitted"


class OracleResearchResponseEvidenceRequirementAdmissionInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleResearchResponseEvidenceRequirementAdmission:
    evidence_admission_id: str
    materialization_id: str
    materialization_hash: str
    plan_admission_id: str
    plan_admission_hash: str
    plan_id: str
    plan_hash: str
    admission_id: str
    admission_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_runtime_completion_id: str
    source_runtime_completion_hash: str
    subsystem_namespace: str
    requester_id: str
    correlation_id: str
    question_text: str
    response_mode: str
    filters: tuple[tuple[str, str], ...]
    requested_at: datetime
    admitted_at: datetime
    planned_at: datetime
    plan_admitted_at: datetime
    materialized_at: datetime
    evidence_admitted_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    admitted_requirement_ids: tuple[str, ...]
    admitted_requirement_hashes: tuple[str, ...]
    materialization_identity_verified: bool
    materialization_hash_verified: bool
    materialization_contract_verified: bool
    requirement_identity_verified: bool
    requirement_hashes_verified: bool
    requirement_order_verified: bool
    requirement_count_verified: bool
    mandatory_read_only_requirements_verified: bool
    deterministic_boundary_verified: bool
    immutable_evidence_admission_boundary_verified: bool
    read_only_boundary_verified: bool
    single_materialization_scope_verified: bool
    evidence_admission_single_use_verified: bool
    duplicate_evidence_admission_allowed: bool
    evidence_admission_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    evidence_admission_type: str
    evidence_admission_status: str
    evidence_admission_hash: str


class OracleResearchResponseEvidenceRequirementAdmissionGate:
    def admit(
        self,
        *,
        materialization: OracleResearchResponseEvidenceRequirementMaterialization,
        evidence_admitted_at: datetime,
    ) -> OracleResearchResponseEvidenceRequirementAdmission:
        if not isinstance(
            materialization,
            OracleResearchResponseEvidenceRequirementMaterialization,
        ):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "materialization must be canonical ORR-006 materialization"
            )

        materialization_body = asdict(materialization)
        supplied_hash = materialization_body.pop("materialization_hash", None)
        if (
            not _valid_sha256(supplied_hash)
            or stable_hash(materialization_body) != supplied_hash
        ):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "ORR-006 materialization hash mismatch"
            )

        required = (
            _valid_sha256(materialization.materialization_id),
            _valid_sha256(materialization.plan_admission_id),
            _valid_sha256(materialization.plan_admission_hash),
            _valid_sha256(materialization.plan_id),
            _valid_sha256(materialization.plan_hash),
            _valid_sha256(materialization.admission_id),
            _valid_sha256(materialization.admission_hash),
            _valid_sha256(materialization.request_id),
            _valid_sha256(materialization.request_hash),
            _valid_sha256(materialization.dependency_receipt_id),
            _valid_sha256(materialization.dependency_receipt_hash),
            _valid_sha256(materialization.source_runtime_completion_id),
            _valid_sha256(materialization.source_runtime_completion_hash),
            materialization.materialization_type == ORR_006_MATERIALIZATION_TYPE,
            materialization.materialization_status == ORR_006_MATERIALIZATION_STATUS,
            bool(materialization.materialized_requirements),
            len(materialization.materialized_requirements)
            == len(materialization.evidence_requirements),
            materialization.plan_admission_identity_verified,
            materialization.plan_admission_hash_verified,
            materialization.plan_admission_contract_verified,
            materialization.evidence_requirement_set_verified,
            materialization.evidence_requirement_order_verified,
            materialization.deterministic_boundary_verified,
            materialization.immutable_materialization_boundary_verified,
            materialization.read_only_boundary_verified,
            materialization.single_plan_materialization_verified,
            materialization.materialization_single_use_verified,
            not materialization.duplicate_materialization_allowed,
            not materialization.materialization_reversible,
        )
        forbidden = (
            materialization.runtime_serving_allowed,
            materialization.network_listener_allowed,
            materialization.database_connection_allowed,
            materialization.publication_allowed,
            materialization.qseries_handoff_allowed,
            materialization.qseries_execution_allowed,
            materialization.order_creation_allowed,
            materialization.funds_movement_allowed,
            materialization.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "ORR-006 materialization contract incomplete or unsafe"
            )

        requirement_ids: list[str] = []
        requirement_hashes: list[str] = []
        requirement_names: list[str] = []
        expected_ordinals = tuple(range(1, len(materialization.materialized_requirements) + 1))

        for requirement in materialization.materialized_requirements:
            body = asdict(requirement)
            supplied_requirement_hash = body.pop("requirement_hash", None)
            if (
                not _valid_sha256(requirement.requirement_id)
                or not _valid_sha256(supplied_requirement_hash)
                or stable_hash(body) != supplied_requirement_hash
                or not requirement.required
                or not requirement.read_only
                or requirement.external_side_effects_allowed
            ):
                raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                    "materialized requirement invalid or unsafe"
                )
            requirement_ids.append(requirement.requirement_id)
            requirement_hashes.append(requirement.requirement_hash)
            requirement_names.append(requirement.requirement_name)

        ordinals = tuple(
            requirement.ordinal
            for requirement in materialization.materialized_requirements
        )
        if (
            ordinals != expected_ordinals
            or tuple(requirement_names) != materialization.evidence_requirements
            or len(set(requirement_ids)) != len(requirement_ids)
        ):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "materialized requirement identity, order, or uniqueness mismatch"
            )

        if (
            not isinstance(evidence_admitted_at, datetime)
            or evidence_admitted_at.tzinfo is None
            or evidence_admitted_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "evidence_admitted_at must be timezone-aware"
            )
        at = evidence_admitted_at.astimezone(timezone.utc)
        if at < materialization.materialized_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceRequirementAdmissionInvariantError(
                "evidence admission cannot precede materialization"
            )

        body = {
            "materialization_id": materialization.materialization_id,
            "materialization_hash": materialization.materialization_hash,
            "plan_admission_id": materialization.plan_admission_id,
            "plan_admission_hash": materialization.plan_admission_hash,
            "plan_id": materialization.plan_id,
            "plan_hash": materialization.plan_hash,
            "admission_id": materialization.admission_id,
            "admission_hash": materialization.admission_hash,
            "request_id": materialization.request_id,
            "request_hash": materialization.request_hash,
            "dependency_receipt_id": materialization.dependency_receipt_id,
            "dependency_receipt_hash": materialization.dependency_receipt_hash,
            "source_runtime_completion_id": materialization.source_runtime_completion_id,
            "source_runtime_completion_hash": materialization.source_runtime_completion_hash,
            "subsystem_namespace": materialization.subsystem_namespace,
            "requester_id": materialization.requester_id,
            "correlation_id": materialization.correlation_id,
            "question_text": materialization.question_text,
            "response_mode": materialization.response_mode,
            "filters": materialization.filters,
            "requested_at": materialization.requested_at.astimezone(timezone.utc),
            "admitted_at": materialization.admitted_at.astimezone(timezone.utc),
            "planned_at": materialization.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": materialization.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": materialization.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": at,
            "plan_steps": materialization.plan_steps,
            "evidence_requirements": materialization.evidence_requirements,
            "admitted_requirement_ids": tuple(requirement_ids),
            "admitted_requirement_hashes": tuple(requirement_hashes),
            "materialization_identity_verified": True,
            "materialization_hash_verified": True,
            "materialization_contract_verified": True,
            "requirement_identity_verified": True,
            "requirement_hashes_verified": True,
            "requirement_order_verified": True,
            "requirement_count_verified": True,
            "mandatory_read_only_requirements_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_evidence_admission_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_materialization_scope_verified": True,
            "evidence_admission_single_use_verified": True,
            "duplicate_evidence_admission_allowed": False,
            "evidence_admission_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "evidence_admission_type": EVIDENCE_ADMISSION_TYPE,
            "evidence_admission_status": EVIDENCE_ADMISSION_STATUS,
        }
        body["evidence_admission_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "materialization_id": materialization.materialization_id,
                "materialization_hash": materialization.materialization_hash,
                "admitted_requirement_ids": tuple(requirement_ids),
                "evidence_admitted_at": at,
                "evidence_admission_type": EVIDENCE_ADMISSION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceRequirementAdmission(
            **body,
            evidence_admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EVIDENCE_ADMISSION_TYPE",
    "EVIDENCE_ADMISSION_STATUS",
    "OracleResearchResponseEvidenceRequirementAdmissionInvariantError",
    "OracleResearchResponseEvidenceRequirementAdmission",
    "OracleResearchResponseEvidenceRequirementAdmissionGate",
    "stable_hash",
]
