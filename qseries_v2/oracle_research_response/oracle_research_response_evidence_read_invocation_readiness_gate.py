from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_admission_gate import (
    EVIDENCE_ADMISSION_STATUS as ORR_007_EVIDENCE_ADMISSION_STATUS,
    EVIDENCE_ADMISSION_TYPE as ORR_007_EVIDENCE_ADMISSION_TYPE,
    OracleResearchResponseEvidenceRequirementAdmission,
)

SCHEMA_VERSION = "ORR-008"
ENGINE_ID = "ORR-008"
POLICY_ID = "oracle.research-response.evidence-read-invocation-readiness.v1"
READINESS_TYPE = "oracle_research_response_evidence_read_invocation_readiness"
READINESS_STATUS = "oracle_research_response_evidence_read_invocation_ready"

ALLOWED_READ_OPERATIONS = (
    "read_certified_analytics",
    "read_certified_observations",
    "read_certified_market_state",
    "read_certified_lineage",
)


class OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
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
class OracleResearchResponseEvidenceReadInvocation:
    invocation_id: str
    ordinal: int
    requirement_id: str
    requirement_hash: str
    requirement_name: str
    read_operation: str
    read_only: bool
    callable_bound: bool
    callable_invoked: bool
    external_side_effects_allowed: bool
    invocation_hash: str


@dataclass(frozen=True)
class OracleResearchResponseEvidenceReadInvocationReadiness:
    readiness_id: str
    evidence_admission_id: str
    evidence_admission_hash: str
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
    readiness_certified_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    read_invocations: tuple[OracleResearchResponseEvidenceReadInvocation, ...]
    evidence_admission_identity_verified: bool
    evidence_admission_hash_verified: bool
    evidence_admission_contract_verified: bool
    requirement_lineage_verified: bool
    read_operation_scope_verified: bool
    callable_binding_disabled_verified: bool
    callable_invocation_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_readiness_boundary_verified: bool
    read_only_boundary_verified: bool
    single_evidence_admission_scope_verified: bool
    readiness_single_use_verified: bool
    duplicate_readiness_allowed: bool
    readiness_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    readiness_type: str
    readiness_status: str
    readiness_hash: str


def _operation_for_requirement(requirement_name: str) -> str:
    if requirement_name in {
        "venue_identity",
        "market_price",
        "market_definition",
        "resolution_criteria",
        "validity_window",
        "filter_compliance",
    }:
        return "read_certified_market_state"
    if requirement_name in {
        "source_provenance",
        "freshness",
        "lineage",
        "read_only_certification",
        "source_conflicts",
    }:
        return "read_certified_lineage"
    if requirement_name in {
        "relevant_observations",
        "supporting_evidence",
        "counter_evidence",
        "risk_factors",
    }:
        return "read_certified_observations"
    return "read_certified_analytics"


