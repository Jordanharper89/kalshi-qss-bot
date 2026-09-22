from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_readiness_gate import (
    READINESS_STATUS as ORR_008_READINESS_STATUS,
    READINESS_TYPE as ORR_008_READINESS_TYPE,
    OracleResearchResponseEvidenceReadInvocationReadiness,
)

SCHEMA_VERSION = "ORR-009"
ENGINE_ID = "ORR-009"
POLICY_ID = "oracle.research-response.evidence-read-invocation-authorization.v1"
AUTHORIZATION_TYPE = "oracle_research_response_evidence_read_invocation_authorization"
AUTHORIZATION_STATUS = "oracle_research_response_evidence_read_invocations_authorized"


class OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
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
class OracleResearchResponseEvidenceReadInvocationAuthorization:
    authorization_id: str
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
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    authorized_invocation_ids: tuple[str, ...]
    authorized_invocation_hashes: tuple[str, ...]
    authorized_read_operations: tuple[str, ...]
    readiness_identity_verified: bool
    readiness_hash_verified: bool
    readiness_contract_verified: bool
    invocation_identity_verified: bool
    invocation_hashes_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_authorization_boundary_verified: bool
    read_only_boundary_verified: bool
    single_readiness_scope_verified: bool
    authorization_single_use_verified: bool
    duplicate_authorization_allowed: bool
    authorization_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    authorization_type: str
    authorization_status: str
    authorization_hash: str


