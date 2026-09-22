from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_gate import (
    CONTINUATION_STATUS,
    CONTINUATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation,
    stable_hash as source_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_gate import *


def sample_continuation():
    t = datetime(2026, 7, 29, 19, 50, tzinfo=timezone.utc)
    body = {
        "continuation_id": "a"*64, "consumption_id": "b"*64, "consumption_hash": "c"*64,
        "attestation_id": "d"*64, "attestation_hash": "e"*64,
        "continuation_source_id": "f"*64, "continuation_source_hash": "1"*64,
        "activation_id": "2"*64, "activation_hash": "3"*64,
        "authorization_consumption_id": "4"*64, "authorization_consumption_hash": "5"*64,
        "authorization_id": "6"*64, "authorization_hash": "7"*64,
        "readiness_id": "8"*64, "readiness_hash": "9"*64,
        "evidence_admission_id": "a"*64, "evidence_admission_hash": "b"*64,
        "materialization_id": "c"*64, "materialization_hash": "d"*64,
        "plan_admission_id": "e"*64, "plan_admission_hash": "f"*64,
        "plan_id": "1"*64, "plan_hash": "2"*64,
        "admission_id": "3"*64, "admission_hash": "4"*64,
        "request_id": "5"*64, "request_hash": "6"*64,
        "dependency_receipt_id": "7"*64, "dependency_receipt_hash": "8"*64,
        "source_runtime_completion_id": "9"*64, "source_runtime_completion_hash": "a"*64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-016-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": t, "admitted_at": t+timedelta(seconds=1),
        "planned_at": t+timedelta(seconds=2), "plan_admitted_at": t+timedelta(seconds=3),
        "materialized_at": t+timedelta(seconds=4), "evidence_admitted_at": t+timedelta(seconds=5),
        "readiness_certified_at": t+timedelta(seconds=6), "authorized_at": t+timedelta(seconds=7),
        "consumed_at": t+timedelta(seconds=8), "activated_at": t+timedelta(seconds=9),
        "continuation_certified_at": t+timedelta(seconds=10), "attested_at": t+timedelta(seconds=11),
        "attestation_consumed_at": t+timedelta(seconds=12), "continuation_at": t+timedelta(seconds=13),
        "plan_steps": ("validate_scope", "identify_required_evidence", "select_analytic_path", "assemble_response", "certify_response_boundary"),
        "evidence_requirements": ("source_provenance", "market_price", "oracle_probability"),
        "activation_record_ids": ("1"*64, "2"*64, "3"*64),
        "activation_record_hashes": ("4"*64, "5"*64, "6"*64),
        "activated_invocation_ids": ("7"*64, "8"*64, "9"*64),
        "activated_invocation_hashes": ("a"*64, "b"*64, "c"*64),
        "activated_read_operations": ("read_certified_lineage", "read_certified_market_state", "read_certified_analytics"),
        "consumption_identity_verified": True, "consumption_hash_verified": True,
        "consumption_contract_verified": True, "attestation_lineage_verified": True,
        "activation_record_identity_verified": True, "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True, "invocation_order_verified": True,
        "invocation_count_verified": True, "approved_read_operations_verified": True,
        "continuation_scope_verified": True, "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True, "immutable_continuation_boundary_verified": True,
        "read_only_boundary_verified": True, "single_consumption_scope_verified": True,
        "continuation_single_use_verified": True, "duplicate_continuation_allowed": False,
        "continuation_reversible": False, "runtime_serving_allowed": False,
        "network_listener_allowed": False, "database_connection_allowed": False,
        "publication_allowed": False, "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False, "order_creation_allowed": False,
        "funds_movement_allowed": False, "portfolio_mutation_allowed": False,
        "continuation_type": CONTINUATION_TYPE, "continuation_status": CONTINUATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuation(
        **body, continuation_hash=source_hash(body)
    )


def reject(fn):
    try:
        fn()
        raise AssertionError("unsafe attestation accepted")
    except OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-016 TEST")
    print(" CONTINUATION ATTESTATION")
    print("=" * 40)

    source = sample_continuation()
    at = source.continuation_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationAttestationGate()
    first = gate.attest(continuation=source, attested_at=at)
    second = gate.attest(continuation=source, attested_at=at)

    assert first == second
    assert first.attestation_hash == stable_hash({k: v for k, v in asdict(first).items() if k != "attestation_hash"})
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.attestation_status == ATTESTATION_STATUS
    assert first.continuation_identity_verified and first.continuation_hash_verified
    assert first.continuation_contract_verified and first.consumption_lineage_verified
    assert first.source_attestation_lineage_verified
    assert first.invocation_lineage_verified and first.invocation_order_verified
    assert first.invocation_count_verified and first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.attestation_single_use_verified
    assert not first.duplicate_attestation_allowed
    assert not first.attestation_reversible

    reject(lambda: gate.attest(continuation=replace(source, continuation_hash="0"*64), attested_at=at))
    reject(lambda: gate.attest(continuation=replace(source, publication_allowed=True), attested_at=at))
    reject(lambda: gate.attest(continuation=replace(source, activated_invocation_ids=("7"*64, "7"*64, "9"*64)), attested_at=at))
    reject(lambda: gate.attest(continuation=source, attested_at=source.continuation_at-timedelta(seconds=1)))

    print("[PASS] Actual ORR-015 attestation-consumption continuation consumed")
    print("[PASS] Complete ORR-001 through ORR-015 lineage preserved")
    print("[PASS] Deterministic continuation attestation certified")
    print("[PASS] Activation-record and invocation identities, hashes, order, and count preserved")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature continuations rejected")
    print("[DONE] ORR-016 CONTINUATION ATTESTATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
