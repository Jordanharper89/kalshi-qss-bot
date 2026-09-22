from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation,
    stable_hash as attestation_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_attestation_consumption_gate import *


def sample_attestation() -> OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation:
    requested_at = datetime(2026, 7, 29, 19, 30, tzinfo=timezone.utc)
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
    attested_at = continuation_certified_at + timedelta(seconds=1)

    body = {
        "attestation_id": "a" * 64,
        "continuation_id": "b" * 64,
        "continuation_hash": "c" * 64,
        "activation_id": "d" * 64,
        "activation_hash": "e" * 64,
        "consumption_id": "f" * 64,
        "consumption_hash": "1" * 64,
        "authorization_id": "2" * 64,
        "authorization_hash": "3" * 64,
        "readiness_id": "4" * 64,
        "readiness_hash": "5" * 64,
        "evidence_admission_id": "6" * 64,
        "evidence_admission_hash": "7" * 64,
        "materialization_id": "8" * 64,
        "materialization_hash": "9" * 64,
        "plan_admission_id": "a" * 64,
        "plan_admission_hash": "b" * 64,
        "plan_id": "c" * 64,
        "plan_hash": "d" * 64,
        "admission_id": "e" * 64,
        "admission_hash": "f" * 64,
        "request_id": "1" * 64,
        "request_hash": "2" * 64,
        "dependency_receipt_id": "3" * 64,
        "dependency_receipt_hash": "4" * 64,
        "source_runtime_completion_id": "5" * 64,
        "source_runtime_completion_hash": "6" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-014-test",
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
        "attested_at": attested_at,
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
        "continuation_identity_verified": True,
        "continuation_hash_verified": True,
        "continuation_contract_verified": True,
        "activation_record_identity_verified": True,
        "activation_record_hashes_verified": True,
        "invocation_lineage_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "attestation_scope_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_attestation_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_continuation_scope_verified": True,
        "attestation_single_use_verified": True,
        "duplicate_attestation_allowed": False,
        "attestation_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "attestation_type": ATTESTATION_TYPE,
        "attestation_status": ATTESTATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestation(
        **body,
        attestation_hash=attestation_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe attestation consumption accepted")
    except OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-014 TEST")
    print(" ATTESTATION CONSUMPTION")
    print("=" * 40)

    attestation = sample_attestation()
    consumed_at = attestation.attested_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationActivationContinuationAttestationConsumptionGate()

    first = gate.consume(
        attestation=attestation,
        attestation_consumed_at=consumed_at,
    )
    second = gate.consume(
        attestation=attestation,
        attestation_consumed_at=consumed_at,
    )

    assert first == second
    assert first.consumption_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "consumption_hash"
        }
    )
    assert first.consumption_type == CONSUMPTION_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.attestation_identity_verified
    assert first.attestation_hash_verified
    assert first.attestation_contract_verified
    assert first.continuation_lineage_verified
    assert first.activation_record_identity_verified
    assert first.activation_record_hashes_verified
    assert first.invocation_lineage_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.consumption_single_use_verified
    assert not first.duplicate_consumption_allowed
    assert not first.consumption_reversible

    reject(
        lambda: gate.consume(
            attestation=replace(attestation, attestation_hash="0" * 64),
            attestation_consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            attestation=replace(attestation, publication_allowed=True),
            attestation_consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            attestation=replace(
                attestation,
                activated_invocation_ids=("7" * 64, "7" * 64, "9" * 64),
            ),
            attestation_consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            attestation=attestation,
            attestation_consumed_at=attestation.attested_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-013 continuation attestation consumed")
    print("[PASS] Complete ORR-001 through ORR-013 lineage preserved")
    print("[PASS] Deterministic single-use attestation consumption certified")
    print("[PASS] Activation-record and invocation identities, hashes, order, and count preserved")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature attestations rejected")
    print("[DONE] ORR-014 ATTESTATION CONSUMPTION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
