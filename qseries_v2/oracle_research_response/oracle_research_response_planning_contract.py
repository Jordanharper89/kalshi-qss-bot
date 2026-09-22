from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import (
    ADMISSION_STATUS as ORR_003_ADMISSION_STATUS,
    ADMISSION_TYPE as ORR_003_ADMISSION_TYPE,
    OracleResearchResponseRequestAdmission,
)

SCHEMA_VERSION = "ORR-004"
ENGINE_ID = "ORR-004"
POLICY_ID = "oracle.research-response.planning-contract.v1"
PLAN_TYPE = "oracle_research_response_plan"
PLAN_STATUS = "oracle_research_response_plan_materialized"

STEP_VALIDATE_SCOPE = "validate_scope"
STEP_IDENTIFY_REQUIRED_EVIDENCE = "identify_required_evidence"
STEP_SELECT_ANALYTIC_PATH = "select_analytic_path"
STEP_ASSEMBLE_RESPONSE = "assemble_response"
STEP_CERTIFY_RESPONSE_BOUNDARY = "certify_response_boundary"

ALLOWED_PLAN_STEPS = (
    STEP_VALIDATE_SCOPE,
    STEP_IDENTIFY_REQUIRED_EVIDENCE,
    STEP_SELECT_ANALYTIC_PATH,
    STEP_ASSEMBLE_RESPONSE,
    STEP_CERTIFY_RESPONSE_BOUNDARY,
)


