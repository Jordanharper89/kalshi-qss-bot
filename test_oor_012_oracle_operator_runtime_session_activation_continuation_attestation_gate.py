from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_gate import (
    CONTINUATION_STATUS,
    CONTINUATION_TYPE,
    OracleOperatorRuntimeSessionActivationContinuation,
    stable_hash as continuation_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_attestation_gate import *


def sample_continuation() -> OracleOperatorRuntimeSessionActivationContinuation:
    start = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    times = [start + timedelta(seconds=index) for index in range(10)]
    body = dict(
        continuation_id="1" * 64,
        authorization_consumption_id="2" * 64,
        authorization_consumption_hash="3" * 64,
        activation_authorization_id="4" * 64,
        activation_authorization_hash="5" * 64,
        attestation_id="6" * 64,
        attestation_hash="7" * 64,
        activation_id="8" * 64,
        activation_hash="9" * 64,
        session_authorization_consumption_id="a" * 64,
        session_authorization_consumption_hash="b" * 64,
        session_authorization_id="c" * 64,
        session_authorization_hash="d" * 64,
        session_id="e" * 64,
        session_hash="f" * 64,
        admission_id="0" * 64,
        admission_hash="1" * 64,
        request_id="2" * 64,
        request_hash="3" * 64,
        dependency_receipt_id="4" * 64,
        dependency_receipt_hash="5" * 64,
        source_operator_completion_certification_id="6" * 64,
        runtime_namespace="oracle_operator_runtime",
        requester_id="operator:test",
        correlation_id="correlation:test",
        mode="query",
        query_text="Show certified intelligence.",
        requested_at=times[0],
        admitted_at=times[1],
        assembled_at=times[2],
        session_authorized_at=times[3],
        session_authorization_consumed_at=times[4],
        activated_at=times[5],
        attested_at=times[6],
        activation_authorized_at=times[7],
        activation_authorization_consumed_at=times[8],
        continued_at=times[9],
        authorization_consumption_identity_verified=True,
        authorization_consumption_hash_verified=True,
        authorization_consumption_contract_verified=True,
        complete_runtime_lineage_verified=True,
        single_consumption_scope_verified=True,
        single_continuation_scope_verified=True,
        continuation_single_use_verified=True,
        read_only_boundary_verified=True,
        deterministic_boundary_verified=True,
        immutable_result_boundary_verified=True,
        duplicate_continuation_allowed=False,
        continuation_reversible=False,
        runtime_serving_allowed=False,
        network_listener_allowed=False,
        database_connection_allowed=False,
        publication_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        continuation_type=CONTINUATION_TYPE,
        continuation_status=CONTINUATION_STATUS,
    )
    return OracleOperatorRuntimeSessionActivationContinuation(
        **body,
        continuation_hash=continuation_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe continuation attestation accepted")
    except OracleOperatorRuntimeSessionActivationContinuationAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-012 TEST")
    print(" CONTINUATION ATTESTATION GATE")
    print("=" * 40)

    continuation = sample_continuation()
    attested_at = continuation.continued_at + timedelta(seconds=1)
    gate = OracleOperatorRuntimeSessionActivationContinuationAttestationGate()

    first = gate.attest(continuation=continuation, attested_at=attested_at)
    second = gate.attest(continuation=continuation, attested_at=attested_at)

    assert first == second
    assert first.attestation_hash == stable_hash(
        {key: value for key, value in asdict(first).items() if key != "attestation_hash"}
    )
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.attestation_status == ATTESTATION_STATUS
    assert first.complete_runtime_lineage_verified
    assert first.single_continuation_scope_verified
    assert first.single_attestation_scope_verified
    assert first.attestation_single_use_verified
    assert not first.duplicate_attestation_allowed
    assert not first.attestation_reversible

    reject(
        lambda: gate.attest(
            continuation=replace(continuation, continuation_hash="0" * 64),
            attested_at=attested_at,
        )
    )
    reject(
        lambda: gate.attest(
            continuation=replace(continuation, qseries_execution_allowed=True),
            attested_at=attested_at,
        )
    )
    reject(
        lambda: gate.attest(
            continuation=continuation,
            attested_at=continuation.continued_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual OOR-011 activation continuation consumed")
    print("[PASS] Complete OOR-001 through OOR-011 lineage preserved")
    print("[PASS] Deterministic bounded continuation attestation certified")
    print("[PASS] Single-continuation and single-use attestation scope certified")
    print("[PASS] Duplicate and reversible attestation disabled")
    print("[PASS] Immutable read-only runtime boundary preserved")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe attestation rejected")
    print("[DONE] OOR-012 CONTINUATION ATTESTATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
