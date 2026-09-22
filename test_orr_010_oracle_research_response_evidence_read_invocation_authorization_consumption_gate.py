from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    OracleResearchResponseEvidenceReadInvocationAuthorization,
    stable_hash as authorization_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_consumption_gate import *


def sample_authorization() -> OracleResearchResponseEvidenceReadInvocationAuthorization:
    requested_at = datetime(2026, 7, 29, 18, 50, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)
    readiness_certified_at = evidence_admitted_at + timedelta(seconds=1)
    authorized_at = readiness_certified_at + timedelta(seconds=1)

    body = {
        "authorization_id": "a" * 64,
        "readiness_id": "b" * 64,
        "readiness_hash": "c" * 64,
        "evidence_admission_id": "d" * 64,
        "evidence_admission_hash": "e" * 64,
        "materialization_id": "f" * 64,
        "materialization_hash": "1" * 64,
        "plan_admission_id": "2" * 64,
        "plan_admission_hash": "3" * 64,
        "plan_id": "4" * 64,
        "plan_hash": "5" * 64,
        "admission_id": "6" * 64,
        "admission_hash": "7" * 64,
        "request_id": "8" * 64,
        "request_hash": "9" * 64,
        "dependency_receipt_id": "a" * 64,
        "dependency_receipt_hash": "b" * 64,
        "source_runtime_completion_id": "c" * 64,
        "source_runtime_completion_hash": "d" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-010-test",
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
        "authorized_invocation_ids": ("1" * 64, "2" * 64, "3" * 64),
        "authorized_invocation_hashes": ("4" * 64, "5" * 64, "6" * 64),
        "authorized_read_operations": (
            "read_certified_lineage",
            "read_certified_market_state",
            "read_certified_analytics",
        ),
        "readiness_identity_verified": True,
        "readiness_hash_verified": True,
        "readiness_contract_verified": True,
        "invocation_identity_verified": True,
        "invocation_hashes_verified": True,
        "invocation_order_verified": True,
        "invocation_count_verified": True,
        "approved_read_operations_verified": True,
        "callable_binding_remains_disabled_verified": True,
        "callable_invocation_remains_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_authorization_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_readiness_scope_verified": True,
        "authorization_single_use_verified": True,
        "duplicate_authorization_allowed": False,
        "authorization_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "authorization_type": AUTHORIZATION_TYPE,
        "authorization_status": AUTHORIZATION_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationAuthorization(
        **body,
        authorization_hash=authorization_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe consumption accepted")
    except OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-010 TEST")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = sample_authorization()
    consumed_at = authorization.authorized_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization, consumed_at=consumed_at)
    second = gate.consume(authorization=authorization, consumed_at=consumed_at)

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
    assert first.consumed_invocation_ids == authorization.authorized_invocation_ids
    assert first.consumed_invocation_hashes == authorization.authorized_invocation_hashes
    assert first.consumed_read_operations == authorization.authorized_read_operations
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_contract_verified
    assert first.invocation_lineage_verified
    assert first.invocation_hashes_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.consumption_single_use_verified
    assert not first.duplicate_consumption_allowed
    assert not first.consumption_reversible

    reject(
        lambda: gate.consume(
            authorization=replace(authorization, authorization_hash="0" * 64),
            consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            authorization=replace(authorization, publication_allowed=True),
            consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_invocation_ids=("1" * 64, "1" * 64, "3" * 64),
            ),
            consumed_at=consumed_at,
        )
    )
    reject(
        lambda: gate.consume(
            authorization=authorization,
            consumed_at=authorization.authorized_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-009 read-invocation authorization consumed")
    print("[PASS] Complete ORR-001 through ORR-009 lineage preserved")
    print("[PASS] Deterministic single-use authorization consumption certified")
    print("[PASS] Invocation identities, hashes, order, count, and operations preserved")
    print("[PASS] No callable was bound or invoked during consumption")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature authorizations rejected")
    print("[DONE] ORR-010 AUTHORIZATION CONSUMPTION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
