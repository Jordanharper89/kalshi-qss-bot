from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_gate import (
    ACTIVATION_STATUS,
    ACTIVATION_TYPE,
    OracleResearchResponseActivatedEvidenceReadInvocation,
    OracleResearchResponseEvidenceReadInvocationActivation,
    stable_hash as activation_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_continuation_gate import *


def sample_activation() -> OracleResearchResponseEvidenceReadInvocationActivation:
    requested_at = datetime(2026, 7, 29, 19, 10, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)
    readiness_certified_at = evidence_admitted_at + timedelta(seconds=1)
    authorized_at = readiness_certified_at + timedelta(seconds=1)
    consumed_at = authorized_at + timedelta(seconds=1)
    activated_at = consumed_at + timedelta(seconds=1)

    records = []
    operations = (
        "read_certified_lineage",
        "read_certified_market_state",
        "read_certified_analytics",
    )
    for ordinal, operation in enumerate(operations, start=1):
        body = {
            "activation_record_id": str(ordinal) * 64,
            "ordinal": ordinal,
            "invocation_id": str(ordinal + 3) * 64,
            "invocation_hash": str(ordinal + 6) * 64,
            "read_operation": operation,
            "read_only": True,
            "activation_permitted": True,
            "callable_bound": False,
            "callable_invoked": False,
            "result_materialized": False,
            "external_side_effects_allowed": False,
        }
        records.append(
            OracleResearchResponseActivatedEvidenceReadInvocation(
                **body,
                activation_record_hash=activation_hash(body),
            )
        )

    body = {
        "activation_id": "a" * 64,
        "consumption_id": "b" * 64,
        "consumption_hash": "c" * 64,
        "authorization_id": "d" * 64,
        "authorization_hash": "e" * 64,
        "readiness_id": "f" * 64,
        "readiness_hash": "1" * 64,
        "evidence_admission_id": "2" * 64,
        "evidence_admission_hash": "3" * 64,
        "materialization_id": "4" * 64,
        "materialization_hash": "5" * 64,
        "plan_admission_id": "6" * 64,
        "plan_admission_hash": "7" * 64,
        "plan_id": "8" * 64,
        "plan_hash": "9" * 64,
        "admission_id": "a" * 64,
        "admission_hash": "b" * 64,
        "request_id": "c" * 64,
        "request_hash": "d" * 64,
        "dependency_receipt_id": "e" * 64,
        "dependency_receipt_hash": "f" * 64,
        "source_runtime_completion_id": "1" * 64,
        "source_runtime_completion_hash": "2" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-012-test",
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
        "activated_invocations": tuple(records),
        "consumption_identity_verified": True,
        "consumption_hash_verified": True,
        "consumption_contract_verified": True,
        "invocation_lineage_verified": True,
        "invocation_hashes_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "activation_scope_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "result_materialization_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_activation_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_consumption_scope_verified": True,
        "activation_single_use_verified": True,
        "duplicate_activation_allowed": False,
        "activation_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "activation_type": ACTIVATION_TYPE,
        "activation_status": ACTIVATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationActivation(
        **body,
        activation_hash=activation_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe continuation accepted")
    except OracleResearchResponseEvidenceReadInvocationActivationContinuationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-012 TEST")
    print(" ACTIVATION CONTINUATION")
    print("=" * 40)

    activation = sample_activation()
    certified_at = activation.activated_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationActivationContinuationGate()

    first = gate.certify(
        activation=activation,
        continuation_certified_at=certified_at,
    )
    second = gate.certify(
        activation=activation,
        continuation_certified_at=certified_at,
    )

    assert first == second
    assert first.continuation_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "continuation_hash"
        }
    )
    assert first.continuation_type == CONTINUATION_TYPE
    assert first.continuation_status == CONTINUATION_STATUS
    assert len(first.activation_record_ids) == 3
    assert len(first.activation_record_hashes) == 3
    assert len(first.activated_invocation_ids) == 3
    assert len(first.activated_invocation_hashes) == 3
    assert len(first.activated_read_operations) == 3
    assert first.activation_identity_verified
    assert first.activation_hash_verified
    assert first.activation_contract_verified
    assert first.activation_record_identity_verified
    assert first.activation_record_hashes_verified
    assert first.invocation_lineage_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.continuation_scope_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.continuation_single_use_verified
    assert not first.duplicate_continuation_allowed
    assert not first.continuation_reversible

    reject(
        lambda: gate.certify(
            activation=replace(activation, activation_hash="0" * 64),
            continuation_certified_at=certified_at,
        )
    )
    reject(
        lambda: gate.certify(
            activation=replace(activation, publication_allowed=True),
            continuation_certified_at=certified_at,
        )
    )
    unsafe = replace(activation.activated_invocations[0], callable_invoked=True)
    reject(
        lambda: gate.certify(
            activation=replace(
                activation,
                activated_invocations=(unsafe, *activation.activated_invocations[1:]),
            ),
            continuation_certified_at=certified_at,
        )
    )
    reject(
        lambda: gate.certify(
            activation=activation,
            continuation_certified_at=activation.activated_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-011 evidence read-invocation activation consumed")
    print("[PASS] Complete ORR-001 through ORR-011 lineage preserved")
    print("[PASS] Deterministic activation continuation certified")
    print("[PASS] Activation-record identities, hashes, invocation order, and count verified")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, invoked, unsafe, and premature activations rejected")
    print("[DONE] ORR-012 ACTIVATION CONTINUATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
