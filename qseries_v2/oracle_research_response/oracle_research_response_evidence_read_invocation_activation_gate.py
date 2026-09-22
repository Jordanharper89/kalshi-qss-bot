from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_consumption_gate import (
    CONSUMPTION_STATUS as ORR_010_CONSUMPTION_STATUS,
    CONSUMPTION_TYPE as ORR_010_CONSUMPTION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption,
)

SCHEMA_VERSION = "ORR-011"
ENGINE_ID = "ORR-011"
POLICY_ID = "oracle.research-response.evidence-read-invocation-activation.v1"
ACTIVATION_TYPE = "oracle_research_response_evidence_read_invocation_activation"
ACTIVATION_STATUS = "oracle_research_response_evidence_read_invocations_activated"


class OracleResearchResponseEvidenceReadInvocationActivationInvariantError(ValueError):
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
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
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
class OracleResearchResponseActivatedEvidenceReadInvocation:
    activation_record_id: str
    ordinal: int
    invocation_id: str
    invocation_hash: str
    read_operation: str
    read_only: bool
    activation_permitted: bool
    callable_bound: bool
    callable_invoked: bool
    result_materialized: bool
    external_side_effects_allowed: bool
    activation_record_hash: str


@dataclass(frozen=True)
class OracleResearchResponseEvidenceReadInvocationActivation:
    activation_id: str
    consumption_id: str
    consumption_hash: str
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
    activated_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    activated_invocations: tuple[OracleResearchResponseActivatedEvidenceReadInvocation, ...]
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_contract_verified: bool
    invocation_lineage_verified: bool
    invocation_hashes_verified: bool
    invocation_order_verified: bool
    invocation_count_verified: bool
    approved_read_operations_verified: bool
    activation_scope_verified: bool
    callable_binding_remains_disabled_verified: bool
    callable_invocation_remains_disabled_verified: bool
    result_materialization_remains_disabled_verified: bool
    deterministic_boundary_verified: bool
    immutable_activation_boundary_verified: bool
    read_only_boundary_verified: bool
    single_consumption_scope_verified: bool
    activation_single_use_verified: bool
    duplicate_activation_allowed: bool
    activation_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    activation_type: str
    activation_status: str
    activation_hash: str


