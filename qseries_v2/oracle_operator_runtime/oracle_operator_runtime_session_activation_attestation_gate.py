from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_gate import (
    ACTIVATION_STATUS as OOR_007_ACTIVATION_STATUS,
    ACTIVATION_TYPE as OOR_007_ACTIVATION_TYPE,
    OracleOperatorRuntimeSessionActivation,
)

SCHEMA_VERSION = "OOR-008"
ENGINE_ID = "OOR-008"
POLICY_ID = "oracle.operator-runtime-session-activation-attestation-gate.v1"
ATTESTATION_TYPE = "oracle_operator_runtime_read_only_session_activation_attestation"
ATTESTATION_STATUS = "oracle_operator_runtime_session_activation_attested"


class OracleOperatorRuntimeSessionActivationAttestationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


@dataclass(frozen=True)
class OracleOperatorRuntimeSessionActivationAttestation:
    attestation_id: str
    activation_id: str
    activation_hash: str
    consumption_id: str
    consumption_hash: str
    authorization_id: str
    authorization_hash: str
    session_id: str
    session_hash: str
    admission_id: str
    admission_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    requester_id: str
    correlation_id: str
    mode: str
    query_text: str
    requested_at: datetime
    admitted_at: datetime
    assembled_at: datetime
    authorized_at: datetime
    consumed_at: datetime
    activated_at: datetime
    attested_at: datetime
    activation_identity_verified: bool
    activation_hash_verified: bool
    activation_contract_verified: bool
    complete_runtime_lineage_verified: bool
    single_activation_scope_verified: bool
    single_attestation_scope_verified: bool
    read_only_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    attestation_type: str
    attestation_status: str
    attestation_hash: str


class OracleOperatorRuntimeSessionActivationAttestationGate:
    @staticmethod
    def _verify_activation(activation: OracleOperatorRuntimeSessionActivation) -> None:
        if not isinstance(activation, OracleOperatorRuntimeSessionActivation):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "activation must be canonical OOR-007 session activation"
            )
        body = asdict(activation)
        supplied_hash = body.pop("activation_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation hash mismatch"
            )
        hashes = (
            activation.activation_id,
            activation.consumption_id,
            activation.consumption_hash,
            activation.authorization_id,
            activation.authorization_hash,
            activation.session_id,
            activation.session_hash,
            activation.admission_id,
            activation.admission_hash,
            activation.request_id,
            activation.request_hash,
            activation.dependency_receipt_id,
            activation.dependency_receipt_hash,
            activation.source_operator_completion_certification_id,
        )
        if not all(_valid_sha256(value) for value in hashes):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation lineage identity invalid"
            )
        if activation.mode not in {"query", "session", "console", "presentation"}:
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation mode invalid"
            )
        if not activation.query_text:
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation query text missing"
            )
        timestamps = (
            activation.requested_at,
            activation.admitted_at,
            activation.assembled_at,
            activation.authorized_at,
            activation.consumed_at,
            activation.activated_at,
        )
        if not all(
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() is not None
            for value in timestamps
        ):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation timestamps invalid"
            )
        normalized = [value.astimezone(timezone.utc) for value in timestamps]
        if normalized != sorted(normalized):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation timestamp lineage invalid"
            )
        required = (
            activation.consumption_identity_verified,
            activation.consumption_hash_verified,
            activation.consumption_contract_verified,
            activation.single_consumption_scope_verified,
            activation.single_activation_scope_verified,
            activation.read_only_boundary_verified,
            activation.deterministic_boundary_verified,
            activation.immutable_result_boundary_verified,
            activation.activation_type == OOR_007_ACTIVATION_TYPE,
            activation.activation_status == OOR_007_ACTIVATION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "OOR-007 activation contract incomplete"
            )
        forbidden = (
            activation.runtime_serving_allowed,
            activation.network_listener_allowed,
            activation.database_connection_allowed,
            activation.publication_allowed,
            activation.qseries_handoff_allowed,
            activation.qseries_execution_allowed,
            activation.order_creation_allowed,
            activation.funds_movement_allowed,
            activation.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "forbidden runtime capability detected"
            )

    def attest(
        self,
        *,
        activation: OracleOperatorRuntimeSessionActivation,
        attested_at: datetime,
    ) -> OracleOperatorRuntimeSessionActivationAttestation:
        self._verify_activation(activation)
        if (
            not isinstance(attested_at, datetime)
            or attested_at.tzinfo is None
            or attested_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "attested_at must be timezone-aware"
            )
        normalized_attested_at = attested_at.astimezone(timezone.utc)
        if normalized_attested_at < activation.activated_at.astimezone(timezone.utc):
            raise OracleOperatorRuntimeSessionActivationAttestationInvariantError(
                "attestation cannot precede activation"
            )
        attestation_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "activation_id": activation.activation_id,
                "activation_hash": activation.activation_hash,
                "attested_at": normalized_attested_at,
                "attestation_type": ATTESTATION_TYPE,
            }
        )
        inherited = {
            key: getattr(activation, key)
            for key in (
                "activation_id",
                "activation_hash",
                "consumption_id",
                "consumption_hash",
                "authorization_id",
                "authorization_hash",
                "session_id",
                "session_hash",
                "admission_id",
                "admission_hash",
                "request_id",
                "request_hash",
                "dependency_receipt_id",
                "dependency_receipt_hash",
                "source_operator_completion_certification_id",
                "runtime_namespace",
                "requester_id",
                "correlation_id",
                "mode",
                "query_text",
                "requested_at",
                "admitted_at",
                "assembled_at",
                "authorized_at",
                "consumed_at",
                "activated_at",
            )
        }
        inherited.update(
            {
                "attestation_id": attestation_id,
                "attested_at": normalized_attested_at,
                "activation_identity_verified": True,
                "activation_hash_verified": True,
                "activation_contract_verified": True,
                "complete_runtime_lineage_verified": True,
                "single_activation_scope_verified": True,
                "single_attestation_scope_verified": True,
                "read_only_boundary_verified": True,
                "deterministic_boundary_verified": True,
                "immutable_result_boundary_verified": True,
                "runtime_serving_allowed": False,
                "network_listener_allowed": False,
                "database_connection_allowed": False,
                "publication_allowed": False,
                "qseries_handoff_allowed": False,
                "qseries_execution_allowed": False,
                "order_creation_allowed": False,
                "funds_movement_allowed": False,
                "portfolio_mutation_allowed": False,
                "attestation_type": ATTESTATION_TYPE,
                "attestation_status": ATTESTATION_STATUS,
            }
        )
        for key in (
            "requested_at",
            "admitted_at",
            "assembled_at",
            "authorized_at",
            "consumed_at",
            "activated_at",
        ):
            inherited[key] = inherited[key].astimezone(timezone.utc)
        return OracleOperatorRuntimeSessionActivationAttestation(
            **inherited,
            attestation_hash=stable_hash(inherited),
        )