class OracleResearchResponsePlanningInvariantError(ValueError):
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
            raise OracleResearchResponsePlanningInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponsePlanningInvariantError(
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


def _derive_evidence_requirements(
    response_mode: str,
    filters: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    base = (
        "source_provenance",
        "freshness",
        "lineage",
        "read_only_certification",
    )
    mode_specific = {
        "research_answer": ("relevant_observations", "analytic_summary"),
        "prediction_card": (
            "venue_identity",
            "market_price",
            "oracle_probability",
            "estimated_edge",
            "confidence",
            "validity_window",
        ),
        "market_deep_dive": (
            "market_definition",
            "resolution_criteria",
            "supporting_evidence",
            "counter_evidence",
            "risk_factors",
        ),
        "comparison": (
            "comparison_subjects",
            "normalized_metrics",
            "relative_ranking",
        ),
        "evidence_summary": (
            "supporting_evidence",
            "counter_evidence",
            "source_conflicts",
        ),
    }
    requirements = list(base + mode_specific.get(response_mode, ()))
    if filters:
        requirements.append("filter_compliance")
    return tuple(requirements)


@dataclass(frozen=True)
class OracleResearchResponsePlan:
    plan_id: str
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
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    admission_identity_verified: bool
    admission_hash_verified: bool
    admission_contract_verified: bool
    planning_scope_verified: bool
    evidence_requirements_verified: bool
    deterministic_boundary_verified: bool
    immutable_plan_boundary_verified: bool
    read_only_boundary_verified: bool
    plan_single_use_verified: bool
    duplicate_plan_allowed: bool
    plan_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    plan_type: str
    plan_status: str
    plan_hash: str


class OracleResearchResponsePlanningContract:
    def materialize(
        self,
        *,
        admission: OracleResearchResponseRequestAdmission,
        planned_at: datetime,
    ) -> OracleResearchResponsePlan:
        if not isinstance(admission, OracleResearchResponseRequestAdmission):
            raise OracleResearchResponsePlanningInvariantError(
                "admission must be canonical ORR-003 admission"
            )

        admission_body = asdict(admission)
        supplied_hash = admission_body.pop("admission_hash", None)
        if (
            not _valid_sha256(supplied_hash)
            or stable_hash(admission_body) != supplied_hash
        ):
            raise OracleResearchResponsePlanningInvariantError(
                "ORR-003 admission hash mismatch"
            )

        required = (
            _valid_sha256(admission.admission_id),
            _valid_sha256(admission.request_id),
            _valid_sha256(admission.request_hash),
            _valid_sha256(admission.dependency_receipt_id),
            _valid_sha256(admission.dependency_receipt_hash),
            _valid_sha256(admission.source_runtime_completion_id),
            _valid_sha256(admission.source_runtime_completion_hash),
            admission.admission_type == ORR_003_ADMISSION_TYPE,
            admission.admission_status == ORR_003_ADMISSION_STATUS,
            admission.request_identity_verified,
            admission.request_hash_verified,
            admission.request_contract_verified,
            admission.typed_question_verified,
            admission.response_mode_verified,
            admission.filter_boundary_verified,
            admission.deterministic_boundary_verified,
            admission.immutable_admission_boundary_verified,
            admission.read_only_boundary_verified,
            admission.single_request_scope_verified,
            admission.admission_single_use_verified,
            not admission.duplicate_admission_allowed,
            not admission.admission_reversible,
        )
        forbidden = (
            admission.runtime_serving_allowed,
            admission.network_listener_allowed,
            admission.database_connection_allowed,
            admission.publication_allowed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.order_creation_allowed,
            admission.funds_movement_allowed,
            admission.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponsePlanningInvariantError(
                "ORR-003 admission contract incomplete or unsafe"
            )

        if (
            not isinstance(planned_at, datetime)
            or planned_at.tzinfo is None
            or planned_at.utcoffset() is None
        ):
            raise OracleResearchResponsePlanningInvariantError(
                "planned_at must be timezone-aware"
            )
        at = planned_at.astimezone(timezone.utc)
        if at < admission.admitted_at.astimezone(timezone.utc):
            raise OracleResearchResponsePlanningInvariantError(
                "planning cannot precede admission"
            )

        plan_steps = ALLOWED_PLAN_STEPS
        evidence_requirements = _derive_evidence_requirements(
            admission.response_mode,
            admission.filters,
        )

        body = {
            "admission_id": admission.admission_id,
            "admission_hash": admission.admission_hash,
            "request_id": admission.request_id,
            "request_hash": admission.request_hash,
            "dependency_receipt_id": admission.dependency_receipt_id,
            "dependency_receipt_hash": admission.dependency_receipt_hash,
            "source_runtime_completion_id": admission.source_runtime_completion_id,
            "source_runtime_completion_hash": admission.source_runtime_completion_hash,
            "subsystem_namespace": admission.subsystem_namespace,
            "requester_id": admission.requester_id,
            "correlation_id": admission.correlation_id,
            "question_text": admission.question_text,
            "response_mode": admission.response_mode,
            "filters": admission.filters,
            "requested_at": admission.requested_at.astimezone(timezone.utc),
            "admitted_at": admission.admitted_at.astimezone(timezone.utc),
            "planned_at": at,
            "plan_steps": plan_steps,
            "evidence_requirements": evidence_requirements,
            "admission_identity_verified": True,
            "admission_hash_verified": True,
            "admission_contract_verified": True,
            "planning_scope_verified": True,
            "evidence_requirements_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_plan_boundary_verified": True,
            "read_only_boundary_verified": True,
            "plan_single_use_verified": True,
            "duplicate_plan_allowed": False,
            "plan_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "plan_type": PLAN_TYPE,
            "plan_status": PLAN_STATUS,
        }
        body["plan_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "admission_id": admission.admission_id,
                "admission_hash": admission.admission_hash,
                "planned_at": at,
                "plan_steps": plan_steps,
                "evidence_requirements": evidence_requirements,
                "plan_type": PLAN_TYPE,
            }
        )
        return OracleResearchResponsePlan(
            **body,
            plan_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "PLAN_TYPE",
    "PLAN_STATUS",
    "ALLOWED_PLAN_STEPS",
    "OracleResearchResponsePlanningInvariantError",
    "OracleResearchResponsePlan",
    "OracleResearchResponsePlanningContract",
    "stable_hash",
]
