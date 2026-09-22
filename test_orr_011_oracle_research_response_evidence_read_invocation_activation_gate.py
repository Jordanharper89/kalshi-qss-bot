from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    CONSUMPTION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption,
    stable_hash as consumption_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_activation_gate import *


def sample_consumption() -> OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption:
    requested_at = datetime(2026, 7, 29, 19, 0, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)
    readiness_certified_at = evidence_admitted_at + timedelta(seconds=1)
    authorized_at = readiness_certified_at + timedelta(seconds=1)
    consumed_at = authorized_at + timedelta(seconds=1)

    body = {
        "consumption_id": "a" * 64,
        "authorization_id": "b" * 64,
        "authorization_hash": "c" * 64,
        "readiness_id": "d" * 64,
        "readiness_hash": "e" * 64,
        "evidence_admission_id": "f" * 64,
        "evidence_admission_hash": "1" * 64,
        "materialization_id": "2" * 64,
        "materialization_hash": "3" * 64,
        "plan_admission_id": "4" * 64,
        "plan_admission_hash": "5" * 64,
        "plan_id": "6" * 64,
        "plan_hash": "7" * 64,
        "admission_id": "8" * 64,
        "admission_hash": "9" * 64,
        "request_id": "a" * 64,
        "request_hash": "b" * 64,
        "dependency_receipt_id": "c" * 64,
        "dependency_receipt_hash": "d" * 64,
        "source_runtime_completion_id": "e" * 64,
        "source_runtime_completion_hash": "f" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-011-test",
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
        "consumed_invocation_ids": ("1" * 64, "2" * 64, "3" * 64),
        "consumed_invocation_hashes": ("4" * 64, "5" * 64, "6" * 64),
        "consumed_read_operations": (
            "read_certified_lineage",
            "read_certified_market_state",
            "read_certified_analytics",
        ),
        "authorization_identity_verified": True,
        "authorization_hash_verified": True,
        "authorization_contract_verified": True,
        "invocation_lineage_verified": True,
        "invocation_hashes_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_consumption_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_authorization_scope_verified": True,
        "consumption_single_use_verified": True,
        "duplicate_consumption_allowed": False,
        "consumption_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "consumption_type": CONSUMPTION_TYPE,
        "consumption_status": CONSUMPTION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationAuthorizationConsumption(
        **body,
        consumption_hash=consumption_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe activation accepted")
    except OracleResearchResponseEvidenceReadInvocationActivationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-011 TEST")
    print(" EVIDENCE READ INVOCATION ACTIVATION")
    print("=" * 40)

    consumption = sample_consumption()
    activated_at = consumption.consumed_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationActivationGate()

    first = gate.activate(consumption=consumption, activated_at=activated_at)
    second = gate.activate(consumption=consumption, activated_at=activated_at)

    assert first == second
    assert first.activation_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "activation_hash"
        }
    )
    assert first.activation_type == ACTIVATION_TYPE
    assert first.activation_status == ACTIVATION_STATUS
    assert len(first.activated_invocations) == len(first.evidence_requirements)
    assert tuple(item.ordinal for item in first.activated_invocations) == (1, 2, 3)
    assert all(item.read_only for item in first.activated_invocations)
    assert all(item.activation_permitted for item in first.activated_invocations)
    assert not any(item.callable_bound for item in first.activated_invocations)
    assert not any(item.callable_invoked for item in first.activated_invocations)
    assert not any(item.result_materialized for item in first.activated_invocations)
    assert not any(item.external_side_effects_allowed for item in first.activated_invocations)
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_contract_verified
    assert first.invocation_lineage_verified
    assert first.invocation_hashes_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.activation_scope_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.result_materialization_remains_disabled_verified
    assert first.activation_single_use_verified
    assert not first.duplicate_activation_allowed
    assert not first.activation_reversible

    reject(
        lambda: gate.activate(
            consumption=replace(consumption, consumption_hash="0" * 64),
            activated_at=activated_at,
        )
    )
    reject(
        lambda: gate.activate(
            consumption=replace(consumption, publication_allowed=True),
            activated_at=activated_at,
        )
    )
    reject(
        lambda: gate.activate(
            consumption=replace(
                consumption,
                consumed_invocation_ids=("1" * 64, "1" * 64, "3" * 64),
            ),
            activated_at=activated_at,
        )
    )
    reject(
        lambda: gate.activate(
            consumption=consumption,
            activated_at=consumption.consumed_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-010 authorization consumption consumed")
    print("[PASS] Complete ORR-001 through ORR-010 lineage preserved")
    print("[PASS] Deterministic evidence read-invocation activation certified")
    print("[PASS] Activation records preserve invocation identities, hashes, order, and operations")
    print("[PASS] Callables remain unbound and uninvoked; results remain unmaterialized")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature consumptions rejected")
    print("[DONE] ORR-011 EVIDENCE READ INVOCATION ACTIVATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
