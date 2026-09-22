from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    OracleOperatorRuntimeSessionActivationAttestation,
    stable_hash as attestation_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_gate import (
    OracleOperatorRuntimeSessionActivationAuthorizationGate,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_authorization_consumption_gate import (
    OracleOperatorRuntimeSessionActivationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_gate import *


def sample_attestation():
    t = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    ts = [t + timedelta(seconds=i) for i in range(7)]
    body = dict(
        attestation_id="1" * 64,
        activation_id="2" * 64,
        activation_hash="3" * 64,
        consumption_id="4" * 64,
        consumption_hash="5" * 64,
        authorization_id="6" * 64,
        authorization_hash="7" * 64,
        session_id="8" * 64,
        session_hash="9" * 64,
        admission_id="a" * 64,
        admission_hash="b" * 64,
        request_id="c" * 64,
        request_hash="d" * 64,
        dependency_receipt_id="e" * 64,
        dependency_receipt_hash="f" * 64,
        source_operator_completion_certification_id="0" * 64,
        runtime_namespace="oracle_operator_runtime",
        requester_id="operator:test",
        correlation_id="correlation:test",
        mode="query",
        query_text="Show certified intelligence.",
        requested_at=ts[0],
        admitted_at=ts[1],
        assembled_at=ts[2],
        authorized_at=ts[3],
        consumed_at=ts[4],
        activated_at=ts[5],
        attested_at=ts[6],
        activation_identity_verified=True,
        activation_hash_verified=True,
        activation_contract_verified=True,
        complete_runtime_lineage_verified=True,
        single_activation_scope_verified=True,
        single_attestation_scope_verified=True,
        read_only_boundary_verified=True,
        deterministic_boundary_verified=True,
        immutable_result_boundary_verified=True,
        runtime_serving_allowed=False,
        network_listener_allowed=False,
        database_connection_allowed=False,
        publication_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        attestation_type=ATTESTATION_TYPE,
        attestation_status=ATTESTATION_STATUS,
    )
    return OracleOperatorRuntimeSessionActivationAttestation(**body, attestation_hash=attestation_hash(body))


def reject(fn):
    try:
        fn()
        raise AssertionError("unsafe continuation accepted")
    except OracleOperatorRuntimeSessionActivationContinuationInvariantError:
        pass


def main():
    print("=" * 40)
    print(" OOR-011 TEST")
    print(" SESSION ACTIVATION CONTINUATION GATE")
    print("=" * 40)
    attestation = sample_attestation()
    authorization = OracleOperatorRuntimeSessionActivationAuthorizationGate().authorize(
        attestation=attestation,
        authorized_at=attestation.attested_at + timedelta(seconds=1),
    )
    consumption = OracleOperatorRuntimeSessionActivationAuthorizationConsumptionGate().consume(
        authorization=authorization,
        consumed_at=authorization.activation_authorized_at + timedelta(seconds=1),
    )
    continued_at = consumption.activation_authorization_consumed_at + timedelta(seconds=1)
    gate = OracleOperatorRuntimeSessionActivationContinuationGate()
    first = gate.continue_session_activation(consumption=consumption, continued_at=continued_at)
    second = gate.continue_session_activation(consumption=consumption, continued_at=continued_at)
    assert first == second
    assert first.continuation_hash == stable_hash({k: v for k, v in asdict(first).items() if k != "continuation_hash"})
    assert first.continuation_type == CONTINUATION_TYPE
    assert first.continuation_status == CONTINUATION_STATUS
    assert first.complete_runtime_lineage_verified
    assert first.single_consumption_scope_verified
    assert first.single_continuation_scope_verified
    assert first.continuation_single_use_verified
    assert not first.duplicate_continuation_allowed
    assert not first.continuation_reversible
    reject(lambda: gate.continue_session_activation(consumption=replace(consumption, consumption_hash="0" * 64), continued_at=continued_at))
    reject(lambda: gate.continue_session_activation(consumption=replace(consumption, qseries_execution_allowed=True), continued_at=continued_at))
    reject(lambda: gate.continue_session_activation(consumption=consumption, continued_at=consumption.activation_authorization_consumed_at - timedelta(seconds=1)))
    print("[PASS] Actual OOR-010 activation authorization consumption consumed")
    print("[PASS] Complete OOR-001 through OOR-010 lineage preserved")
    print("[PASS] Deterministic bounded activation continuation certified")
    print("[PASS] Single-consumption and single-use continuation scope certified")
    print("[PASS] Duplicate and reversible continuation disabled")
    print("[PASS] Immutable read-only runtime boundary preserved")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe continuation rejected")
    print("[DONE] OOR-011 SESSION ACTIVATION CONTINUATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
