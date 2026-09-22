from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_plan_admission_gate import (
    PLAN_ADMISSION_STATUS as ORR_005_PLAN_ADMISSION_STATUS,
    PLAN_ADMISSION_TYPE as ORR_005_PLAN_ADMISSION_TYPE,
    OracleResearchResponsePlanAdmission,
)

SCHEMA_VERSION = "ORR-006"
ENGINE_ID = "ORR-006"
POLICY_ID = "oracle.research-response.evidence-requirement-materialization.v1"
MATERIALIZATION_TYPE = "oracle_research_response_evidence_requirement_materialization"
MATERIALIZATION_STATUS = "oracle_research_response_evidence_requirements_materialized"

SUPPORTED_EVIDENCE_REQUIREMENTS = (
    "source_provenance", "freshness", "lineage", "read_only_certification",
    "relevant_observations", "analytic_summary", "venue_identity", "market_price",
    "oracle_probability", "estimated_edge", "confidence", "validity_window",
    "market_definition", "resolution_criteria", "supporting_evidence",
    "counter_evidence", "risk_factors", "comparison_subjects",
    "normalized_metrics", "relative_ranking", "source_conflicts", "filter_compliance",
)


class OracleResearchResponseEvidenceRequirementMaterializationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda i: str(i[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class OracleResearchResponseEvidenceRequirement:
    requirement_id: str
    ordinal: int
    requirement_name: str
    required: bool
    read_only: bool
    external_side_effects_allowed: bool
    requirement_hash: str


@dataclass(frozen=True)
class OracleResearchResponseEvidenceRequirementMaterialization:
    materialization_id: str
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
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    materialized_requirements: tuple[OracleResearchResponseEvidenceRequirement, ...]
    plan_admission_identity_verified: bool
    plan_admission_hash_verified: bool
    plan_admission_contract_verified: bool
    evidence_requirement_set_verified: bool
    evidence_requirement_order_verified: bool
    deterministic_boundary_verified: bool
    immutable_materialization_boundary_verified: bool
    read_only_boundary_verified: bool
    single_plan_materialization_verified: bool
    materialization_single_use_verified: bool
    duplicate_materialization_allowed: bool
    materialization_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    materialization_type: str
    materialization_status: str
    materialization_hash: str


class OracleResearchResponseEvidenceRequirementMaterializationContract:
    def materialize(self, *, plan_admission: OracleResearchResponsePlanAdmission,
                    materialized_at: datetime) -> OracleResearchResponseEvidenceRequirementMaterialization:
        if not isinstance(plan_admission, OracleResearchResponsePlanAdmission):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "plan_admission must be canonical ORR-005 plan admission"
            )

        admission_body = asdict(plan_admission)
        supplied_hash = admission_body.pop("plan_admission_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(admission_body) != supplied_hash:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "ORR-005 plan admission hash mismatch"
            )

        required = (
            _valid_sha256(plan_admission.plan_admission_id),
            _valid_sha256(plan_admission.plan_id),
            _valid_sha256(plan_admission.plan_hash),
            _valid_sha256(plan_admission.admission_id),
            _valid_sha256(plan_admission.admission_hash),
            _valid_sha256(plan_admission.request_id),
            _valid_sha256(plan_admission.request_hash),
            _valid_sha256(plan_admission.dependency_receipt_id),
            _valid_sha256(plan_admission.dependency_receipt_hash),
            _valid_sha256(plan_admission.source_runtime_completion_id),
            _valid_sha256(plan_admission.source_runtime_completion_hash),
            plan_admission.plan_admission_type == ORR_005_PLAN_ADMISSION_TYPE,
            plan_admission.plan_admission_status == ORR_005_PLAN_ADMISSION_STATUS,
            plan_admission.plan_identity_verified,
            plan_admission.plan_hash_verified,
            plan_admission.plan_contract_verified,
            plan_admission.plan_steps_verified,
            plan_admission.evidence_requirements_verified,
            plan_admission.deterministic_boundary_verified,
            plan_admission.immutable_plan_admission_boundary_verified,
            plan_admission.read_only_boundary_verified,
            plan_admission.single_plan_scope_verified,
            plan_admission.plan_admission_single_use_verified,
            not plan_admission.duplicate_plan_admission_allowed,
            not plan_admission.plan_admission_reversible,
        )
        forbidden = (
            plan_admission.runtime_serving_allowed,
            plan_admission.network_listener_allowed,
            plan_admission.database_connection_allowed,
            plan_admission.publication_allowed,
            plan_admission.qseries_handoff_allowed,
            plan_admission.qseries_execution_allowed,
            plan_admission.order_creation_allowed,
            plan_admission.funds_movement_allowed,
            plan_admission.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "ORR-005 plan admission contract incomplete or unsafe"
            )

        if materialized_at.tzinfo is None or materialized_at.utcoffset() is None:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "materialized_at must be timezone-aware"
            )
        at = materialized_at.astimezone(timezone.utc)
        if at < plan_admission.plan_admitted_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "materialization cannot precede plan admission"
            )

        requirements = tuple(dict.fromkeys(v.strip() for v in plan_admission.evidence_requirements if v.strip()))
        if not requirements:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "evidence requirements cannot be empty"
            )
        unsupported = tuple(v for v in requirements if v not in SUPPORTED_EVIDENCE_REQUIREMENTS)
        if unsupported:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                f"unsupported evidence requirements: {unsupported}"
            )

        records = []
        for ordinal, name in enumerate(requirements, start=1):
            item_body = {
                "ordinal": ordinal,
                "requirement_name": name,
                "required": True,
                "read_only": True,
                "external_side_effects_allowed": False,
            }
            requirement_id = stable_hash({
                "engine_id": ENGINE_ID,
                "plan_admission_id": plan_admission.plan_admission_id,
                **item_body,
            })
            records.append(OracleResearchResponseEvidenceRequirement(
                requirement_id=requirement_id,
                **item_body,
                requirement_hash=stable_hash({"requirement_id": requirement_id, **item_body}),
            ))

        body = {
            "plan_admission_id": plan_admission.plan_admission_id,
            "plan_admission_hash": plan_admission.plan_admission_hash,
            "plan_id": plan_admission.plan_id,
            "plan_hash": plan_admission.plan_hash,
            "admission_id": plan_admission.admission_id,
            "admission_hash": plan_admission.admission_hash,
            "request_id": plan_admission.request_id,
            "request_hash": plan_admission.request_hash,
            "dependency_receipt_id": plan_admission.dependency_receipt_id,
            "dependency_receipt_hash": plan_admission.dependency_receipt_hash,
            "source_runtime_completion_id": plan_admission.source_runtime_completion_id,
            "source_runtime_completion_hash": plan_admission.source_runtime_completion_hash,
            "subsystem_namespace": plan_admission.subsystem_namespace,
            "requester_id": plan_admission.requester_id,
            "correlation_id": plan_admission.correlation_id,
            "question_text": plan_admission.question_text,
            "response_mode": plan_admission.response_mode,
            "filters": plan_admission.filters,
            "requested_at": plan_admission.requested_at.astimezone(timezone.utc),
            "admitted_at": plan_admission.admitted_at.astimezone(timezone.utc),
            "planned_at": plan_admission.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": plan_admission.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": at,
            "plan_steps": plan_admission.plan_steps,
            "evidence_requirements": requirements,
            "materialized_requirements": tuple(records),
            "plan_admission_identity_verified": True,
            "plan_admission_hash_verified": True,
            "plan_admission_contract_verified": True,
            "evidence_requirement_set_verified": True,
            "evidence_requirement_order_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_materialization_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_plan_materialization_verified": True,
            "materialization_single_use_verified": True,
            "duplicate_materialization_allowed": False,
            "materialization_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "materialization_type": MATERIALIZATION_TYPE,
            "materialization_status": MATERIALIZATION_STATUS,
        }
        body["materialization_id"] = stable_hash({
            "engine_id": ENGINE_ID,
            "plan_admission_id": plan_admission.plan_admission_id,
            "plan_admission_hash": plan_admission.plan_admission_hash,
            "materialized_at": at,
            "evidence_requirements": requirements,
            "materialization_type": MATERIALIZATION_TYPE,
        })
        return OracleResearchResponseEvidenceRequirementMaterialization(
            **body,
            materialization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION", "ENGINE_ID", "POLICY_ID", "MATERIALIZATION_TYPE",
    "MATERIALIZATION_STATUS", "SUPPORTED_EVIDENCE_REQUIREMENTS",
    "OracleResearchResponseEvidenceRequirementMaterializationInvariantError",
    "OracleResearchResponseEvidenceRequirement",
    "OracleResearchResponseEvidenceRequirementMaterialization",
    "OracleResearchResponseEvidenceRequirementMaterializationContract", "stable_hash",
]
