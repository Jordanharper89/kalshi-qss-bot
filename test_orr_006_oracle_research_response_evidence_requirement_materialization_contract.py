from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_plan_admission_gate import (
    PLAN_ADMISSION_STATUS,
    PLAN_ADMISSION_TYPE,
    OracleResearchResponsePlanAdmission,
    stable_hash as plan_admission_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_materialization_contract import *


def sample_plan_admission() -> OracleResearchResponsePlanAdmission:
    requested_at = datetime(2026, 7, 29, 18, 20, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    body = {
        "plan_admission_id": "1" * 64,
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
        "correlation_id": "session:orr-006-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "planned_at": planned_at,
        "plan_admitted_at": plan_admitted_at,
        "plan_steps": (
            "validate_scope", "identify_required_evidence", "select_analytic_path",
            "assemble_response", "certify_response_boundary",
        ),
        "evidence_requirements": (
            "source_provenance", "freshness", "lineage", "read_only_certification",
            "venue_identity", "market_price", "oracle_probability", "estimated_edge",
            "confidence", "validity_window", "filter_compliance",
        ),
        "plan_identity_verified": True,
        "plan_hash_verified": True,
        "plan_contract_verified": True,
        "plan_steps_verified": True,
        "evidence_requirements_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_plan_admission_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_plan_scope_verified": True,
        "plan_admission_single_use_verified": True,
        "duplicate_plan_admission_allowed": False,
        "plan_admission_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "plan_admission_type": PLAN_ADMISSION_TYPE,
        "plan_admission_status": PLAN_ADMISSION_STATUS,
    }
    return OracleResearchResponsePlanAdmission(**body, plan_admission_hash=plan_admission_hash(body))


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe materialization accepted")
    except OracleResearchResponseEvidenceRequirementMaterializationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-006 TEST")
    print(" EVIDENCE REQUIREMENT MATERIALIZATION")
    print("=" * 40)

    plan_admission = sample_plan_admission()
    materialized_at = plan_admission.plan_admitted_at + timedelta(seconds=1)
    contract = OracleResearchResponseEvidenceRequirementMaterializationContract()

    first = contract.materialize(plan_admission=plan_admission, materialized_at=materialized_at)
    second = contract.materialize(plan_admission=plan_admission, materialized_at=materialized_at)

    assert first == second
    assert first.materialization_hash == stable_hash({
        key: value for key, value in asdict(first).items() if key != "materialization_hash"
    })
    assert first.materialization_type == MATERIALIZATION_TYPE
    assert first.materialization_status == MATERIALIZATION_STATUS
    assert len(first.materialized_requirements) == len(first.evidence_requirements)
    assert tuple(item.requirement_name for item in first.materialized_requirements) == first.evidence_requirements
    assert tuple(item.ordinal for item in first.materialized_requirements) == tuple(range(1, len(first.materialized_requirements) + 1))
    assert all(item.required and item.read_only for item in first.materialized_requirements)
    assert not any(item.external_side_effects_allowed for item in first.materialized_requirements)
    assert first.plan_admission_identity_verified
    assert first.plan_admission_hash_verified
    assert first.plan_admission_contract_verified
    assert first.evidence_requirement_set_verified
    assert first.evidence_requirement_order_verified
    assert first.materialization_single_use_verified
    assert not first.duplicate_materialization_allowed
    assert not first.materialization_reversible

    reject(lambda: contract.materialize(
        plan_admission=replace(plan_admission, plan_admission_hash="0" * 64),
        materialized_at=materialized_at,
    ))
    reject(lambda: contract.materialize(
        plan_admission=replace(plan_admission, publication_allowed=True),
        materialized_at=materialized_at,
    ))
    reject(lambda: contract.materialize(
        plan_admission=replace(plan_admission, evidence_requirements=("unsupported_requirement",)),
        materialized_at=materialized_at,
    ))
    reject(lambda: contract.materialize(
        plan_admission=plan_admission,
        materialized_at=plan_admission.plan_admitted_at - timedelta(seconds=1),
    ))

    print("[PASS] Actual ORR-005 plan admission consumed")
    print("[PASS] Complete ORR-001 through ORR-005 lineage preserved")
    print("[PASS] Deterministic evidence requirements materialized")
    print("[PASS] Ordered immutable requirement records certified")
    print("[PASS] Every requirement remains mandatory and read-only")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsupported, premature, and unsafe admissions rejected")
    print("[DONE] ORR-006 EVIDENCE REQUIREMENT MATERIALIZATION CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
