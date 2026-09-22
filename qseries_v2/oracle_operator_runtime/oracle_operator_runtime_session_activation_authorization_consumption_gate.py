from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_gate import (
    AUTHORIZATION_STATUS as OOR_009_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOR_009_AUTHORIZATION_TYPE,
    OracleOperatorRuntimeSessionActivationAuthorization,
)

SCHEMA_VERSION = "OOR-010"
ENGINE_ID = "OOR-010"
POLICY_ID = "oracle.operator-runtime-session-activation-authorization-consumption-gate.v1"
CONSUMPTION_TYPE = "oracle_operator_runtime_read_only_session_activation_authorization_consumption"
CONSUMPTION_STATUS = "oracle_operator_runtime_session_activation_authorization_consumed"

class OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError(ValueError):
    pass

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value,(str,int,float,bool)): return value
    raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError(f"unsupported value type: {type(value)!r}")

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()

def _sha(value: Any) -> bool:
    return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value)

@dataclass(frozen=True)
class OracleOperatorRuntimeSessionActivationAuthorizationConsumption:
    consumption_id: str
    activation_authorization_id: str
    activation_authorization_hash: str
    attestation_id: str
    attestation_hash: str
    activation_id: str
    activation_hash: str
    session_authorization_consumption_id: str
    session_authorization_consumption_hash: str
    session_authorization_id: str
    session_authorization_hash: str
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
    session_authorized_at: datetime
    session_authorization_consumed_at: datetime
    activated_at: datetime
    attested_at: datetime
    activation_authorized_at: datetime
    activation_authorization_consumed_at: datetime
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_contract_verified: bool
    complete_runtime_lineage_verified: bool
    single_authorization_scope_verified: bool
    single_consumption_scope_verified: bool
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
    consumption_type: str
    consumption_status: str
    consumption_hash: str

class OracleOperatorRuntimeSessionActivationAuthorizationConsumptionGate:
    def consume(self, *, authorization: OracleOperatorRuntimeSessionActivationAuthorization, consumed_at: datetime) -> OracleOperatorRuntimeSessionActivationAuthorizationConsumption:
        if not isinstance(authorization, OracleOperatorRuntimeSessionActivationAuthorization):
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("authorization must be canonical OOR-009 activation authorization")
        body=asdict(authorization); supplied=body.pop("authorization_hash",None)
        if not _sha(supplied) or stable_hash(body)!=supplied:
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("OOR-009 authorization hash mismatch")
        ids=(authorization.authorization_id,authorization.attestation_id,authorization.attestation_hash,authorization.activation_id,authorization.activation_hash,authorization.consumption_id,authorization.consumption_hash,authorization.session_authorization_id,authorization.session_authorization_hash,authorization.session_id,authorization.session_hash,authorization.admission_id,authorization.admission_hash,authorization.request_id,authorization.request_hash,authorization.dependency_receipt_id,authorization.dependency_receipt_hash,authorization.source_operator_completion_certification_id)
        if not all(_sha(v) for v in ids):
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("OOR-009 lineage identity invalid")
        required=(authorization.attestation_identity_verified,authorization.attestation_hash_verified,authorization.attestation_contract_verified,authorization.complete_runtime_lineage_verified,authorization.single_attestation_scope_verified,authorization.single_authorization_scope_verified,authorization.read_only_boundary_verified,authorization.deterministic_boundary_verified,authorization.immutable_result_boundary_verified,authorization.authorization_type==OOR_009_AUTHORIZATION_TYPE,authorization.authorization_status==OOR_009_AUTHORIZATION_STATUS)
        if not all(required):
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("OOR-009 authorization contract incomplete")
        forbidden=(authorization.runtime_serving_allowed,authorization.network_listener_allowed,authorization.database_connection_allowed,authorization.publication_allowed,authorization.qseries_handoff_allowed,authorization.qseries_execution_allowed,authorization.order_creation_allowed,authorization.funds_movement_allowed,authorization.portfolio_mutation_allowed)
        if any(forbidden):
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("forbidden runtime capability detected")
        if not isinstance(consumed_at,datetime) or consumed_at.tzinfo is None or consumed_at.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("consumed_at must be timezone-aware")
        at=consumed_at.astimezone(timezone.utc)
        if at < authorization.activation_authorized_at.astimezone(timezone.utc):
            raise OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError("consumption cannot precede activation authorization")
        inherited={
            "activation_authorization_id":authorization.authorization_id,"activation_authorization_hash":authorization.authorization_hash,"attestation_id":authorization.attestation_id,"attestation_hash":authorization.attestation_hash,"activation_id":authorization.activation_id,"activation_hash":authorization.activation_hash,"session_authorization_consumption_id":authorization.consumption_id,"session_authorization_consumption_hash":authorization.consumption_hash,"session_authorization_id":authorization.session_authorization_id,"session_authorization_hash":authorization.session_authorization_hash,"session_id":authorization.session_id,"session_hash":authorization.session_hash,"admission_id":authorization.admission_id,"admission_hash":authorization.admission_hash,"request_id":authorization.request_id,"request_hash":authorization.request_hash,"dependency_receipt_id":authorization.dependency_receipt_id,"dependency_receipt_hash":authorization.dependency_receipt_hash,"source_operator_completion_certification_id":authorization.source_operator_completion_certification_id,"runtime_namespace":authorization.runtime_namespace,"requester_id":authorization.requester_id,"correlation_id":authorization.correlation_id,"mode":authorization.mode,"query_text":authorization.query_text,"requested_at":authorization.requested_at.astimezone(timezone.utc),"admitted_at":authorization.admitted_at.astimezone(timezone.utc),"assembled_at":authorization.assembled_at.astimezone(timezone.utc),"session_authorized_at":authorization.session_authorized_at.astimezone(timezone.utc),"session_authorization_consumed_at":authorization.consumed_at.astimezone(timezone.utc),"activated_at":authorization.activated_at.astimezone(timezone.utc),"attested_at":authorization.attested_at.astimezone(timezone.utc),"activation_authorized_at":authorization.activation_authorized_at.astimezone(timezone.utc),"activation_authorization_consumed_at":at,
            "authorization_identity_verified":True,"authorization_hash_verified":True,"authorization_contract_verified":True,"complete_runtime_lineage_verified":True,"single_authorization_scope_verified":True,"single_consumption_scope_verified":True,"read_only_boundary_verified":True,"deterministic_boundary_verified":True,"immutable_result_boundary_verified":True,"runtime_serving_allowed":False,"network_listener_allowed":False,"database_connection_allowed":False,"publication_allowed":False,"qseries_handoff_allowed":False,"qseries_execution_allowed":False,"order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"consumption_type":CONSUMPTION_TYPE,"consumption_status":CONSUMPTION_STATUS}
        inherited["consumption_id"]=stable_hash({"engine_id":ENGINE_ID,"authorization_id":authorization.authorization_id,"authorization_hash":authorization.authorization_hash,"consumed_at":at,"consumption_type":CONSUMPTION_TYPE})
        return OracleOperatorRuntimeSessionActivationAuthorizationConsumption(**inherited,consumption_hash=stable_hash(inherited))
