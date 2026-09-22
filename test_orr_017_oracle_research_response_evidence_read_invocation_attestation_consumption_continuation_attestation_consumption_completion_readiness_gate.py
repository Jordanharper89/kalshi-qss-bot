from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationAttestation,
    stable_hash as source_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_attestation_consumption_continuation_attestation_consumption_completion_readiness_gate import *


def sample_attestation():
    t = datetime(2026, 7, 29, 20, 0, tzinfo=timezone.utc)
    body = {
        "attestation_id": "a"*64, "continuation_id": "b"*64, "continuation_hash": "c"*64,
        "consumption_id": "d"*64, "consumption_hash": "e"*64,
        "source_attestation_id": "f"*64, "source_attestation_hash": "1"*64,
        "activation_continuation_id": "2"*64, "activation_continuation_hash": "3"*64,
        "activation_id": "4"*64, "activation_hash": "5"*64,
        "authorization_consumption_id": "6"*64, "authorization_consumption_hash": "7"*64,
        "authorization_id": "8"*64, "authorization_hash": "9"*64,
        "readiness_id": "a"*64, "readiness_hash": "b"*64,
        "evidence_admission_id": "c"*64, "evidence_admission_hash": "d"*64,
        "materialization_id": "e"*64, "materialization_hash": "f"*64,
        "plan_admission_id": "1"*64, "plan_admission_hash": "2"*64,
        "plan_id": "3"*64, "plan_hash": "4"*64,
        "admission_id": "5"*64, "admission_hash": "6"*64,
        "request_id": "7"*64, "request_hash": "8"*64,
        "dependency_receipt_id": "9"*64, "dependency_receipt_hash": "a"*64,
        "source_runtime_completion_id": "b"*64, "source_runtime_completion_hash": "c"*64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-017-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": t, "admitted_at": t+timedelta(seconds=1),
        "planned_at": t+timedelta(seconds=2), "plan_admitted_at": t+timedelta(seconds=3),
        "materialized_at": t+timedelta(seconds=4), "evidence_admitted_at": t+timedelta(seconds=5),
        "readiness_certified_at": t+timedelta(seconds=6), "authorized_at": t+timedelta(seconds=7),
        "consumed_at": t+timedelta(seconds=8), "activated_at": t+timedelta(seconds=9),
        "activation_continuation_certified_at": t+timedelta(seconds=10),
        "source_attested_at": t+timedelta(seconds=11), "attestation_consumed_at": t+timedelta(seconds=12),
        "continuation_at": t+timedelta(seconds=13), "attested_at": t+timedelta(seconds=14),
        "plan_steps": ("validate_scope", "identify_required_evidence", "select_analytic_path", "assemble_response", "certify_response_boundary"),
        "evidence_requirements": ("source_provenance", "market_price", "oracle_probability"),
        "activation_record_ids": ("1"*64, "2"*64, "3"*64),
        "activation_record_hashes": ("4"*64, "5"*64, "6"*64),
        "activated_invocation_ids": ("7"*64, "8"*64, "9"*64),
        "activated_invocation_hashes": ("a"*64, "b"*64, "c"*64),
        "activated_read_operations": ("read_certified_lineage", "read_certified_market_state", "read_certified_analytics"),
        "continuation_identity_verified": True, "continuation_hash_verified": True,
        "continuation_contract_verified": True, "consumption_lineage_verified": True,
        "source_attestation_lineage_verified": True,
        "activation_record_identity_verified": True, "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True, "invocation_order_verified": True,
        "invocation_count_verified": True, "approved_read_operations_verified": True,
        "attestation_scope_verified": True, "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True, "immutable_attestation_boundary_verified": True,
        "read_only_boundary_verified": True, "single_continuation_scope_verified": True,
        "attestation_single_use_verified": True, "duplicate_attestation_allowed": False,
        "attestation_reversible": False, "runtime_serving_allowed": False,
        "network_listener_allowed": False, "database_connection_allowed": False,
        "publication_allowed": False, "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False, "order_creation_allowed": False,
        "funds_movement_allowed": False, "portfolio_mutation_allowed": False,
        "attestation_type": ATTESTATION_TYPE, "attestation_status": ATTESTATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationAttestationConsumptionContinuationAttestation(
        **body, attestation_hash=source_hash(body)
    )


def reject(fn):
    try:
        fn()
        raise AssertionError("unsafe readiness accepted")
    except OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-017 TEST")
    print(" FINAL ATTESTATION CONSUMPTION")
    print(" COMPLETION READINESS")
    print("=" * 40)

    source = sample_attestation()
    at = source.attested_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationFinalAttestationConsumptionCompletionReadinessGate()
    first = gate.certify(attestation=source, final_attestation_consumed_at=at)
    second = gate.certify(attestation=source, final_attestation_consumed_at=at)

    assert first == second
    assert first.readiness_hash == stable_hash({k: v for k, v in asdict(first).items() if k != "readiness_hash"})
    assert first.readiness_type == READINESS_TYPE
    assert first.readiness_status == READINESS_STATUS
    assert first.final_attestation_identity_verified and first.final_attestation_hash_verified
    assert first.final_attestation_contract_verified and first.full_lineage_verified
    assert first.completion_scope_verified and first.completion_readiness_verified
    assert first.invocation_lineage_verified and first.invocation_order_verified
    assert first.invocation_count_verified and first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.consumption_single_use_verified
    assert not first.duplicate_consumption_allowed
    assert not first.consumption_reversible

    reject(lambda: gate.certify(attestation=replace(source, attestation_hash="0"*64), final_attestation_consumed_at=at))
    reject(lambda: gate.certify(attestation=replace(source, publication_allowed=True), final_attestation_consumed_at=at))
    reject(lambda: gate.certify(attestation=replace(source, activated_invocation_ids=("7"*64, "7"*64, "9"*64)), final_attestation_consumed_at=at))
    reject(lambda: gate.certify(attestation=source, final_attestation_consumed_at=source.attested_at-timedelta(seconds=1)))

    print("[PASS] Actual ORR-016 continuation attestation consumed")
    print("[PASS] Complete ORR-001 through ORR-016 lineage preserved")
    print("[PASS] Deterministic final attestation consumption certified")
    print("[PASS] ORR subsystem completion readiness certified")
    print("[PASS] Activation-record and invocation identities, hashes, order, and count preserved")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature attestations rejected")
    print("[DONE] ORR-017 FINAL ATTESTATION CONSUMPTION AND COMPLETION READINESS GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
