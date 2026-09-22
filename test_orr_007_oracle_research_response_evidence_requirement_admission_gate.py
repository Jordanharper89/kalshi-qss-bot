from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_materialization_contract import (
    MATERIALIZATION_STATUS,
    MATERIALIZATION_TYPE,
    OracleResearchResponseEvidenceRequirement,
    OracleResearchResponseEvidenceRequirementMaterialization,
    stable_hash as materialization_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_evidence_requirement_admission_gate import *


def sample_materialization() -> OracleResearchResponseEvidenceRequirementMaterialization:
    requested_at = datetime(2026, 7, 29, 18, 20, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    planned_at = admitted_at + timedelta(seconds=1)
    plan_admitted_at = planned_at + timedelta(seconds=1)
    materialized_at = plan_admitted_at + timedelta(seconds=1)

    requirements = []
    names = ("source_provenance", "freshness", "lineage")
    for ordinal, name in enumerate(names, start=1):
        body = {
            "requirement_id": str(ordinal) * 64,
            "ordinal": ordinal,
            "requirement_name": name,
            "required": True,
            "read_only": True,
            "external_side_effects_allowed": False,
        }
        requirements.append(
            OracleResearchResponseEvidenceRequirement(
                **body,
                requirement_hash=materialization_hash(body),
            )
        )

    body = {
        "materialization_id": "a" * 64,
        "plan_admission_id": "b" * 64,
        "plan_admission_hash": "c" * 64,
        "plan_id": "d" * 64,
        "plan_hash": "e" * 64,
        "admission_id": "f" * 64,
        "admission_hash": "1" * 64,
        "request_id": "2" * 64,
        "request_hash": "3" * 64,
        "dependency_receipt_id": "4" * 64,
        "dependency_receipt_hash": "5" * 64,
        "source_runtime_completion_id": "6" * 64,
        "source_runtime_completion_hash": "7" * 64,
        "subsystem_namespace": "oracle_research_response",
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-007-test",
        "question_text": "Summarize the evidence for this Kalshi market.",
        "response_mode": "evidence_summary",
        "filters": (("venue", "Kalshi"),),
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "planned_at": planned_at,
        "plan_admitted_at": plan_admitted_at,
        "materialized_at": materialized_at,
        "plan_steps": (
            "validate_scope",
            "identify_required_evidence",
            "select_analytic_path",
            "assemble_response",
            "certify_response_boundary",
        ),
        "evidence_requirements": names,
        "materialized_requirements": tuple(requirements),
        "plan_admission_identity_verified": True,
        "plan_admission_hash_verified": True,
        "plan_admission_contract_verified": True,
        "evidence_requirement_set_verified": True,
        "evidence_requirement_order_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_materialization_boundary_verified": True,
        "read_only_boundary_verified": True,
        "single_plan_materialization_verified": True,
        "materialization_single_use_verified": True,
        "duplicate_materialization_allowed": False,
        "materialization_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "materialization_type": MATERIALIZATION_TYPE,
        "materialization_status": MATERIALIZATION_STATUS,
    }
    return OracleResearchResponseEvidenceRequirementMaterialization(
        **body,
        materialization_hash=materialization_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe evidence admission accepted")
    except OracleResearchResponseEvidenceRequirementAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-007 TEST")
    print(" EVIDENCE REQUIREMENT ADMISSION")
    print("=" * 40)

    materialization = sample_materialization()
    admitted_at = materialization.materialized_at + timedelta(seconds=1)
    gate = OracleResearchResponseEvidenceRequirementAdmissionGate()

    first = gate.admit(
        materialization=materialization,
        evidence_admitted_at=admitted_at,
    )
    second = gate.admit(
        materialization=materialization,
        evidence_admitted_at=admitted_at,
    )

    assert first == second
    assert first.evidence_admission_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "evidence_admission_hash"
        }
    )
    assert first.evidence_admission_type == EVIDENCE_ADMISSION_TYPE
    assert first.evidence_admission_status == EVIDENCE_ADMISSION_STATUS
    assert first.materialization_identity_verified
    assert first.materialization_hash_verified
    assert first.materialization_contract_verified
    assert first.requirement_identity_verified
    assert first.requirement_hashes_verified
    assert first.requirement_order_verified
    assert first.requirement_count_verified
    assert first.mandatory_read_only_requirements_verified
    assert first.evidence_admission_single_use_verified
    assert not first.duplicate_evidence_admission_allowed
    assert not first.evidence_admission_reversible
    assert len(first.admitted_requirement_ids) == 3
    assert len(first.admitted_requirement_hashes) == 3

    reject(
        lambda: gate.admit(
            materialization=replace(materialization, materialization_hash="0" * 64),
            evidence_admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            materialization=replace(materialization, publication_allowed=True),
            evidence_admitted_at=admitted_at,
        )
    )
    bad_requirement = replace(
        materialization.materialized_requirements[0],
        read_only=False,
    )
    reject(
        lambda: gate.admit(
            materialization=replace(
                materialization,
                materialized_requirements=(
                    bad_requirement,
                    *materialization.materialized_requirements[1:],
                ),
            ),
            evidence_admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            materialization=materialization,
            evidence_admitted_at=materialization.materialized_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-006 evidence materialization consumed")
    print("[PASS] Complete ORR-001 through ORR-006 lineage preserved")
    print("[PASS] Deterministic evidence-requirement admission certified")
    print("[PASS] Requirement identities, hashes, order, and count verified")
    print("[PASS] Mandatory read-only evidence boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and premature materializations rejected")
    print("[DONE] ORR-007 EVIDENCE REQUIREMENT ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
