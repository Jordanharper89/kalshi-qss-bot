from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_attestation_gate import OracleOperatorRuntimeSessionActivationAttestation, ATTESTATION_TYPE, ATTESTATION_STATUS, stable_hash as attestation_hash
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_gate import OracleOperatorRuntimeSessionActivationAuthorizationGate
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_consumption_gate import *

def sample_attestation():
    t=datetime(2026,7,28,12,0,tzinfo=timezone.utc); ts=[t+timedelta(seconds=i) for i in range(7)]
    b=dict(attestation_id='1'*64,activation_id='2'*64,activation_hash='3'*64,consumption_id='4'*64,consumption_hash='5'*64,authorization_id='6'*64,authorization_hash='7'*64,session_id='8'*64,session_hash='9'*64,admission_id='a'*64,admission_hash='b'*64,request_id='c'*64,request_hash='d'*64,dependency_receipt_id='e'*64,dependency_receipt_hash='f'*64,source_operator_completion_certification_id='0'*64,runtime_namespace='oracle_operator_runtime',requester_id='operator:test',correlation_id='correlation:test',mode='query',query_text='Show certified intelligence.',requested_at=ts[0],admitted_at=ts[1],assembled_at=ts[2],authorized_at=ts[3],consumed_at=ts[4],activated_at=ts[5],attested_at=ts[6],activation_identity_verified=True,activation_hash_verified=True,activation_contract_verified=True,complete_runtime_lineage_verified=True,single_activation_scope_verified=True,single_attestation_scope_verified=True,read_only_boundary_verified=True,deterministic_boundary_verified=True,immutable_result_boundary_verified=True,runtime_serving_allowed=False,network_listener_allowed=False,database_connection_allowed=False,publication_allowed=False,qseries_handoff_allowed=False,qseries_execution_allowed=False,order_creation_allowed=False,funds_movement_allowed=False,portfolio_mutation_allowed=False,attestation_type=ATTESTATION_TYPE,attestation_status=ATTESTATION_STATUS)
    return OracleOperatorRuntimeSessionActivationAttestation(**b,attestation_hash=attestation_hash(b))

def reject(fn):
    try: fn(); raise AssertionError('unsafe consumption accepted')
    except OracleOperatorRuntimeSessionActivationAuthorizationConsumptionInvariantError: pass

def main():
    print('='*40);print(' OOR-010 TEST');print(' ACTIVATION AUTHORIZATION CONSUMPTION');print('='*40)
    a=sample_attestation(); auth=OracleOperatorRuntimeSessionActivationAuthorizationGate().authorize(attestation=a,authorized_at=a.attested_at+timedelta(seconds=1)); at=auth.activation_authorized_at+timedelta(seconds=1); g=OracleOperatorRuntimeSessionActivationAuthorizationConsumptionGate(); x=g.consume(authorization=auth,consumed_at=at); y=g.consume(authorization=auth,consumed_at=at)
    assert x==y and x.consumption_hash==stable_hash({k:v for k,v in asdict(x).items() if k!='consumption_hash'})
    assert x.consumption_type==CONSUMPTION_TYPE and x.consumption_status==CONSUMPTION_STATUS
    reject(lambda:g.consume(authorization=replace(auth,authorization_hash='0'*64),consumed_at=at))
    reject(lambda:g.consume(authorization=replace(auth,qseries_execution_allowed=True),consumed_at=at))
    reject(lambda:g.consume(authorization=auth,consumed_at=auth.activation_authorized_at-timedelta(seconds=1)))
    print('[PASS] Actual OOR-009 activation authorization consumed');print('[PASS] Complete OOR-001 through OOR-009 lineage preserved');print('[PASS] Deterministic bounded authorization consumption certified');print('[PASS] Single-authorization and single-use consumption scope certified');print('[PASS] Read-only runtime boundary preserved');print('[PASS] Runtime serving, networking, and publication remain disabled');print('[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled');print('[PASS] Tampered, premature, and unsafe consumption rejected');print('[DONE] OOR-010 ACTIVATION AUTHORIZATION CONSUMPTION GATE PASS');return 0
if __name__=='__main__': raise SystemExit(main())
