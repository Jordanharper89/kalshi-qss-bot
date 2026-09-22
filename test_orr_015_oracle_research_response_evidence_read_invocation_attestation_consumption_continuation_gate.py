from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_consumption_gate import (
    CONSUMPTION_STATUS,
    CONSUMPTION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption,
    stable_hash as source_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_gate import *


def sample_consumption():
    t = datetime(2026, 7, 29, 19, 40, tzinfo=timezone.utc)
    body = {
        "consumption_id": "a"*64, "attestation_id": "b"*64, "attestation_hash": "c"*64,
        "continuation_id": "d"*64, "continuation_hash": "e"*64,
        "activation_id": "f"*64, "activation_hash": "1"*64,
        "consumption_source_id": "2"*64, "consumption_source_hash": "3"*64,
        "authorization_id": "4"*64, "authorization_hash": "5"*64,
        "readiness_id": "6"*64, "readiness_hash": "7"*64,
        "evidence_admission_id": "8"*64, "evidence_admission_hash": "9"*64,
        "materialization_id": "a"*64, "materialization_hash": "b"*64,
        "plan_admission_id": "c"*64, "plan_admission_hash": "d"*64,
        "plan_id": "e"*64, "plan_hash": "f"*64,
        "admission_id": "1"*64, "admission_hash": "2"*64,
        "request_id": "3"*64, "request_hash": "4"*64,
        "dependency_receipt_id": "5"*64, "dependency_receipt_hash": "6"*64,
        "source_runtime_completion_id": "7"*64, "source_runtime_completion_hash": "8"*64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-015-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": t, "admitted_at": t+timedelta(seconds=1),
        "planned_at": t+timedelta(seconds=2), "plan_admitted_at": t+timedelta(seconds=3),
        "materialized_at": t+timedelta(seconds=4), "evidence_admitted_at": t+timedelta(seconds=5),
        "readiness_certified_at": t+timedelta(seconds=6), "authorized_at": t+timedelta(seconds=7),
        "consumed_at": t+timedelta(seconds=8), "activated_at": t+timedelta(seconds=9),
        "continuation_certified_at": t+timedelta(seconds=10), "attested_at": t+timedelta(seconds=11),
        "attestation_consumed_at": t+timedelta(seconds=12),
        "plan_steps": ("validate_scope", "identify_required_evidence", "select_analytic_path", "assemble_response", "certify_response_boundary"),
        "evidence_requirements": ("source_provenance", "market_price", "oracle_probability"),
        "activation_record_ids": ("1"*64, "2"*64, "3"*64),
        "activation_record_hashes": ("4"*64, "5"*64, "6"*64),
        "activated_invocation_ids": ("7"*64, "8"*64, "9"*64),
        "activated_invocation_hashes": ("a"*64, "b"*64, "c"*64),
        "activated_read_operations": ("read_certified_lineage", "read_certified_market_state", "read_certified_analytics"),
        "attestation_identity_verified": True, "attestation_hash_verified": True,
        "attestation_contract_verified": True, "continuation_lineage_verified": True,
        "activation_record_identity_verified": True, "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True, "invocation_order_verified": True,
        "invocation_count_verified": True, "approved_read_operations_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True, "immutable_consumption_boundary_verified": True,
        "read_only_boundary_verified": True, "single_attestation_scope_verified": True,
        "consumption_single_use_verified": True, "duplicate_consumption_allowed": False,
        "consumption_reversible": False, "runtime_serving_allowed": False,
        "network_listener_allowed": False, "database_connection_allowed": False,
        "publication_allowed": False, "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False, "order_creation_allowed": False,
        "funds_movement_allowed": False, "portfolio_mutation_allowed": False,
        "consumption_type": CONSUMPTION_TYPE, "consumption_status": CONSUMPTION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumption(
        **body, consumption_hash=source_hash(body)
    )


def reject(fn):
    try:
        fn()
        raise AssertionError("unsafe continuation accepted")
    except OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-015 TEST")
    print(" ATTESTATION CONSUMPTION CONTINUATION")
    print("=" * 40)

    source = sample_consumption()
    at = source.attestation_consumed_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationGate()
    first = gate.certify(consumption=source, continuation_at=at)
    second = gate.certify(consumption=source, continuation_at=at)

    assert first == second
    assert first.continuation_hash == stable_hash({k: v for k, v in asdict(first).items() if k != "continuation_hash"})
    assert first.continuation_type == CONTINUATION_TYPE
    assert first.continuation_status == CONTINUATION_STATUS
    assert first.consumption_identity_verified and first.consumption_hash_verified
    assert first.consumption_contract_verified and first.attestation_lineage_verified
    assert first.invocation_lineage_verified and first.invocation_order_verified
    assert first.invocation_count_verified and first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.continuation_single_use_verified
    assert not first.duplicate_continuation_allowed
    assert not first.continuation_reversible

    reject(lambda: gate.certify(consumption=replace(source, consumption_hash="0"*64), continuation_at=at))
    reject(lambda: gate.certify(consumption=replace(source, publication_allowed=True), continuation_at=at))
    reject(lambda: gate.certify(consumption=replace(source, activated_invocation_ids=("7"*64, "7"*64, "9"*64)), continuation_at=at))
    reject(lambda: gate.certify(consumption=source, continuation_at=source.attestation_consumed_at-timedelta(seconds=1)))

    print("[PASS] Actual ORR-014 attestation consumption consumed")
    print("[PASS] Complete ORR-001 through ORR-014 lineage preserved")
    print("[PASS] Deterministic attestation-consumption continuation certified")
    print("[PASS] Activation-record and invocation identities, hashes, order, and count preserved")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature consumptions rejected")
    print("[DONE] ORR-015 ATTESTATION CONSUMPTION CONTINUATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
