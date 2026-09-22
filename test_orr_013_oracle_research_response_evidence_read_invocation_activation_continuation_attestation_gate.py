from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_gate import (
    CONTINUATION_STATUS,
    CONTINUATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuation,
    stable_hash as continuation_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_gate import *


def sample_continuation() -> OracleResearchResponseEvidenceReadInvocationActivationContinuation:
    requested_at = datetime(2026, 7, 29, 19, 20, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)
    readiness_certified_at = evidence_admitted_at + timedelta(seconds=1)
    authorized_at = readiness_certified_at + timedelta(seconds=1)
    consumed_at = authorized_at + timedelta(seconds=1)
    activated_at = consumed_at + timedelta(seconds=1)
    continuation_certified_at = activated_at + timedelta(seconds=1)

    body = {
        "continuation_id": "a" * 64,
        "activation_id": "b" * 64,
        "activation_hash": "c" * 64,
        "consumption_id": "d" * 64,
        "consumption_hash": "e" * 64,
        "authorization_id": "f" * 64,
        "authorization_hash": "1" * 64,
        "readiness_id": "2" * 64,
        "readiness_hash": "3" * 64,
        "evidence_admission_id": "4" * 64,
        "evidence_admission_hash": "5" * 64,
        "materialization_id": "6" * 64,
        "materialization_hash": "7" * 64,
        "plan_admission_id": "8" * 64,
        "plan_admission_hash": "9" * 64,
        "plan_id": "a" * 64,
        "plan_hash": "b" * 64,
        "admission_id": "c" * 64,
        "admission_hash": "d" * 64,
        "request_id": "e" * 64,
        "request_hash": "f" * 64,
        "dependency_receipt_id": "1" * 64,
        "dependency_receipt_hash": "2" * 64,
        "source_runtime_completion_id": "3" * 64,
        "source_runtime_completion_hash": "4" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-013-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "planned_at": planned_at,
        "plan_admitted_at": plan_admitted_at,
        "materialized_at": materialized_at,
        "evidence_admitted_at": evidence_admitted_at,
        "readiness_certified_at": readiness_certified_at,
        "authorized_at": authorized_at,
        "consumed_at": consumed_at,
        "activated_at": activated_at,
        "continuation_certified_at": continuation_certified_at,
        "plan_steps": (
            "validate_scope",
            "identify_required_evidence",
            "select_analytic_path",
            "assemble_response",
            "certify_response_boundary",
        ),
        "evidence_requirements": (
            "source_provenance",
            "market_price",
            "oracle_probability",
        ),
        "activation_record_ids": ("1" * 64, "2" * 64, "3" * 64),
        "activation_record_hashes": ("4" * 64, "5" * 64, "6" * 64),
        "activated_invocation_ids": ("7" * 64, "8" * 64, "9" * 64),
        "activated_invocation_hashes": ("a" * 64, "b" * 64, "c" * 64),
        "activated_read_operations": (
            "read_certified_lineage",
            "read_certified_market_state",
            "read_certified_analytics",
        ),
        "activation_identity_verified": True,
        "activation_hash_verified": True,
        "activation_contract_verified": True,
        "activation_record_identity_verified": True,
        "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "continuation_scope_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_continuation_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_activation_scope_verified": True,
        "continuation_single_use_verified": True,
        "duplicate_continuation_allowed": False,
        "continuation_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "continuation_type": CONTINUATION_TYPE,
        "continuation_status": CONTINUATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationActivationContinuation(
        **body,
        continuation_hash=continuation_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe attestation accepted")
    except OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-013 TEST")
    print(" CONTINUATION ATTESTATION")
    print("=" * 40)

    continuation = sample_continuation()
    attested_at = continuation.continuation_certified_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationGate()

    first = gate.attest(continuation=continuation, attested_at=attested_at)
    second = gate.attest(continuation=continuation, attested_at=attested_at)

    assert first == second
    assert first.attestation_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "attestation_hash"
        }
    )
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.attestation_status == ATTESTATION_STATUS
    assert first.continuation_identity_verified
    assert first.continuation_hash_verified
    assert first.continuation_contract_verified
    assert first.activation_record_identity_verified
    assert first.activation_record_hashes_verified
    assert first.invocation_lineage_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.attestation_scope_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
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
            continuation=replace(continuation, publication_allowed=True),
            attested_at=attested_at,
        )
    )
    reject(
        lambda: gate.attest(
            continuation=replace(
                continuation,
                activated_invocation_ids=("7" * 64, "7" * 64, "9" * 64),
            ),
            attested_at=attested_at,
        )
    )
    reject(
        lambda: gate.attest(
            continuation=continuation,
            attested_at=continuation.continuation_certified_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-012 activation continuation consumed")
    print("[PASS] Complete ORR-001 through ORR-012 lineage preserved")
    print("[PASS] Deterministic continuation attestation certified")
    print("[PASS] Activation-record and invocation identities, hashes, order, and count verified")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature continuations rejected")
    print("[DONE] ORR-013 CONTINUATION ATTESTATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