class OracleResearchResponseEvidenceReadInvocationReadinessGate:
    def certify(
        self,
        *,
        evidence_admission: OracleResearchResponseEvidenceRequirementAdmission,
        readiness_certified_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationReadiness:
        if not isinstance(
            evidence_admission,
            OracleResearchResponseEvidenceRequirementAdmission,
        ):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "evidence_admission must be canonical ORR-007 admission"
            )

        admission_body = asdict(evidence_admission)
        supplied_hash = admission_body.pop("evidence_admission_hash", None)
        if (
            not _valid_sha256(supplied_hash)
            or stable_hash(admission_body) != supplied_hash
        ):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "ORR-007 evidence admission hash mismatch"
            )

        required = (
            _valid_sha256(evidence_admission.evidence_admission_id),
            _valid_sha256(evidence_admission.materialization_id),
            _valid_sha256(evidence_admission.materialization_hash),
            _valid_sha256(evidence_admission.plan_admission_id),
            _valid_sha256(evidence_admission.plan_admission_hash),
            _valid_sha256(evidence_admission.plan_id),
            _valid_sha256(evidence_admission.plan_hash),
            _valid_sha256(evidence_admission.admission_id),
            _valid_sha256(evidence_admission.admission_hash),
            _valid_sha256(evidence_admission.request_id),
            _valid_sha256(evidence_admission.request_hash),
            evidence_admission.evidence_admission_type
            == ORR_007_EVIDENCE_ADMISSION_TYPE,
            evidence_admission.evidence_admission_status
            == ORR_007_EVIDENCE_ADMISSION_STATUS,
            bool(evidence_admission.evidence_requirements),
            len(evidence_admission.admitted_requirement_ids)
            == len(evidence_admission.evidence_requirements),
            len(evidence_admission.admitted_requirement_hashes)
            == len(evidence_admission.evidence_requirements),
            evidence_admission.materialization_identity_verified,
            evidence_admission.materialization_hash_verified,
            evidence_admission.materialization_contract_verified,
            evidence_admission.requirement_identity_verified,
            evidence_admission.requirement_hashes_verified,
            evidence_admission.requirement_order_verified,
            evidence_admission.requirement_count_verified,
            evidence_admission.mandatory_read_only_requirements_verified,
            evidence_admission.deterministic_boundary_verified,
            evidence_admission.immutable_evidence_admission_boundary_verified,
            evidence_admission.read_only_boundary_verified,
            evidence_admission.single_materialization_scope_verified,
            evidence_admission.evidence_admission_single_use_verified,
            not evidence_admission.duplicate_evidence_admission_allowed,
            not evidence_admission.evidence_admission_reversible,
        )
        forbidden = (
            evidence_admission.runtime_serving_allowed,
            evidence_admission.network_listener_allowed,
            evidence_admission.database_connection_allowed,
            evidence_admission.publication_allowed,
            evidence_admission.qseries_handoff_allowed,
            evidence_admission.qseries_execution_allowed,
            evidence_admission.order_creation_allowed,
            evidence_admission.funds_movement_allowed,
            evidence_admission.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "ORR-007 evidence admission contract incomplete or unsafe"
            )

        if (
            len(set(evidence_admission.admitted_requirement_ids))
            != len(evidence_admission.admitted_requirement_ids)
            or not all(_valid_sha256(value) for value in evidence_admission.admitted_requirement_ids)
            or not all(_valid_sha256(value) for value in evidence_admission.admitted_requirement_hashes)
        ):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "requirement identities or hashes invalid"
            )

        if (
            not isinstance(readiness_certified_at, datetime)
            or readiness_certified_at.tzinfo is None
            or readiness_certified_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "readiness_certified_at must be timezone-aware"
            )
        at = readiness_certified_at.astimezone(timezone.utc)
        if at < evidence_admission.evidence_admitted_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                "readiness cannot precede evidence admission"
            )

        invocations = []
        for ordinal, (
            requirement_name,
            requirement_id,
            requirement_hash,
        ) in enumerate(
            zip(
                evidence_admission.evidence_requirements,
                evidence_admission.admitted_requirement_ids,
                evidence_admission.admitted_requirement_hashes,
            ),
            start=1,
        ):
            operation = _operation_for_requirement(requirement_name)
            if operation not in ALLOWED_READ_OPERATIONS:
                raise OracleResearchResponseEvidenceReadInvocationReadinessInvariantError(
                    "unsupported read operation"
                )
            invocation_body = {
                "ordinal": ordinal,
                "requirement_id": requirement_id,
                "requirement_hash": requirement_hash,
                "requirement_name": requirement_name,
                "read_operation": operation,
                "read_only": True,
                "callable_bound": False,
                "callable_invoked": False,
                "external_side_effects_allowed": False,
            }
            invocation_id = stable_hash(
                {
                    "engine_id": ENGINE_ID,
                    "evidence_admission_id": evidence_admission.evidence_admission_id,
                    **invocation_body,
                }
            )
            invocations.append(
                OracleResearchResponseEvidenceReadInvocation(
                    invocation_id=invocation_id,
                    **invocation_body,
                    invocation_hash=stable_hash(
                        {"invocation_id": invocation_id, **invocation_body}
                    ),
                )
            )

        body = {
            "evidence_admission_id": evidence_admission.evidence_admission_id,
            "evidence_admission_hash": evidence_admission.evidence_admission_hash,
            "materialization_id": evidence_admission.materialization_id,
            "materialization_hash": evidence_admission.materialization_hash,
            "plan_admission_id": evidence_admission.plan_admission_id,
            "plan_admission_hash": evidence_admission.plan_admission_hash,
            "plan_id": evidence_admission.plan_id,
            "plan_hash": evidence_admission.plan_hash,
            "admission_id": evidence_admission.admission_id,
            "admission_hash": evidence_admission.admission_hash,
            "request_id": evidence_admission.request_id,
            "request_hash": evidence_admission.request_hash,
            "dependency_receipt_id": evidence_admission.dependency_receipt_id,
            "dependency_receipt_hash": evidence_admission.dependency_receipt_hash,
            "source_runtime_completion_id": evidence_admission.source_runtime_completion_id,
            "source_runtime_completion_hash": evidence_admission.source_runtime_completion_hash,
            "subsystem_namespace": evidence_admission.subsystem_namespace,
            "requester_id": evidence_admission.requester_id,
            "correlation_id": evidence_admission.correlation_id,
            "question_text": evidence_admission.question_text,
            "response_mode": evidence_admission.response_mode,
            "filters": evidence_admission.filters,
            "requested_at": evidence_admission.requested_at.astimezone(timezone.utc),
            "admitted_at": evidence_admission.admitted_at.astimezone(timezone.utc),
            "planned_at": evidence_admission.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": evidence_admission.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": evidence_admission.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": evidence_admission.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": at,
            "plan_steps": evidence_admission.plan_steps,
            "evidence_requirements": evidence_admission.evidence_requirements,
            "read_invocations": tuple(invocations),
            "evidence_admission_identity_verified": True,
            "evidence_admission_hash_verified": True,
            "evidence_admission_contract_verified": True,
            "requirement_lineage_verified": True,
            "read_operation_scope_verified": True,
            "callable_binding_disabled_verified": True,
            "callable_invocation_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_readiness_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_evidence_admission_scope_verified": True,
            "readiness_single_use_verified": True,
            "duplicate_readiness_allowed": False,
            "readiness_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "readiness_type": READINESS_TYPE,
            "readiness_status": READINESS_STATUS,
        }
        body["readiness_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "evidence_admission_id": evidence_admission.evidence_admission_id,
                "evidence_admission_hash": evidence_admission.evidence_admission_hash,
                "readiness_certified_at": at,
                "invocation_ids": tuple(item.invocation_id for item in invocations),
                "readiness_type": READINESS_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationReadiness(
            **body,
            readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_TYPE",
    "READINESS_STATUS",
    "ALLOWED_READ_OPERATIONS",
    "OracleResearchResponseEvidenceReadInvocationReadinessInvariantError",
    "OracleResearchResponseEvidenceReadInvocation",
    "OracleResearchResponseEvidenceReadInvocationReadiness",
    "OracleResearchResponseEvidenceReadInvocationReadinessGate",
    "stable_hash",
]
