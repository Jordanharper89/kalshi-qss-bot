from __future__ import annotations

import hashlib, json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_attestation_gate import (
    ATTESTATION_STATUS as OOR_008_ATTESTATION_STATUS,
    ATTESTATION_TYPE as OOR_008_ATTESTATION_TYPE,
    OracleOperatorRuntimeSessionActivationAttestation,
)

SCHEMA_VERSION = "OOR-009"
ENGINE_ID = "OOR-009"
POLICY_ID = "oracle.operator-runtime-session-activation-authorization-gate.v1"
AUTHORIZATION_TYPE = "oracle_operator_runtime_read_only_session_activation_authorization"
AUTHORIZATION_STATUS = "oracle_operator_runtime_session_activation_authorized"

class OracleOperatorRuntimeSessionActivationAuthorizationInvariantError(ValueError): pass

def _canonical(v: Any) -> Any:
    if is_dataclass(v): return _canonical(asdict(v))
    if isinstance(v, Mapping): return {str(k):_canonical(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)): return [_canonical(x) for x in v]
    if isinstance(v,datetime):
        if v.tzinfo is None or v.utcoffset() is None: raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("datetime must be timezone-aware")
        return v.astimezone(timezone.utc).isoformat()
    if v is None or isinstance(v,(str,int,float,bool)): return v
    raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError(f"unsupported value type: {type(v)!r}")

def stable_hash(v: Any)->str:
    return hashlib.sha256(json.dumps(_canonical(v),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _sha(v:Any)->bool: return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v)

@dataclass(frozen=True)
class OracleOperatorRuntimeSessionActivationAuthorization:
    authorization_id: str
    attestation_id: str
    attestation_hash: str
    activation_id: str
    activation_hash: str
    consumption_id: str
    consumption_hash: str
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
    consumed_at: datetime
    activated_at: datetime
    attested_at: datetime
    activation_authorized_at: datetime
    attestation_identity_verified: bool
    attestation_hash_verified: bool
    attestation_contract_verified: bool
    complete_runtime_lineage_verified: bool
    single_attestation_scope_verified: bool
    single_authorization_scope_verified: bool
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
    authorization_type: str
    authorization_status: str
    authorization_hash: str

class OracleOperatorRuntimeSessionActivationAuthorizationGate:
    def authorize(self, *, attestation: OracleOperatorRuntimeSessionActivationAttestation, authorized_at: datetime)->OracleOperatorRuntimeSessionActivationAuthorization:
        if not isinstance(attestation, OracleOperatorRuntimeSessionActivationAttestation): raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("attestation must be canonical OOR-008 activation attestation")
        body=asdict(attestation); supplied=body.pop("attestation_hash",None)
        if not _sha(supplied) or stable_hash(body)!=supplied: raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("OOR-008 attestation hash mismatch")
        ids=(attestation.attestation_id,attestation.activation_id,attestation.activation_hash,attestation.consumption_id,attestation.consumption_hash,attestation.authorization_id,attestation.authorization_hash,attestation.session_id,attestation.session_hash,attestation.admission_id,attestation.admission_hash,attestation.request_id,attestation.request_hash,attestation.dependency_receipt_id,attestation.dependency_receipt_hash,attestation.source_operator_completion_certification_id)
        if not all(_sha(x) for x in ids): raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("OOR-008 lineage identity invalid")
        req=(attestation.activation_identity_verified,attestation.activation_hash_verified,attestation.activation_contract_verified,attestation.complete_runtime_lineage_verified,attestation.single_activation_scope_verified,attestation.single_attestation_scope_verified,attestation.read_only_boundary_verified,attestation.deterministic_boundary_verified,attestation.immutable_result_boundary_verified,attestation.attestation_type==OOR_008_ATTESTATION_TYPE,attestation.attestation_status==OOR_008_ATTESTATION_STATUS)
        if not all(req): raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("OOR-008 attestation contract incomplete")
        forbidden=(attestation.runtime_serving_allowed,attestation.network_listener_allowed,attestation.database_connection_allowed,attestation.publication_allowed,attestation.qseries_handoff_allowed,attestation.qseries_execution_allowed,attestation.order_creation_allowed,attestation.funds_movement_allowed,attestation.portfolio_mutation_allowed)
        if any(forbidden): raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("forbidden runtime capability detected")
        if not isinstance(authorized_at,datetime) or authorized_at.tzinfo is None or authorized_at.utcoffset() is None: raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("authorized_at must be timezone-aware")
        at=authorized_at.astimezone(timezone.utc)
        if at < attestation.attested_at.astimezone(timezone.utc): raise OracleOperatorRuntimeSessionActivationAuthorizationInvariantError("authorization cannot precede attestation")
        inherited={
          "attestation_id":attestation.attestation_id,"attestation_hash":attestation.attestation_hash,"activation_id":attestation.activation_id,"activation_hash":attestation.activation_hash,"consumption_id":attestation.consumption_id,"consumption_hash":attestation.consumption_hash,"session_authorization_id":attestation.authorization_id,"session_authorization_hash":attestation.authorization_hash,"session_id":attestation.session_id,"session_hash":attestation.session_hash,"admission_id":attestation.admission_id,"admission_hash":attestation.admission_hash,"request_id":attestation.request_id,"request_hash":attestation.request_hash,"dependency_receipt_id":attestation.dependency_receipt_id,"dependency_receipt_hash":attestation.dependency_receipt_hash,"source_operator_completion_certification_id":attestation.source_operator_completion_certification_id,"runtime_namespace":attestation.runtime_namespace,"requester_id":attestation.requester_id,"correlation_id":attestation.correlation_id,"mode":attestation.mode,"query_text":attestation.query_text,"requested_at":attestation.requested_at.astimezone(timezone.utc),"admitted_at":attestation.admitted_at.astimezone(timezone.utc),"assembled_at":attestation.assembled_at.astimezone(timezone.utc),"session_authorized_at":attestation.authorized_at.astimezone(timezone.utc),"consumed_at":attestation.consumed_at.astimezone(timezone.utc),"activated_at":attestation.activated_at.astimezone(timezone.utc),"attested_at":attestation.attested_at.astimezone(timezone.utc),"activation_authorized_at":at,
          "attestation_identity_verified":True,"attestation_hash_verified":True,"attestation_contract_verified":True,"complete_runtime_lineage_verified":True,"single_attestation_scope_verified":True,"single_authorization_scope_verified":True,"read_only_boundary_verified":True,"deterministic_boundary_verified":True,"immutable_result_boundary_verified":True,"runtime_serving_allowed":False,"network_listener_allowed":False,"database_connection_allowed":False,"publication_allowed":False,"qseries_handoff_allowed":False,"qseries_execution_allowed":False,"order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"authorization_type":AUTHORIZATION_TYPE,"authorization_status":AUTHORIZATION_STATUS}
        inherited["authorization_id"]=stable_hash({"engine_id":ENGINE_ID,"attestation_id":attestation.attestation_id,"attestation_hash":attestation.attestation_hash,"authorized_at":at,"authorization_type":AUTHORIZATION_TYPE})
        return OracleOperatorRuntimeSessionActivationAuthorization(**inherited,authorization_hash=stable_hash(inherited))