class OracleResearchResponseEvidenceReadInvocationActivationGate:
    def activate(
        self,
        *,
        consumption: OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption,
        activated_at: datetime,
    ) -> OracleResearchResponseEvidenceReadInvocationActivation:
        if not isinstance(
            consumption,
            OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption,
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "consumption must be canonical ORR-010 consumption"
            )

        consumption_body = asdict(consumption)
        supplied_hash = consumption_body.pop("consumption_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(consumption_body) != supplied_hash:
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "ORR-010 consumption hash mismatch"
            )

        required = (
            _valid_sha256(consumption.consumption_id),
            _valid_sha256(consumption.authorization_id),
            _valid_sha256(consumption.authorization_hash),
            _valid_sha256(consumption.readiness_id),
            _valid_sha256(consumption.readiness_hash),
            _valid_sha256(consumption.evidence_admission_id),
            _valid_sha256(consumption.evidence_admission_hash),
            _valid_sha256(consumption.materialization_id),
            _valid_sha256(consumption.materialization_hash),
            _valid_sha256(consumption.plan_admission_id),
            _valid_sha256(consumption.plan_admission_hash),
            _valid_sha256(consumption.plan_id),
            _valid_sha256(consumption.plan_hash),
            _valid_sha256(consumption.admission_id),
            _valid_sha256(consumption.admission_hash),
            _valid_sha256(consumption.request_id),
            _valid_sha256(consumption.request_hash),
            consumption.consumption_type == ORR_010_CONSUMPTION_TYPE,
            consumption.consumption_status == ORR_010_CONSUMPTION_STATUS,
            bool(consumption.consumed_invocation_ids),
            len(consumption.consumed_invocation_ids)
            == len(consumption.consumed_invocation_hashes)
            == len(consumption.consumed_read_operations)
            == len(consumption.evidence_requirements),
            consumption.authorization_identity_verified,
            consumption.authorization_hash_verified,
            consumption.authorization_contract_verified,
            consumption.invocation_lineage_verified,
            consumption.invocation_hashes_verified,
            consumption.invocation_order_verified,
            consumption.invocation_count_verified,
            consumption.approved_read_operations_verified,
            consumption.callable_binding_remains_disabled_verified,
            consumption.callable_invocation_remains_disabled_verified,
            consumption.deterministic_boundary_verified,
            consumption.immutable_consumption_boundary_verified,
            consumption.read_only_boundary_verified,
            consumption.single_authorization_scope_verified,
            consumption.consumption_single_use_verified,
            not consumption.duplicate_consumption_allowed,
            not consumption.consumption_reversible,
        )
        forbidden = (
            consumption.runtime_serving_allowed,
            consumption.network_listener_allowed,
            consumption.database_connection_allowed,
            consumption.publication_allowed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.order_creation_allowed,
            consumption.funds_movement_allowed,
            consumption.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "ORR-010 consumption contract incomplete or unsafe"
            )

        if (
            len(set(consumption.consumed_invocation_ids))
            != len(consumption.consumed_invocation_ids)
            or not all(_valid_sha256(value) for value in consumption.consumed_invocation_ids)
            or not all(_valid_sha256(value) for value in consumption.consumed_invocation_hashes)
            or not all(isinstance(value, str) and value for value in consumption.consumed_read_operations)
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "consumed invocation identities, hashes, or operations invalid"
            )

        if (
            not isinstance(activated_at, datetime)
            or activated_at.tzinfo is None
            or activated_at.utcoffset() is None
        ):
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "activated_at must be timezone-aware"
            )
        at = activated_at.astimezone(timezone.utc)
        if at < consumption.consumed_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceReadInvocationActivationInvariantError(
                "activation cannot precede consumption"
            )

        activated = []
        for ordinal, (invocation_id, invocation_hash, read_operation) in enumerate(
            zip(
                consumption.consumed_invocation_ids,
                consumption.consumed_invocation_hashes,
                consumption.consumed_read_operations,
            ),
            start=1,
        ):
            record_body = {
                "ordinal": ordinal,
                "invocation_id": invocation_id,
                "invocation_hash": invocation_hash,
                "read_operation": read_operation,
                "read_only": True,
                "activation_permitted": True,
                "callable_bound": False,
                "callable_invoked": False,
                "result_materialized": False,
                "external_side_effects_allowed": False,
            }
            record_id = stable_hash(
                {
                    "engine_id": ENGINE_ID,
                    "consumption_id": consumption.consumption_id,
                    **record_body,
                }
            )
            activated.append(
                OracleResearchResponseActivatedEvidenceReadInvocation(
                    activation_record_id=record_id,
                    **record_body,
                    activation_record_hash=stable_hash(
                        {"activation_record_id": record_id, **record_body}
                    ),
                )
            )

        body = {
            "consumption_id": consumption.consumption_id,
            "consumption_hash": consumption.consumption_hash,
            "authorization_id": consumption.authorization_id,
            "authorization_hash": consumption.authorization_hash,
            "readiness_id": consumption.readiness_id,
            "readiness_hash": consumption.readiness_hash,
            "evidence_admission_id": consumption.evidence_admission_id,
            "evidence_admission_hash": consumption.evidence_admission_hash,
            "materialization_id": consumption.materialization_id,
            "materialization_hash": consumption.materialization_hash,
            "plan_admission_id": consumption.plan_admission_id,
            "plan_admission_hash": consumption.plan_admission_hash,
            "plan_id": consumption.plan_id,
            "plan_hash": consumption.plan_hash,
            "admission_id": consumption.admission_id,
            "admission_hash": consumption.admission_hash,
            "request_id": consumption.request_id,
            "request_hash": consumption.request_hash,
            "dependency_receipt_id": consumption.dependency_receipt_id,
            "dependency_receipt_hash": consumption.dependency_receipt_hash,
            "source_runtime_completion_id": consumption.source_runtime_completion_id,
            "source_runtime_completion_hash": consumption.source_runtime_completion_hash,
            "subsystem_namespace": consumption.subsystem_namespace,
            "requester_id": consumption.requester_id,
            "correlation_id": consumption.correlation_id,
            "question_text": consumption.question_text,
            "response_mode": consumption.response_mode,
            "filters": consumption.filters,
            "requested_at": consumption.requested_at.astimezone(timezone.utc),
            "admitted_at": consumption.admitted_at.astimezone(timezone.utc),
            "planned_at": consumption.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": consumption.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": consumption.materialized_at.astimezone(timezone.utc),
            "evidence_admitted_at": consumption.evidence_admitted_at.astimezone(timezone.utc),
            "readiness_certified_at": consumption.readiness_certified_at.astimezone(timezone.utc),
            "authorized_at": consumption.authorized_at.astimezone(timezone.utc),
            "consumed_at": consumption.consumed_at.astimezone(timezone.utc),
            "activated_at": at,
            "plan_steps": consumption.plan_steps,
            "evidence_requirements": consumption.evidence_requirements,
            "activated_invocations": tuple(activated),
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_contract_verified": True,
            "invocation_lineage_verified": True,
            "invocation_hashes_verified": True,
            "invocation_order_verified": True,
            "invocation_count_verified": True,
            "approved_read_operations_verified": True,
            "activation_scope_verified": True,
            "callable_binding_remains_disabled_verified": True,
            "callable_invocation_remains_disabled_verified": True,
            "result_materialization_remains_disabled_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_activation_boundary_verified": True,
            "read_only_boundary_verified": True,
            "single_consumption_scope_verified": True,
            "activation_single_use_verified": True,
            "duplicate_activation_allowed": False,
            "activation_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "activation_type": ACTIVATION_TYPE,
            "activation_status": ACTIVATION_STATUS,
        }
        body["activation_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "consumption_id": consumption.consumption_id,
                "consumption_hash": consumption.consumption_hash,
                "activated_at": at,
                "activation_record_ids": tuple(
                    item.activation_record_id for item in activated
                ),
                "activation_type": ACTIVATION_TYPE,
            }
        )
        return OracleResearchResponseEvidenceReadInvocationActivation(
            **body,
            activation_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ACTIVATION_TYPE",
    "ACTIVATION_STATUS",
    "OracleResearchResponseEvidenceReadInvocationActivationInvariantError",
    "OracleResearchResponseActivatedEvidenceReadInvocation",
    "OracleResearchResponseEvidenceReadInvocationActivation",
    "OracleResearchResponseEvidenceReadInvocationActivationGate",
    "stable_hash",
]
