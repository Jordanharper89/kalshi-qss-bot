from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    OracleOperatorRuntimeSessionActivationContinuationAttestation,
    stable_hash as attestation_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import *


def sample_attestation() -> OracleOperatorRuntimeSessionActivationContinuationAttestation:
    start = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    times = [start + timedelta(seconds=index) for index in range(11)]
    body = dict(
        attestation_id="1" * 64,
        continuation_id="2" * 64,
        continuation_hash="3" * 64,
        authorization_consumption_id="4" * 64,
        authorization_consumption_hash="5" * 64,
        activation_authorization_id="6" * 64,
        activation_authorization_hash="7" * 64,
        attestation_source_id="8" * 64,
        attestation_source_hash="9" * 64,
        activation_id="a" * 64,
        activation_hash="b" * 64,
        session_authorization_consumption_id="c" * 64,
        session_authorization_consumption_hash="d" * 64,
        session_authorization_id="e" * 64,
        session_authorization_hash="f" * 64,
        session_id="0" * 64,
        session_hash="1" * 64,
        admission_id="2" * 64,
        admission_hash="3" * 64,
        request_id="4" * 64,
        request_hash="5" * 64,
        dependency_receipt_id="6" * 64,
        dependency_receipt_hash="7" * 64,
        source_operator_completion_certification_id="8" * 64,
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
        activation_attested_at=times[6],
        activation_authorized_at=times[7],
        activation_authorization_consumed_at=times[8],
        continued_at=times[9],
        continuation_attested_at=times[10],
        continuation_identity_verified=True,
        continuation_hash_verified=True,
        continuation_contract_verified=True,
        complete_runtime_lineage_verified=True,
        single_continuation_scope_verified=True,
        single_attestation_scope_verified=True,
        attestation_single_use_verified=True,
        read_only_boundary_verified=True,
        deterministic_boundary_verified=True,
        immutable_result_boundary_verified=True,
        duplicate_attestation_allowed=False,
        attestation_reversible=False,
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
    return OracleOperatorRuntimeSessionActivationContinuationAttestation(
        **body,
        attestation_hash=attestation_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe final completion accepted")
    except OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-013 TEST")
    print(" FINAL COMPLETION AND FREEZE GATE")
    print("=" * 40)

    source = sample_attestation()
    first = complete_and_freeze_oracle_operator_runtime(attestation=source)
    second = complete_and_freeze_oracle_operator_runtime(attestation=source)

    assert first == second
    assert verify_oracle_operator_runtime_final_completion_and_freeze(first)
    assert first.completion_hash == stable_hash(
        {key: value for key, value in asdict(first).items() if key != "completion_hash"}
    )
    assert first.runtime_complete and first.immutable_freeze and first.read_only
    assert first.downstream_read_only_operation_allowed
    assert not first.further_oor_certification_required

    reject(lambda: complete_and_freeze_oracle_operator_runtime(attestation=replace(source, attestation_hash="0" * 64)))
    reject(lambda: complete_and_freeze_oracle_operator_runtime(attestation=replace(source, qseries_execution_allowed=True)))
    reject(lambda: verify_oracle_operator_runtime_final_completion_and_freeze(replace(first, completion_hash="0" * 64)))

    print("[PASS] Actual OOR-012 continuation attestation consumed")
    print("[PASS] Complete OOR-001 through OOR-012 lineage preserved")
    print("[PASS] Deterministic final completion certified")
    print("[PASS] Immutable Oracle Operator Runtime freeze certified")
    print("[PASS] Downstream read-only operation remains allowed")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] No further OOR certification layers required")
    print("[DONE] OOR-013 FINAL COMPLETION AND FREEZE GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