class OracleResearchResponseEvidenceReadInvocationAuthorizationGate:
    def authorize(
        self,
        *,
        readiness: OracleResearchResponseEvidenceReadInvocationReadiness,
        authorized_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationAuthorization:
        if not isinstance(
            readiness,
            OracleResearchResponseEvidenceReadInvocationReadiness,
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "readiness must be canonical ORR-008 readiness"
            )

        readiness_body = asdict(readiness)
        supplied_hash = readiness_body.pop("readiness_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(readiness_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "ORR-008 readiness hash mismatch"
            )

        required = (
            _valid_sha256(readiness.readiness_id),
            _valid_sha256(readiness.evidence_admission_id),
            _valid_sha256(readiness.evidence_admission_hash),
            _valid_sha256(readiness.materialization_id),
            _valid_sha256(readiness.materialization_hash),
            _valid_sha256(readiness.plan_admission_id),
            _valid_sha256(readiness.plan_admission_hash),
            _valid_sha256(readiness.plan_id),
            _valid_sha256(readiness.plan_hash),
            _valid_sha256(readiness.admission_id),
            _valid_sha256(readiness.admission_hash),
            _valid_sha256(readiness.request_id),
            _valid_sha256(readiness.request_hash),
            readiness.readiness_type == ORR_008_READINESS_TYPE,
            readiness.readiness_status == ORR_008_READINESS_STATUS,
            bool(readiness.read_invocations),
            len(readiness.read_invocations) == len(readiness.evidence_requirements),
            readiness.evidence_admission_identity_verified,
            readiness.evidence_admission_hash_verified,
            readiness.evidence_admission_contract_verified,
            readiness.requirement_lineage_verified,
            readiness.read_operation_scope_verified,
            readiness.callable_binding_disabled_verified,
            readiness.callable_invocation_disabled_verified,
            readiness.deterministic_boundary_verified,
            readiness.immutable_readiness_boundary_verified,
            readiness.read_only_boundary_verified,
            readiness.single_evidence_admission_scope_verified,
            readiness.readiness_single_use_verified,
            not readiness.duplicate_readiness_allowed,
            not readiness.readiness_reversible,
        )
        forbidden = (
            readiness.runtime_serving_allowed,
            readiness.network_listener_allowed,
            readiness.database_connection_allowed,
            readiness.publication_allowed,
            readiness.qseries_handoff_allowed,
            readiness.qseries_execution_allowed,
            readiness.order_creation_allowed,
            readiness.funds_movement_allowed,
            readiness.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "ORR-008 readiness contract incomplete or unsafe"
            )

        invocation_ids: list[str] = []
        invocation_hashes: list[str] = []
        read_operations: list[str] = []
        expected_ordinals = tuple(range(1, len(readiness.read_invocations) + 1))

        for invocation in readiness.read_invocations:
            invocation_body = asdict(invocation)
            supplied_invocation_hash = invocation_body.pop("invocation_hash", None)
            if (
                not _valid_sha256(invocation.invocation_id)
                or not _valid_sha256(invocation.requirement_id)
                or not _valid_sha256(invocation.requirement_hash)
                or not _valid_sha256(supplied_invocation_hash)
                or stable_hash(invocation_body) != supplied_invocation_hash
                or not invocation.read_only
                or invocation.callable_bound
                or invocation.callable_invoked
                or invocation.external_side_effects_allowed
            ):
                raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                    "read invocation invalid or unsafe"
                )
            invocation_ids.append(invocation.invocation_id)
            invocation_hashes.append(invocation.invocation_hash)
            read_operations.append(invocation.read_operation)

        ordinals = tuple(item.ordinal for item in readiness.read_invocations)
        if (
            ordinals != expected_ordinals
            or len(set(invocation_ids)) != len(invocation_ids)
            or len(invocation_ids) != len(readiness.evidence_requirements)
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "read invocation identity, order, uniqueness, or count mismatch"
            )

        if (
            not isinstance(authorized_at, datetime)
            or authorized_at.tzinfo is None
            or authorized_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "authorized_at must be timezone-aware"
            )
        at = authorized_at.astimezone(timezone.utc)
        if at < readiness.readiness_certified_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError(
                "authorization cannot precede readiness"
            )

        body = {
            "readiness_id": readiness.readiness_id,
            "readiness_hash": readiness.readiness_hash,
            "evidence_admission_id": readiness.evidence_admission_id,
            "evidence_admission_hash": readiness.evidence_admission_hash,
            "materialization_id": readiness.materialization_id,
            "materialization_hash": readiness.materialization_hash,
            "plan_admission_id": readiness.plan_admission_id,
            "plan_admission_hash": readiness.plan_admission_hash,
            "plan_id": readiness.plan_id,
            "plan_hash": readiness.plan_hash,
            "admission_id": readiness.admission_id,
            "admission_hash": readiness.admission_hash,
            "request_id": readiness.request_id,
            "request_hash": readiness.request_hash,
            "dependency_receipt_id": readiness.dependency_receipt_id,
            "dependency_receipt_hash": readiness.dependency_receipt_hash,
            "source_runtime_completion_id": readiness.source_runtime_completion_id,
            "source_runtime_completion_hash": readiness.source_runtime_completion_hash,
            "subsystem_namespace": readiness.subsystem_namespace,
            "requester_id": readiness.requester_id,
            "correlation_id": readiness.correlation_id,
            "question_text": readiness.question_text,
            "response_mode": readiness.response_mode,
            "filters": readiness.filters,
            "requested_at": readiness.requested_at.astimezone(timezone.utc),
            "admitted_at": readiness.admitted_at.astimezone(timezone.utc),
            "planned_at": readiness.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": readiness.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": readiness.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": readiness.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": readiness.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": at,
            "plan_steps": readiness.plan_steps,
            "evidence_requirements": readiness.evidence_requirements,
            "authorized_invocation_ids": tuple(invocation_ids),
            "authorized_invocation_hashes": tuple(invocation_hashes),
            "authorized_read_operations": tuple(read_operations),
            "readiness_identity_verified": True,
            "readiness_hash_verified": True,
            "readiness_contract_verified": True,
            "invocation_identity_verified": True,
            "invocation_hashes_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_authorization_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_readiness_scope_verified": True,
            "authorization_single_use_verified": True,
            "duplicate_authorization_allowed": False,
            "authorization_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "authorization_type": AUTHORIZATION_TYPE,
            "authorization_status": AUTHORIZATION_STATUS,
        }
        body["authorization_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "readiness_id": readiness.readiness_id,
                "readiness_hash": readiness.readiness_hash,
                "authorized_at": at,
                "authorized_invocation_ids": tuple(invocation_ids),
                "authorization_type": AUTHORIZATION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_TYPE",
    "AUTHORIZATION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError",
    "OracleResearchResponseEvidenceReadInvocationAuthorization",
    "OracleResearchResponseEvidenceReadInvocationAuthorizationGate",
    "stable_hash",
]
