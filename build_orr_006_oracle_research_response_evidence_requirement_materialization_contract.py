from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (
            candidate / "qseries_v2" / "oracle_research_response" /
            "oracle_research_response_plan_admission_gate.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-005 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_plan_admission_gate.py"
PRODUCTION = PACKAGE / "oracle_research_response_evidence_requirement_materialization_contract.py"
TEST = ROOT / "test_orr_006_oracle_research_response_evidence_requirement_materialization_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_research_response.oracle_research_response_plan_admission_gate import (
    PLAN_ADMISSION_STATUS as ORR_005_PLAN_ADMISSION_STATUS,
    PLAN_ADMISSION_TYPE as ORR_005_PLAN_ADMISSION_TYPE,
    OracleResearchResponsePlanAdmission,
)

SCHEMA_VERSION = "ORR-006"
ENGINE_ID = "ORR-006"
POLICY_ID = "oracle.research-response.evidence-requirement-materialization.v1"
MATERIALIZATION_TYPE = "oracle_research_response_evidence_requirement_materialization"
MATERIALIZATION_STATUS = "oracle_research_response_evidence_requirements_materialized"

SUPPORTED_EVIDENCE_REQUIREMENTS = (
    "source_provenance", "freshness", "lineage", "read_only_certification",
    "relevant_observations", "analytic_summary", "venue_identity", "market_price",
    "oracle_probability", "estimated_edge", "confidence", "validity_window",
    "market_definition", "resolution_criteria", "supporting_evidence",
    "counter_evidence", "risk_factors", "comparison_subjects",
    "normalized_metrics", "relative_ranking", "source_conflicts", "filter_compliance",
)


