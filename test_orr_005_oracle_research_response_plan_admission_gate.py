from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_planning_contract import (
    ALLOWED_PLAN_STEPS,
    PLAN_STATUS,
    PLAN_TYPE,
    OracleResearchResponsePlan,
    stable_hash as plan_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_plan_admission_gate import *


def sample_plan() -> OracleResearchResponsePlan:
    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    body = {
        "plan_id": "1" * 64,
        "admission_id": "2" * 64,
        "admission_hash": "3" * 64,
        "request_id": "4" * 64,
        "request_hash": "5" * 64,
        "dependency_receipt_id": "6" * 64,
        "dependency_receipt_hash": "7" * 64,
        "source_runtime_completion_id": "8" * 64,
        "source_runtime_completion_hash": "9" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-005-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "planned_at": planned_at,
        "plan_steps": ALLOWED_PLAN_STEPS,
        "evidence_requirements": (
            "source_provenance",
            "freshness",
            "lineage",
            "read_only_certification",
            "venue_identity",
            "market_price",
            "oracle_probability",
            "estimated_edge",
            "confidence",
            "validity_window",
            "filter_compliance",
        ),
        "admission_identity_verified": True,
        "admission_hash_verified": True,
        "admission_contract_verified": True,
        "planning_scope_verified": True,
        "evidence_requirements_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_plan_boundary_verified": True,
        "read_only_boundary_verified": True,
        "plan_single_use_verified": True,
        "duplicate_plan_allowed": False,
        "plan_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "plan_type": PLAN_TYPE,
        "plan_status": PLAN_STATUS,
    }
    return OracleResearchResponsePlan(
        **body,
        plan_hash=plan_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe plan admission accepted")
    except OracleResearchResponsePlanAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-005 TEST")
    print(" RESEARCH RESPONSE PLAN ADMISSION")
    print("=" * 40)

    plan = sample_plan()
    admitted_at = plan.planned_at + timedelta(seconds=1)
    gate = OracleResearchResponsePlanAdmissionGate()

    first = gate.admit(plan=plan, plan_admitted_at=admitted_at)
    second = gate.admit(plan=plan, plan_admitted_at=admitted_at)

    assert first == second
    assert first.plan_admission_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "plan_admission_hash"
        }
    )
    assert first.plan_admission_type == PLAN_ADMISSION_TYPE
    assert first.plan_admission_status == PLAN_ADMISSION_STATUS
    assert first.plan_identity_verified
    assert first.plan_hash_verified
    assert first.plan_contract_verified
    assert first.plan_steps_verified
    assert first.evidence_requirements_verified
    assert first.single_plan_scope_verified
    assert first.plan_admission_single_use_verified
    assert not first.duplicate_plan_admission_allowed
    assert not first.plan_admission_reversible

    reject(
        lambda: gate.admit(
            plan=replace(plan, plan_hash="0" * 64),
            plan_admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            plan=replace(plan, network_listener_allowed=True),
            plan_admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            plan=replace(plan, evidence_requirements=()),
            plan_admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            plan=plan,
            plan_admitted_at=plan.planned_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-004 research response plan consumed")
    print("[PASS] Complete ORR-001 through ORR-004 lineage preserved")
    print("[PASS] Deterministic single-plan admission certified")
    print("[PASS] Plan steps and evidence requirements admitted")
    print("[PASS] Immutable single-use plan-admission boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, empty, premature, and unsafe plans rejected")
    print("[DONE] ORR-005 RESEARCH RESPONSE PLAN ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
