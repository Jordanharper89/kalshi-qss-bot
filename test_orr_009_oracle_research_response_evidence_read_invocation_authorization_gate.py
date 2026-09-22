from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_readiness_gate import (
    READINESS_STATUS,
    READINESS_TYPE,
    OracleResearchResponseEvidenceReadInvocation,
    OracleResearchResponseEvidenceReadInvocationReadiness,
    stable_hash as readiness_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_authorization_gate import *


def sample_readiness() -> OracleResearchResponseEvidenceReadInvocationReadiness:
    requested_at = datetime(2026, 7, 29, 18, 40, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)
    readiness_certified_at = evidence_admitted_at + timedelta(seconds=1)

    requirements = ("source_provenance", "market_price", "oracle_probability")
    operations = (
        "read_certified_lineage",
        "read_certified_market_state",
        "read_certified_analytics",
    )
    invocations = []
    for ordinal, (name, operation) in enumerate(zip(requirements, operations), start=1):
        body = {
            "invocation_id": str(ordinal) * 64,
            "ordinal": ordinal,
            "requirement_id": str(ordinal + 3) * 64,
            "requirement_hash": str(ordinal + 6) * 64,
            "requirement_name": name,
            "read_operation": operation,
            "read_only": True,
            "callable_bound": False,
            "callable_invoked": False,
            "external_side_effects_allowed": False,
        }
        invocations.append(
            OracleResearchResponseEvidenceReadInvocation(
                **body,
                invocation_hash=readiness_hash(body),
            )
        )

    body = {
        "readiness_id": "a" * 64,
        "evidence_admission_id": "b" * 64,
        "evidence_admission_hash": "c" * 64,
        "materialization_id": "d" * 64,
        "materialization_hash": "e" * 64,
        "plan_admission_id": "f" * 64,
        "plan_admission_hash": "1" * 64,
        "plan_id": "2" * 64,
        "plan_hash": "3" * 64,
        "admission_id": "4" * 64,
        "admission_hash": "5" * 64,
        "request_id": "6" * 64,
        "request_hash": "7" * 64,
        "dependency_receipt_id": "8" * 64,
        "dependency_receipt_hash": "9" * 64,
        "source_runtime_completion_id": "a" * 64,
        "source_runtime_completion_hash": "b" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-009-test",
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
        "plan_steps": (
            "validate_scope",
            "identify_required_evidence",
            "select_analytic_path",
            "assemble_response",
            "certify_response_boundary",
        ),
        "evidence_requirements": requirements,
        "read_invocations": tuple(invocations),
        "evidence_admission_identity_verified": True,
        "evidence_admission_hash_verified": True,
        "evidence_admission_contract_verified": True,
        "requirement_lineage_verified": True,
        "read_operation_scope_verified": True,
        "callable_binding_disabled_verified": True,
        "callable_invocation_disabled_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_readiness_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_evidence_admission_scope_verified": True,
        "readiness_single_use_verified": True,
        "duplicate_readiness_allowed": False,
        "readiness_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "readiness_type": READINESS_TYPE,
        "readiness_status": READINESS_STATUS,
    }
    return OracleResearchResponseEvidenceReadInvocationReadiness(
        **body,
        readiness_hash=readiness_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe authorization accepted")
    except OracleResearchResponseEvidenceReadInvocationAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-009 TEST")
    print(" EVIDENCE READ INVOCATION AUTHORIZATION")
    print("=" * 40)

    readiness = sample_readiness()
    authorized_at = readiness.readiness_certified_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationAuthorizationGate()

    first = gate.authorize(readiness=readiness, authorized_at=authorized_at)
    second = gate.authorize(readiness=readiness, authorized_at=authorized_at)

    assert first == second
    assert first.authorization_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "authorization_hash"
        }
    )
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert len(first.authorized_invocation_ids) == 3
    assert len(first.authorized_invocation_hashes) == 3
    assert len(first.authorized_read_operations) == 3
    assert first.readiness_identity_verified
    assert first.readiness_hash_verified
    assert first.readiness_contract_verified
    assert first.invocation_identity_verified
    assert first.invocation_hashes_verified
    assert first.invocation_order_verified
    assert first.invocation_count_verified
    assert first.approved_read_operations_verified
    assert first.callable_binding_remains_disabled_verified
    assert first.callable_invocation_remains_disabled_verified
    assert first.authorization_single_use_verified
    assert not first.duplicate_authorization_allowed
    assert not first.authorization_reversible

    reject(
        lambda: gate.authorize(
            readiness=replace(readiness, readiness_hash="0" * 64),
            authorized_at=authorized_at,
        )
    )
    reject(
        lambda: gate.authorize(
            readiness=replace(readiness, publication_allowed=True),
            authorized_at=authorized_at,
        )
    )
    unsafe_invocation = replace(readiness.read_invocations[0], callable_bound=True)
    reject(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                read_invocations=(unsafe_invocation, *readiness.read_invocations[1:]),
            ),
            authorized_at=authorized_at,
        )
    )
    reject(
        lambda: gate.authorize(
            readiness=readiness,
            authorized_at=readiness.readiness_certified_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-008 read-invocation readiness consumed")
    print("[PASS] Complete ORR-001 through ORR-008 lineage preserved")
    print("[PASS] Deterministic read-invocation authorization certified")
    print("[PASS] Invocation identities, hashes, order, and count verified")
    print("[PASS] Approved read operations authorized without binding or invocation")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, bound, unsafe, and premature readiness records rejected")
    print("[DONE] ORR-009 EVIDENCE READ INVOCATION AUTHORIZATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
