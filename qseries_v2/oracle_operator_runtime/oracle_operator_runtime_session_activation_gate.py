from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOR_006_CONSUMPTION_STATUS,
    CONSUMPTION_TYPE as OOR_006_CONSUMPTION_TYPE,
    OracleOperatorRuntimeSessionAuthorizationConsumption,
)

SCHEMA_VERSION = "OOR-007"
ENGINE_ID = "OOR-007"
POLICY_ID = "oracle.operator-runtime-session-activation-gate.v1"
ACTIVATION_TYPE = "oracle_operator_runtime_read_only_session_activation"
ACTIVATION_STATUS = "oracle_operator_runtime_session_activated"

class OracleOperatorRuntimeSessionActivationInvariantError(ValueError):
    pass

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None: raise OracleOperatorRuntimeSessionActivationInvariantError("datetime must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value,(str,int,float,bool)): return value
    raise OracleOperatorRuntimeSessionActivationInvariantError(f"unsupported value type: {type(value)!r}")

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()

def _valid_sha256(value: Any) -> bool:
    return isinstance(value,str) and len(value)==64 and all(c in "0123456789abcdef" for c in value)

@dataclass(frozen=True)
class OracleOperatorRuntimeSessionActivation:
    activation_id: str
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
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_contract_verified: bool
    single_consumption_scope_verified: bool
    single_activation_scope_verified: bool
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
    activation_type: str
    activation_status: str
    activation_hash: str

class OracleOperatorRuntimeSessionActivationGate:
    @staticmethod
    def _verify_consumption(consumption: OracleOperatorRuntimeSessionAuthorizationConsumption) -> None:
        if not isinstance(consumption, OracleOperatorRuntimeSessionAuthorizationConsumption):
            raise OracleOperatorRuntimeSessionActivationInvariantError("consumption must be canonical OOR-006 authorization consumption")
        body=asdict(consumption); supplied=body.pop("consumption_hash",None)
        if not _valid_sha256(supplied) or stable_hash(body)!=supplied:
            raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 consumption hash mismatch")
        hashes=(consumption.consumption_id,consumption.authorization_id,consumption.authorization_hash,consumption.session_id,consumption.session_hash,consumption.admission_id,consumption.admission_hash,consumption.request_id,consumption.request_hash,consumption.dependency_receipt_id,consumption.dependency_receipt_hash,consumption.source_operator_completion_certification_id)
        if not all(_valid_sha256(v) for v in hashes): raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 lineage identity invalid")
        if consumption.mode not in {"query","session","console","presentation"} or not consumption.query_text:
            raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 request scope invalid")
        times=(consumption.requested_at,consumption.admitted_at,consumption.assembled_at,consumption.authorized_at,consumption.consumed_at)
        if not all(isinstance(v,datetime) and v.tzinfo is not None and v.utcoffset() is not None for v in times):
            raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 timestamps invalid")
        utc=[v.astimezone(timezone.utc) for v in times]
        if utc != sorted(utc): raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 timestamp lineage invalid")
        required=(consumption.authorization_identity_verified,consumption.authorization_hash_verified,consumption.authorization_contract_verified,consumption.single_authorization_scope_verified,consumption.single_consumption_scope_verified,consumption.read_only_boundary_verified,consumption.deterministic_boundary_verified,consumption.immutable_result_boundary_verified,consumption.consumption_type==OOR_006_CONSUMPTION_TYPE,consumption.consumption_status==OOR_006_CONSUMPTION_STATUS)
        if not all(required): raise OracleOperatorRuntimeSessionActivationInvariantError("OOR-006 consumption contract incomplete")
        forbidden=(consumption.runtime_serving_allowed,consumption.network_listener_allowed,consumption.database_connection_allowed,consumption.publication_allowed,consumption.qseries_handoff_allowed,consumption.qseries_execution_allowed,consumption.order_creation_allowed,consumption.funds_movement_allowed,consumption.portfolio_mutation_allowed)
        if any(forbidden): raise OracleOperatorRuntimeSessionActivationInvariantError("forbidden runtime capability detected")

    def activate(self, *, consumption: OracleOperatorRuntimeSessionAuthorizationConsumption, activated_at: datetime) -> OracleOperatorRuntimeSessionActivation:
        self._verify_consumption(consumption)
        if not isinstance(activated_at,datetime) or activated_at.tzinfo is None or activated_at.utcoffset() is None:
            raise OracleOperatorRuntimeSessionActivationInvariantError("activated_at must be timezone-aware")
        normalized=activated_at.astimezone(timezone.utc)
        if normalized < consumption.consumed_at.astimezone(timezone.utc): raise OracleOperatorRuntimeSessionActivationInvariantError("activation cannot precede consumption")
        activation_id=stable_hash({"engine_id":ENGINE_ID,"consumption_id":consumption.consumption_id,"consumption_hash":consumption.consumption_hash,"activated_at":normalized,"activation_type":ACTIVATION_TYPE})
        body={k:getattr(consumption,k) for k in (
            "consumption_id","consumption_hash","authorization_id","authorization_hash","session_id","session_hash","admission_id","admission_hash","request_id","request_hash","dependency_receipt_id","dependency_receipt_hash","source_operator_completion_certification_id","runtime_namespace","requester_id","correlation_id","mode","query_text","requested_at","admitted_at","assembled_at","authorized_at","consumed_at")}
        body.update({"activation_id":activation_id,"activated_at":normalized,"consumption_identity_verified":True,"consumption_hash_verified":True,"consumption_contract_verified":True,"single_consumption_scope_verified":True,"single_activation_scope_verified":True,"read_only_boundary_verified":True,"deterministic_boundary_verified":True,"immutable_result_boundary_verified":True,"runtime_serving_allowed":False,"network_listener_allowed":False,"database_connection_allowed":False,"publication_allowed":False,"qseries_handoff_allowed":False,"qseries_execution_allowed":False,"order_creation_allowed":False,"funds_movement_allowed":False,"portfolio_mutation_allowed":False,"activation_type":ACTIVATION_TYPE,"activation_status":ACTIVATION_STATUS})
        for key in ("requested_at","admitted_at","assembled_at","authorized_at","consumed_at"): body[key]=body[key].astimezone(timezone.utc)
        return OracleOperatorRuntimeSessionActivation(**body,activation_hash=stable_hash(body))
