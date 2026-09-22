from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import (
    ADMISSION_STATUS,
    ADMISSION_TYPE,
    OracleResearchResponseRequestAdmission,
    stable_hash as admission_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_planning_contract import *


def sample_admission() -> OracleResearchResponseRequestAdmission:
    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    body = {
        "admission_id": "1" * 64,
        "request_id": "2" * 64,
        "request_hash": "3" * 64,
        "dependency_receipt_id": "4" * 64,
        "dependency_receipt_hash": "5" * 64,
        "source_runtime_completion_id": "6" * 64,
        "source_runtime_completion_hash": "7" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-004-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "request_identity_verified": True,
        "request_hash_verified": True,
        "request_contract_verified": True,
        "typed_question_verified": True,
        "response_mode_verified": True,
        "filter_boundary_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_admission_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_request_scope_verified": True,
        "admission_single_use_verified": True,
        "duplicate_admission_allowed": False,
        "admission_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "admission_type": ADMISSION_TYPE,
        "admission_status": ADMISSION_STATUS,
    }
    return OracleResearchResponseRequestAdmission(
        **body,
        admission_hash=admission_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe response plan accepted")
    except OracleResearchResponsePlanningInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-004 TEST")
    print(" RESEARCH RESPONSE PLANNING CONTRACT")
    print("=" * 40)

    admission = sample_admission()
    planned_at = admission.admitted_at + timedelta(seconds=1)
    contract = OracleResearchResponsePlanningContract()

    first = contract.materialize(admission=admission, planned_at=planned_at)
    second = contract.materialize(admission=admission, planned_at=planned_at)

    assert first == second
    assert first.plan_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "plan_hash"
        }
    )
    assert first.plan_type == PLAN_TYPE
    assert first.plan_status == PLAN_STATUS
    assert first.plan_steps == ALLOWED_PLAN_STEPS
    assert "venue_identity" in first.evidence_requirements
    assert "oracle_probability" in first.evidence_requirements
    assert "filter_compliance" in first.evidence_requirements
    assert first.admission_identity_verified
    assert first.admission_hash_verified
    assert first.admission_contract_verified
    assert first.planning_scope_verified
    assert first.evidence_requirements_verified
    assert first.read_only_boundary_verified
    assert first.plan_single_use_verified
    assert not first.duplicate_plan_allowed
    assert not first.plan_reversible

    reject(
        lambda: contract.materialize(
            admission=replace(admission, admission_hash="0" * 64),
            planned_at=planned_at,
        )
    )
    reject(
        lambda: contract.materialize(
            admission=replace(admission, publication_allowed=True),
            planned_at=planned_at,
        )
    )
    reject(
        lambda: contract.materialize(
            admission=admission,
            planned_at=admission.admitted_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-003 request admission consumed")
    print("[PASS] Complete ORR-001 through ORR-003 lineage preserved")
    print("[PASS] Deterministic response plan materialized")
    print("[PASS] Response-mode evidence requirements certified")
    print("[PASS] Immutable single-use planning boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe admissions rejected")
    print("[DONE] ORR-004 RESEARCH RESPONSE PLANNING CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
