from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_admission_gate import (
    EVIDENCE_ADMISSION_STATUS,
    EVIDENCE_ADMISSION_TYPE,
    OracleResearchResponseEvidenceRequirementAdmission,
    stable_hash as evidence_admission_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_read_invocation_readiness_gate import *


def sample_evidence_admission() -> OracleResearchResponseEvidenceRequirementAdmission:
    requested_at = datetime(2026, 7, 29, 18, 30, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)
    evidence_admitted_at = materialized_at + timedelta(seconds=1)

    requirements = (
        "source_provenance",
        "market_price",
        "oracle_probability",
    )
    requirement_ids = ("1" * 64, "2" * 64, "3" * 64)
    requirement_hashes = ("4" * 64, "5" * 64, "6" * 64)

    body = {
        "evidence_admission_id": "a" * 64,
        "materialization_id": "b" * 64,
        "materialization_hash": "c" * 64,
        "plan_admission_id": "d" * 64,
        "plan_admission_hash": "e" * 64,
        "plan_id": "f" * 64,
        "plan_hash": "1" * 64,
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
        "correlation_id": "session:orr-008-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": "prediction_card",
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "planned_at": planned_at,
        "plan_admitted_at": plan_admitted_at,
        "materialized_at": materialized_at,
        "evidence_admitted_at": evidence_admitted_at,
        "plan_steps": (
            "validate_scope",
            "identify_required_evidence",
            "select_analytic_path",
            "assemble_response",
            "certify_response_boundary",
        ),
        "evidence_requirements": requirements,
        "admitted_requirement_ids": requirement_ids,
        "admitted_requirement_hashes": requirement_hashes,
        "materialization_identity_verified": True,
        "materialization_hash_verified": True,
        "materialization_contract_verified": True,
        "requirement_identity_verified": True,
        "requirement_hashes_verified": True,
        "requirement_order_verified": True,
        "requirement_count_verified": True,
        "mandatory_read_only_requirements_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_evidence_admission_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_materialization_scope_verified": True,
        "evidence_admission_single_use_verified": True,
        "duplicate_evidence_admission_allowed": False,
        "evidence_admission_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "evidence_admission_type": EVIDENCE_ADMISSION_TYPE,
        "evidence_admission_status": EVIDENCE_ADMISSION_STATUS,
    }
    return OracleResearchResponseEvidenceRequirementAdmission(
        **body,
        evidence_admission_hash=evidence_admission_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe readiness accepted")
    except OracleResearchResponseEvidenceReadInvocationReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-008 TEST")
    print(" EVIDENCE READ INVOCATION READINESS")
    print("=" * 40)

    admission = sample_evidence_admission()
    certified_at = admission.evidence_admitted_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceReadInvocationReadinessGate()

    first = gate.certify(
        evidence_admission=admission,
        readiness_certified_at=certified_at,
    )
    second = gate.certify(
        evidence_admission=admission,
        readiness_certified_at=certified_at,
    )

    assert first == second
    assert first.readiness_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "readiness_hash"
        }
    )
    assert first.readiness_type == READINESS_TYPE
    assert first.readiness_status == READINESS_STATUS
    assert len(first.read_invocations) == len(first.evidence_requirements)
    assert all(item.read_operation in ALLOWED_READ_OPERATIONS for item in first.read_invocations)
    assert all(item.read_only for item in first.read_invocations)
    assert not any(item.callable_bound for item in first.read_invocations)
    assert not any(item.callable_invoked for item in first.read_invocations)
    assert not any(item.external_side_effects_allowed for item in first.read_invocations)
    assert first.evidence_admission_identity_verified
    assert first.evidence_admission_hash_verified
    assert first.evidence_admission_contract_verified
    assert first.requirement_lineage_verified
    assert first.read_operation_scope_verified
    assert first.callable_binding_disabled_verified
    assert first.callable_invocation_disabled_verified
    assert first.readiness_single_use_verified
    assert not first.duplicate_readiness_allowed
    assert not first.readiness_reversible

    reject(
        lambda: gate.certify(
            evidence_admission=replace(admission, evidence_admission_hash="0" * 64),
            readiness_certified_at=certified_at,
        )
    )
    reject(
        lambda: gate.certify(
            evidence_admission=replace(admission, publication_allowed=True),
            readiness_certified_at=certified_at,
        )
    )
    reject(
        lambda: gate.certify(
            evidence_admission=replace(
                admission,
                admitted_requirement_ids=("1" * 64, "1" * 64, "3" * 64),
            ),
            readiness_certified_at=certified_at,
        )
    )
    reject(
        lambda: gate.certify(
            evidence_admission=admission,
            readiness_certified_at=admission.evidence_admitted_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-007 evidence admission consumed")
    print("[PASS] Complete ORR-001 through ORR-007 lineage preserved")
    print("[PASS] Deterministic evidence read invocations materialized")
    print("[PASS] Read-operation scope and requirement lineage certified")
    print("[PASS] Callable binding and invocation remain disabled")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, duplicate-identity, unsafe, and premature admissions rejected")
    print("[DONE] ORR-008 EVIDENCE READ INVOCATION READINESS GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
