from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_planning_contract import (
    ALLOWED_PLAN_STEPS,
    PLAN_STATUS as ORR_004_PLAN_STATUS,
    PLAN_TYPE as ORR_004_PLAN_TYPE,
    OracleResearchResponsePlan,
)

SCHEMA_VERSION = "ORR-005"
ENGINE_ID = "ORR-005"
POLICY_ID = "oracle.research-response.plan-admission-gate.v1"
PLAN_ADMISSION_TYPE = "oracle_research_response_plan_admission"
PLAN_ADMISSION_STATUS = "oracle_research_response_plan_admitted"


class OracleResearchResponsePlanAdmissionInvariantError(ValueError):
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
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponsePlanAdmissionInvariantError(
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
class OracleResearchResponsePlanAdmission:
    plan_admission_id: str
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
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    plan_identity_verified: bool
    plan_hash_verified: bool
    plan_contract_verified: bool
    plan_steps_verified: bool
    evidence_requirements_verified: bool
    deterministic_boundary_verified: bool
    immutable_plan_admission_boundary_verified: bool
    read_only_boundary_verified: bool
    single_plan_scope_verified: bool
    plan_admission_single_use_verified: bool
    duplicate_plan_admission_allowed: bool
    plan_admission_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    plan_admission_type: str
    plan_admission_status: str
    plan_admission_hash: str


class OracleResearchResponsePlanAdmissionGate:
    def admit(
        self,
        *,
        plan: OracleResearchResponsePlan,
        plan_admitted_at: datetime,
    ) -> OracleResearchResponsePlanAdmission:
        if not isinstance(plan, OracleResearchResponsePlan):
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "plan must be canonical ORR-004 plan"
            )

        plan_body = asdict(plan)
        supplied_hash = plan_body.pop("plan_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(plan_body) != supplied_hash:
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "ORR-004 plan hash mismatch"
            )

        required = (
            _valid_sha256(plan.plan_id),
            _valid_sha256(plan.admission_id),
            _valid_sha256(plan.admission_hash),
            _valid_sha256(plan.request_id),
            _valid_sha256(plan.request_hash),
            _valid_sha256(plan.dependency_receipt_id),
            _valid_sha256(plan.dependency_receipt_hash),
            _valid_sha256(plan.source_runtime_completion_id),
            _valid_sha256(plan.source_runtime_completion_hash),
            plan.plan_type == ORR_004_PLAN_TYPE,
            plan.plan_status == ORR_004_PLAN_STATUS,
            plan.plan_steps == ALLOWED_PLAN_STEPS,
            bool(plan.evidence_requirements),
            plan.admission_identity_verified,
            plan.admission_hash_verified,
            plan.admission_contract_verified,
            plan.planning_scope_verified,
            plan.evidence_requirements_verified,
            plan.deterministic_boundary_verified,
            plan.immutable_plan_boundary_verified,
            plan.read_only_boundary_verified,
            plan.plan_single_use_verified,
            not plan.duplicate_plan_allowed,
            not plan.plan_reversible,
        )
        forbidden = (
            plan.runtime_serving_allowed,
            plan.network_listener_allowed,
            plan.database_connection_allowed,
            plan.publication_allowed,
            plan.qseries_handoff_allowed,
            plan.qseries_execution_allowed,
            plan.order_creation_allowed,
            plan.funds_movement_allowed,
            plan.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "ORR-004 plan contract incomplete or unsafe"
            )

        if (
            not isinstance(plan_admitted_at, datetime)
            or plan_admitted_at.tzinfo is None
            or plan_admitted_at.utcoffset() is None
        ):
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "plan_admitted_at must be timezone-aware"
            )
        at = plan_admitted_at.astimezone(timezone.utc)
        if at < plan.planned_at.astimezone(timezone.utc):
            raise OracleResearchResponsePlanAdmissionInvariantError(
                "plan admission cannot precede planning"
            )

        body = {
            "plan_id": plan.plan_id,
            "plan_hash": plan.plan_hash,
            "admission_id": plan.admission_id,
            "admission_hash": plan.admission_hash,
            "request_id": plan.request_id,
            "request_hash": plan.request_hash,
            "dependency_receipt_id": plan.dependency_receipt_id,
            "dependency_receipt_hash": plan.dependency_receipt_hash,
            "source_runtime_completion_id": plan.source_runtime_completion_id,
            "source_runtime_completion_hash": plan.source_runtime_completion_hash,
            "subsystem_namespace": plan.subsystem_namespace,
            "requester_id": plan.requester_id,
            "correlation_id": plan.correlation_id,
            "question_text": plan.question_text,
            "response_mode": plan.response_mode,
            "filters": plan.filters,
            "requested_at": plan.requested_at.astimezone(timezone.utc),
            "admitted_at": plan.admitted_at.astimezone(timezone.utc),
            "planned_at": plan.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": at,
            "plan_steps": plan.plan_steps,
            "evidence_requirements": plan.evidence_requirements,
            "plan_identity_verified": True,
            "plan_hash_verified": True,
            "plan_contract_verified": True,
            "plan_steps_verified": True,
            "evidence_requirements_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_plan_admission_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_plan_scope_verified": True,
            "plan_admission_single_use_verified": True,
            "duplicate_plan_admission_allowed": False,
            "plan_admission_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "plan_admission_type": PLAN_ADMISSION_TYPE,
            "plan_admission_status": PLAN_ADMISSION_STATUS,
        }
        body["plan_admission_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "plan_id": plan.plan_id,
                "plan_hash": plan.plan_hash,
                "plan_admitted_at": at,
                "plan_admission_type": PLAN_ADMISSION_TYPE,
            }
        )
        return OracleResearchResponsePlanAdmission(
            **body,
            plan_admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "PLAN_ADMISSION_TYPE",
    "PLAN_ADMISSION_STATUS",
    "OracleResearchResponsePlanAdmissionInvariantError",
    "OracleResearchResponsePlanAdmission",
    "OracleResearchResponsePlanAdmissionGate",
    "stable_hash",
]
