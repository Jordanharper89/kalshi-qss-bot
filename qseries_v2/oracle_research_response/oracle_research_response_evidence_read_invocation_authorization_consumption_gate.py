from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_gate import (
    AUTHORIZATION_STATUS as ORR_009_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as ORR_009_AUTHORIZATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAuthorization,
)

SCHEMA_VERSION = "ORR-010"
ENGINE_ID = "ORR-010"
POLICY_ID = "oracle.research-response.evidence-read-invocation-authorization-consumption.v1"
CONSUMPTION_TYPE = "oracle_research_response_evidence_read_invocation_authorization_consumption"
CONSUMPTION_STATUS = "oracle_research_response_evidence_read_invocation_authorization_consumed"


class OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
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
class OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption:
    consumption_id: str
    authorization_id: str
    authorization_hash: str
    readiness_id: str
    readiness_hash: str
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
    authorized_at: datetime
    consumed_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    consumed_invocation_ids: tuple[str, ...]
    consumed_invocation_hashes: tuple[str, ...]
    consumed_read_operations: tuple[str, ...]
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_contract_verified: bool
    invocation_lineage_verified: bool
    invocation_hashes_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_consumption_boundary_verified: bool
    read_only_boundary_verified: bool
    single_authorization_scope_verified: bool
    consumption_single_use_verified: bool
    duplicate_consumption_allowed: bool
    consumption_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    consumption_type: str
    consumption_status: str
    consumption_hash: str


class OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionGate:
    def consume(
        self,
        *,
        authorization: OracleResearchResponseEvidenceReadInvocationAuthorization,
        consumed_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption:
        if not isinstance(
            authorization,
            OracleResearchResponseEvidenceReadInvocationAuthorization,
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "authorization must be canonical ORR-009 authorization"
            )

        authorization_body = asdict(authorization)
        supplied_hash = authorization_body.pop("authorization_hash", None)
        if (
            not _valid_sha256(supplied_hash)
            or stable_hash(authorization_body) != supplied_hash
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "ORR-009 authorization hash mismatch"
            )

        required = (
            _valid_sha256(authorization.authorization_id),
            _valid_sha256(authorization.readiness_id),
            _valid_sha256(authorization.readiness_hash),
            _valid_sha256(authorization.evidence_admission_id),
            _valid_sha256(authorization.evidence_admission_hash),
            _valid_sha256(authorization.materialization_id),
            _valid_sha256(authorization.materialization_hash),
            _valid_sha256(authorization.plan_admission_id),
            _valid_sha256(authorization.plan_admission_hash),
            _valid_sha256(authorization.plan_id),
            _valid_sha256(authorization.plan_hash),
            _valid_sha256(authorization.admission_id),
            _valid_sha256(authorization.admission_hash),
            _valid_sha256(authorization.request_id),
            _valid_sha256(authorization.request_hash),
            authorization.authorization_type == ORR_009_AUTHORIZATION_TYPE,
            authorization.authorization_status == ORR_009_AUTHORIZATION_STATUS,
            bool(authorization.authorized_invocation_ids),
            len(authorization.authorized_invocation_ids)
            == len(authorization.authorized_invocation_hashes)
            == len(authorization.authorized_read_operations)
            == len(authorization.evidence_requirements),
            authorization.readiness_identity_verified,
            authorization.readiness_hash_verified,
            authorization.readiness_contract_verified,
            authorization.invocation_identity_verified,
            authorization.invocation_hashes_verified,
            authorization.invocation_order_verified,
            authorization.invocation_count_verified,
            authorization.approved_read_operations_verified,
            authorization.callable_binding_remains_disabled_verified,
            authorization.callable_invocation_remains_disabled_verified,
            authorization.deterministic_boundary_verified,
            authorization.immutable_authorization_boundary_verified,
            authorization.read_only_boundary_verified,
            authorization.single_readiness_scope_verified,
            authorization.authorization_single_use_verified,
            not authorization.duplicate_authorization_allowed,
            not authorization.authorization_reversible,
        )
        forbidden = (
            authorization.runtime_serving_allowed,
            authorization.network_listener_allowed,
            authorization.database_connection_allowed,
            authorization.publication_allowed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.order_creation_allowed,
            authorization.funds_movement_allowed,
            authorization.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "ORR-009 authorization contract incomplete or unsafe"
            )

        if (
            len(set(authorization.authorized_invocation_ids))
            != len(authorization.authorized_invocation_ids)
            or not all(_valid_sha256(value) for value in authorization.authorized_invocation_ids)
            or not all(_valid_sha256(value) for value in authorization.authorized_invocation_hashes)
            or not all(
                isinstance(value, str) and value
                for value in authorization.authorized_read_operations
            )
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "authorized invocation identities, hashes, or operations invalid"
            )

        if (
            not isinstance(consumed_at, datetime)
            or consumed_at.tzinfo is None
            or consumed_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "consumed_at must be timezone-aware"
            )
        at = consumed_at.astimezone(timezone.utc)
        if at < authorization.authorized_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError(
                "consumption cannot precede authorization"
            )

        body = {
            "authorization_id": authorization.authorization_id,
            "authorization_hash": authorization.authorization_hash,
            "readiness_id": authorization.readiness_id,
            "readiness_hash": authorization.readiness_hash,
            "evidence_admission_id": authorization.evidence_admission_id,
            "evidence_admission_hash": authorization.evidence_admission_hash,
            "materialization_id": authorization.materialization_id,
            "materialization_hash": authorization.materialization_hash,
            "plan_admission_id": authorization.plan_admission_id,
            "plan_admission_hash": authorization.plan_admission_hash,
            "plan_id": authorization.plan_id,
            "plan_hash": authorization.plan_hash,
            "admission_id": authorization.admission_id,
            "admission_hash": authorization.admission_hash,
            "request_id": authorization.request_id,
            "request_hash": authorization.request_hash,
            "dependency_receipt_id": authorization.dependency_receipt_id,
            "dependency_receipt_hash": authorization.dependency_receipt_hash,
            "source_runtime_completion_id": authorization.source_runtime_completion_id,
            "source_runtime_completion_hash": authorization.source_runtime_completion_hash,
            "subsystem_namespace": authorization.subsystem_namespace,
            "requester_id": authorization.requester_id,
            "correlation_id": authorization.correlation_id,
            "question_text": authorization.question_text,
            "response_mode": authorization.response_mode,
            "filters": authorization.filters,
            "requested_at": authorization.requested_at.astimezone(timezone.utc),
            "admitted_at": authorization.admitted_at.astimezone(timezone.utc),
            "planned_at": authorization.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": authorization.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": authorization.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": authorization.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": authorization.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": authorization.authorized_at.astimezone(timezone.utc),
            "consumed_at": at,
            "plan_steps": authorization.plan_steps,
            "evidence_requirements": authorization.evidence_requirements,
            "consumed_invocation_ids": authorization.authorized_invocation_ids,
            "consumed_invocation_hashes": authorization.authorized_invocation_hashes,
            "consumed_read_operations": authorization.authorized_read_operations,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_contract_verified": True,
            "invocation_lineage_verified": True,
            "invocation_hashes_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_consumption_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_authorization_scope_verified": True,
            "consumption_single_use_verified": True,
            "duplicate_consumption_allowed": False,
            "consumption_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "consumption_type": CONSUMPTION_TYPE,
            "consumption_status": CONSUMPTION_STATUS,
        }
        body["consumption_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "authorization_id": authorization.authorization_id,
                "authorization_hash": authorization.authorization_hash,
                "consumed_at": at,
                "consumed_invocation_ids": authorization.authorized_invocation_ids,
                "consumption_type": CONSUMPTION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption(
            **body,
            consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_TYPE",
    "CONSUMPTION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError",
    "OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption",
    "OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionGate",
    "stable_hash",
]