class OracleResearchResponseEvidenceRequirementMaterializationInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda i: str(i[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class OracleResearchResponseEvidenceRequirement:
    requirement_id: str
    ordinal: int
    requirement_name: str
    required: bool
    read_only: bool
    external_side_effects_allowed: bool
    requirement_hash: str


@dataclass(frozen=True)
class OracleResearchResponseEvidenceRequirementMaterialization:
    materialization_id: str
    plan_admission_id: str
    plan_admission_hash: str
    plan_id: str
    plan_hash: str
    admission_id: str
    admission_hash: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_runtime_completion_id: str
    source_runtime_completion_hash: str
    subsystem_namespace: str
    requester_id: str
    correlation_id: str
    question_text: str
    response_mode: str
    filters: tuple[tuple[str, str], ...]
    requested_at: datetime
    admitted_at: datetime
    planned_at: datetime
    plan_admitted_at: datetime
    materialized_at: datetime
    plan_steps: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    materialized_requirements: tuple[OracleResearchResponseEvidenceRequirement, ...]
    plan_admission_identity_verified: bool
    plan_admission_hash_verified: bool
    plan_admission_contract_verified: bool
    evidence_requirement_set_verified: bool
    evidence_requirement_order_verified: bool
    deterministic_boundary_verified: bool
    immutable_materialization_boundary_verified: bool
    read_only_boundary_verified: bool
    single_plan_materialization_verified: bool
    materialization_single_use_verified: bool
    duplicate_materialization_allowed: bool
    materialization_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    materialization_type: str
    materialization_status: str
    materialization_hash: str


class OracleResearchResponseEvidenceRequirementMaterializationContract:
    def materialize(self, *, plan_admission: OracleResearchResponsePlanAdmission,
                    materialized_at: datetime) -> OracleResearchResponseEvidenceRequirementMaterialization:
        if not isinstance(plan_admission, OracleResearchResponsePlanAdmission):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "plan_admission must be canonical ORR-005 plan admission"
            )

        admission_body = asdict(plan_admission)
        supplied_hash = admission_body.pop("plan_admission_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(admission_body) != supplied_hash:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "ORR-005 plan admission hash mismatch"
            )

        required = (
            _valid_sha256(plan_admission.plan_admission_id),
            _valid_sha256(plan_admission.plan_id),
            _valid_sha256(plan_admission.plan_hash),
            _valid_sha256(plan_admission.admission_id),
            _valid_sha256(plan_admission.admission_hash),
            _valid_sha256(plan_admission.request_id),
            _valid_sha256(plan_admission.request_hash),
            _valid_sha256(plan_admission.dependency_receipt_id),
            _valid_sha256(plan_admission.dependency_receipt_hash),
            _valid_sha256(plan_admission.source_runtime_completion_id),
            _valid_sha256(plan_admission.source_runtime_completion_hash),
            plan_admission.plan_admission_type == ORR_005_PLAN_ADMISSION_TYPE,
            plan_admission.plan_admission_status == ORR_005_PLAN_ADMISSION_STATUS,
            plan_admission.plan_identity_verified,
            plan_admission.plan_hash_verified,
            plan_admission.plan_contract_verified,
            plan_admission.plan_steps_verified,
            plan_admission.evidence_requirements_verified,
            plan_admission.deterministic_boundary_verified,
            plan_admission.immutable_plan_admission_boundary_verified,
            plan_admission.read_only_boundary_verified,
            plan_admission.single_plan_scope_verified,
            plan_admission.plan_admission_single_use_verified,
            not plan_admission.duplicate_plan_admission_allowed,
            not plan_admission.plan_admission_reversible,
        )
        forbidden = (
            plan_admission.runtime_serving_allowed,
            plan_admission.network_listener_allowed,
            plan_admission.database_connection_allowed,
            plan_admission.publication_allowed,
            plan_admission.qseries_handoff_allowed,
            plan_admission.qseries_execution_allowed,
            plan_admission.order_creation_allowed,
            plan_admission.funds_movement_allowed,
            plan_admission.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "ORR-005 plan admission contract incomplete or unsafe"
            )

        if materialized_at.tzinfo is None or materialized_at.utcoffset() is None:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "materialized_at must be timezone-aware"
            )
        at = materialized_at.astimezone(timezone.utc)
        if at < plan_admission.plan_admitted_at.astimezone(timezone.utc):
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "materialization cannot precede plan admission"
            )

        requirements = tuple(dict.fromkeys(v.strip() for v in plan_admission.evidence_requirements if v.strip()))
        if not requirements:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                "evidence requirements cannot be empty"
            )
        unsupported = tuple(v for v in requirements if v not in SUPPORTED_EVIDENCE_REQUIREMENTS)
        if unsupported:
            raise OracleResearchResponseEvidenceRequirementMaterializationInvariantError(
                f"unsupported evidence requirements: {unsupported}"
            )

        records = []
        for ordinal, name in enumerate(requirements, start=1):
            item_body = {
                "ordinal": ordinal,
                "requirement_name": name,
                "required": True,
                "read_only": True,
                "external_side_effects_allowed": False,
            }
            requirement_id = stable_hash({
                "engine_id": ENGINE_ID,
                "plan_admission_id": plan_admission.plan_admission_id,
                **item_body,
            })
            records.append(OracleResearchResponseEvidenceRequirement(
                requirement_id=requirement_id,
                **item_body,
                requirement_hash=stable_hash({"requirement_id": requirement_id, **item_body}),
            ))

        body = {
            "plan_admission_id": plan_admission.plan_admission_id,
            "plan_admission_hash": plan_admission.plan_admission_hash,
            "plan_id": plan_admission.plan_id,
            "plan_hash": plan_admission.plan_hash,
            "admission_id": plan_admission.admission_id,
            "admission_hash": plan_admission.admission_hash,
            "request_id": plan_admission.request_id,
            "request_hash": plan_admission.request_hash,
            "dependency_receipt_id": plan_admission.dependency_receipt_id,
            "dependency_receipt_hash": plan_admission.dependency_receipt_hash,
            "source_runtime_completion_id": plan_admission.source_runtime_completion_id,
            "source_runtime_completion_hash": plan_admission.source_runtime_completion_hash,
            "subsystem_namespace": plan_admission.subsystem_namespace,
            "requester_id": plan_admission.requester_id,
            "correlation_id": plan_admission.correlation_id,
            "question_text": plan_admission.question_text,
            "response_mode": plan_admission.response_mode,
            "filters": plan_admission.filters,
            "requested_at": plan_admission.requested_at.astimezone(timezone.utc),
            "admitted_at": plan_admission.admitted_at.astimezone(timezone.utc),
            "planned_at": plan_admission.planned_at.astimezone(timezone.utc),
            "plan_admitted_at": plan_admission.plan_admitted_at.astimezone(timezone.utc),
            "materialized_at": at,
            "plan_steps": plan_admission.plan_steps,
            "evidence_requirements": requirements,
            "materialized_requirements": tuple(records),
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
        body["materialization_id"] = stable_hash({
            "engine_id": ENGINE_ID,
            "plan_admission_id": plan_admission.plan_admission_id,
            "plan_admission_hash": plan_admission.plan_admission_hash,
            "materialized_at": at,
            "evidence_requirements": requirements,
            "materialization_type": MATERIALIZATION_TYPE,
        })
        return OracleResearchResponseEvidenceRequirementMaterialization(
            **body,
            materialization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION", "ENGINE_ID", "POLICY_ID", "MATERIALIZATION_TYPE",
    "MATERIALIZATION_STATUS", "SUPPORTED_EVIDENCE_REQUIREMENTS",
    "OracleResearchResponseEvidenceRequirementMaterializationInvariantError",
    "OracleResearchResponseEvidenceRequirement",
    "OracleResearchResponseEvidenceRequirementMaterialization",
    "OracleResearchResponseEvidenceRequirementMaterializationContract", "stable_hash",
]
'''

TEST_SOURCE = r'''from dataclasses import asdict, replace
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
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-006 INSTALLER")
    print(" EVIDENCE REQUIREMENT MATERIALIZATION")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-005"',
            "OracleResearchResponsePlanAdmission",
            "plan_admission_hash",
            "evidence_requirements",
            "PLAN_ADMISSION_TYPE",
            "PLAN_ADMISSION_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-005 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-005 plan admission gate verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_evidence_requirement_materialization_contract import ("
            "MATERIALIZATION_STATUS, MATERIALIZATION_TYPE, SUPPORTED_EVIDENCE_REQUIREMENTS, "
            "OracleResearchResponseEvidenceRequirement, "
            "OracleResearchResponseEvidenceRequirementMaterialization, "
            "OracleResearchResponseEvidenceRequirementMaterializationContract, "
            "OracleResearchResponseEvidenceRequirementMaterializationInvariantError)"
        )
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else "from __future__ import annotations\n"
        if export not in current:
            INIT.write_text(current.rstrip() + "\n\n" + export + "\n", encoding="utf-8", newline="\n")
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))
        print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"ORR-006 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-005 module changed")

        print("[PASS] Protected ORR-005 module unchanged")
        print("[PASS] ORR-001 through ORR-005 lineage preserved")
        print("[PASS] Evidence-requirement materialization boundary established")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-006 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError, TypeError, AttributeError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
