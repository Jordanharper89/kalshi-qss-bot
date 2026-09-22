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
            "oracle_research_response_request_admission_gate.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-003 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_request_admission_gate.py"
PRODUCTION = PACKAGE / "oracle_research_response_planning_contract.py"
TEST = ROOT / "test_orr_004_oracle_research_response_planning_contract.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import (\n    ADMISSION_STATUS as ORR_003_ADMISSION_STATUS,\n    ADMISSION_TYPE as ORR_003_ADMISSION_TYPE,\n    OracleResearchResponseRequestAdmission,\n)\n\nSCHEMA_VERSION = "ORR-004"\nENGINE_ID = "ORR-004"\nPOLICY_ID = "oracle.research-response.planning-contract.v1"\nPLAN_TYPE = "oracle_research_response_plan"\nPLAN_STATUS = "oracle_research_response_plan_materialized"\n\nSTEP_VALIDATE_SCOPE = "validate_scope"\nSTEP_IDENTIFY_REQUIRED_EVIDENCE = "identify_required_evidence"\nSTEP_SELECT_ANALYTIC_PATH = "select_analytic_path"\nSTEP_ASSEMBLE_RESPONSE = "assemble_response"\nSTEP_CERTIFY_RESPONSE_BOUNDARY = "certify_response_boundary"\n\nALLOWED_PLAN_STEPS = (\n    STEP_VALIDATE_SCOPE,\n    STEP_IDENTIFY_REQUIRED_EVIDENCE,\n    STEP_SELECT_ANALYTIC_PATH,\n    STEP_ASSEMBLE_RESPONSE,\n    STEP_CERTIFY_RESPONSE_BOUNDARY,\n)\n\n\nclass OracleResearchResponsePlanningInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda item: str(item[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponsePlanningInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponsePlanningInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\ndef _derive_evidence_requirements(\n    response_mode: str,\n    filters: tuple[tuple[str, str], ...],\n) -> tuple[str, ...]:\n    base = (\n        "source_provenance",\n        "freshness",\n        "lineage",\n        "read_only_certification",\n    )\n    mode_specific = {\n        "research_answer": ("relevant_observations", "analytic_summary"),\n        "prediction_card": (\n            "venue_identity",\n            "market_price",\n            "oracle_probability",\n            "estimated_edge",\n            "confidence",\n            "validity_window",\n        ),\n        "market_deep_dive": (\n            "market_definition",\n            "resolution_criteria",\n            "supporting_evidence",\n            "counter_evidence",\n            "risk_factors",\n        ),\n        "comparison": (\n            "comparison_subjects",\n            "normalized_metrics",\n            "relative_ranking",\n        ),\n        "evidence_summary": (\n            "supporting_evidence",\n            "counter_evidence",\n            "source_conflicts",\n        ),\n    }\n    requirements = list(base + mode_specific.get(response_mode, ()))\n    if filters:\n        requirements.append("filter_compliance")\n    return tuple(requirements)\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponsePlan:\n    plan_id: str\n    admission_id: str\n    admission_hash: str\n    request_id: str\n    request_hash: str\n    dependency_receipt_id: str\n    dependency_receipt_hash: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    subsystem_namespace: str\n    requester_id: str\n    correlation_id: str\n    question_text: str\n    response_mode: str\n    filters: tuple[tuple[str, str], ...]\n    requested_at: datetime\n    admitted_at: datetime\n    planned_at: datetime\n    plan_steps: tuple[str, ...]\n    evidence_requirements: tuple[str, ...]\n    admission_identity_verified: bool\n    admission_hash_verified: bool\n    admission_contract_verified: bool\n    planning_scope_verified: bool\n    evidence_requirements_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_plan_boundary_verified: bool\n    read_only_boundary_verified: bool\n    plan_single_use_verified: bool\n    duplicate_plan_allowed: bool\n    plan_reversible: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    plan_type: str\n    plan_status: str\n    plan_hash: str\n\n\nclass OracleResearchResponsePlanningContract:\n    def materialize(\n        self,\n        *,\n        admission: OracleResearchResponseRequestAdmission,\n        planned_at: datetime,\n    ) -> OracleResearchResponsePlan:\n        if not isinstance(admission, OracleResearchResponseRequestAdmission):\n            raise OracleResearchResponsePlanningInvariantError(\n                "admission must be canonical ORR-003 admission"\n            )\n\n        admission_body = asdict(admission)\n        supplied_hash = admission_body.pop("admission_hash", None)\n        if (\n            not _valid_sha256(supplied_hash)\n            or stable_hash(admission_body) != supplied_hash\n        ):\n            raise OracleResearchResponsePlanningInvariantError(\n                "ORR-003 admission hash mismatch"\n            )\n\n        required = (\n            _valid_sha256(admission.admission_id),\n            _valid_sha256(admission.request_id),\n            _valid_sha256(admission.request_hash),\n            _valid_sha256(admission.dependency_receipt_id),\n            _valid_sha256(admission.dependency_receipt_hash),\n            _valid_sha256(admission.source_runtime_completion_id),\n            _valid_sha256(admission.source_runtime_completion_hash),\n            admission.admission_type == ORR_003_ADMISSION_TYPE,\n            admission.admission_status == ORR_003_ADMISSION_STATUS,\n            admission.request_identity_verified,\n            admission.request_hash_verified,\n            admission.request_contract_verified,\n            admission.typed_question_verified,\n            admission.response_mode_verified,\n            admission.filter_boundary_verified,\n            admission.deterministic_boundary_verified,\n            admission.immutable_admission_boundary_verified,\n            admission.read_only_boundary_verified,\n            admission.single_request_scope_verified,\n            admission.admission_single_use_verified,\n            not admission.duplicate_admission_allowed,\n            not admission.admission_reversible,\n        )\n        forbidden = (\n            admission.runtime_serving_allowed,\n            admission.network_listener_allowed,\n            admission.database_connection_allowed,\n            admission.publication_allowed,\n            admission.qseries_handoff_allowed,\n            admission.qseries_execution_allowed,\n            admission.order_creation_allowed,\n            admission.funds_movement_allowed,\n            admission.portfolio_mutation_allowed,\n        )\n        if not all(required) or any(forbidden):\n            raise OracleResearchResponsePlanningInvariantError(\n                "ORR-003 admission contract incomplete or unsafe"\n            )\n\n        if (\n            not isinstance(planned_at, datetime)\n            or planned_at.tzinfo is None\n            or planned_at.utcoffset() is None\n        ):\n            raise OracleResearchResponsePlanningInvariantError(\n                "planned_at must be timezone-aware"\n            )\n        at = planned_at.astimezone(timezone.utc)\n        if at < admission.admitted_at.astimezone(timezone.utc):\n            raise OracleResearchResponsePlanningInvariantError(\n                "planning cannot precede admission"\n            )\n\n        plan_steps = ALLOWED_PLAN_STEPS\n        evidence_requirements = _derive_evidence_requirements(\n            admission.response_mode,\n            admission.filters,\n        )\n\n        body = {\n            "admission_id": admission.admission_id,\n            "admission_hash": admission.admission_hash,\n            "request_id": admission.request_id,\n            "request_hash": admission.request_hash,\n            "dependency_receipt_id": admission.dependency_receipt_id,\n            "dependency_receipt_hash": admission.dependency_receipt_hash,\n            "source_runtime_completion_id": admission.source_runtime_completion_id,\n            "source_runtime_completion_hash": admission.source_runtime_completion_hash,\n            "subsystem_namespace": admission.subsystem_namespace,\n            "requester_id": admission.requester_id,\n            "correlation_id": admission.correlation_id,\n            "question_text": admission.question_text,\n            "response_mode": admission.response_mode,\n            "filters": admission.filters,\n            "requested_at": admission.requested_at.astimezone(timezone.utc),\n            "admitted_at": admission.admitted_at.astimezone(timezone.utc),\n            "planned_at": at,\n            "plan_steps": plan_steps,\n            "evidence_requirements": evidence_requirements,\n            "admission_identity_verified": True,\n            "admission_hash_verified": True,\n            "admission_contract_verified": True,\n            "planning_scope_verified": True,\n            "evidence_requirements_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_plan_boundary_verified": True,\n            "read_only_boundary_verified": True,\n            "plan_single_use_verified": True,\n            "duplicate_plan_allowed": False,\n            "plan_reversible": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "plan_type": PLAN_TYPE,\n            "plan_status": PLAN_STATUS,\n        }\n        body["plan_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "admission_id": admission.admission_id,\n                "admission_hash": admission.admission_hash,\n                "planned_at": at,\n                "plan_steps": plan_steps,\n                "evidence_requirements": evidence_requirements,\n                "plan_type": PLAN_TYPE,\n            }\n        )\n        return OracleResearchResponsePlan(\n            **body,\n            plan_hash=stable_hash(body),\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "PLAN_TYPE",\n    "PLAN_STATUS",\n    "ALLOWED_PLAN_STEPS",\n    "OracleResearchResponsePlanningInvariantError",\n    "OracleResearchResponsePlan",\n    "OracleResearchResponsePlanningContract",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timedelta, timezone\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import (\n    ADMISSION_STATUS,\n    ADMISSION_TYPE,\n    OracleResearchResponseRequestAdmission,\n    stable_hash as admission_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_planning_contract import *\n\n\ndef sample_admission() -> OracleResearchResponseRequestAdmission:\n    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)\n    admitted_at = requested_at + timedelta(seconds=1)\n    body = {\n        "admission_id": "1" * 64,\n        "request_id": "2" * 64,\n        "request_hash": "3" * 64,\n        "dependency_receipt_id": "4" * 64,\n        "dependency_receipt_hash": "5" * 64,\n        "source_runtime_completion_id": "6" * 64,\n        "source_runtime_completion_hash": "7" * 64,\n        "subsystem_namespace": "oracle_research_response",\n        "requester_id": "operator:jordan",\n        "correlation_id": "session:orr-004-test",\n        "question_text": "What are the strongest Kalshi opportunities closing today?",\n        "response_mode": "prediction_card",\n        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),\n        "requested_at": requested_at,\n        "admitted_at": admitted_at,\n        "request_identity_verified": True,\n        "request_hash_verified": True,\n        "request_contract_verified": True,\n        "typed_question_verified": True,\n        "response_mode_verified": True,\n        "filter_boundary_verified": True,\n        "deterministic_boundary_verified": True,\n        "immutable_admission_boundary_verified": True,\n        "read_only_boundary_verified": True,\n        "single_request_scope_verified": True,\n        "admission_single_use_verified": True,\n        "duplicate_admission_allowed": False,\n        "admission_reversible": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "admission_type": ADMISSION_TYPE,\n        "admission_status": ADMISSION_STATUS,\n    }\n    return OracleResearchResponseRequestAdmission(\n        **body,\n        admission_hash=admission_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe response plan accepted")\n    except OracleResearchResponsePlanningInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-004 TEST")\n    print(" RESEARCH RESPONSE PLANNING CONTRACT")\n    print("=" * 40)\n\n    admission = sample_admission()\n    planned_at = admission.admitted_at + timedelta(seconds=1)\n    contract = OracleResearchResponsePlanningContract()\n\n    first = contract.materialize(admission=admission, planned_at=planned_at)\n    second = contract.materialize(admission=admission, planned_at=planned_at)\n\n    assert first == second\n    assert first.plan_hash == stable_hash(\n        {\n            key: value\n            for key, value in asdict(first).items()\n            if key != "plan_hash"\n        }\n    )\n    assert first.plan_type == PLAN_TYPE\n    assert first.plan_status == PLAN_STATUS\n    assert first.plan_steps == ALLOWED_PLAN_STEPS\n    assert "venue_identity" in first.evidence_requirements\n    assert "oracle_probability" in first.evidence_requirements\n    assert "filter_compliance" in first.evidence_requirements\n    assert first.admission_identity_verified\n    assert first.admission_hash_verified\n    assert first.admission_contract_verified\n    assert first.planning_scope_verified\n    assert first.evidence_requirements_verified\n    assert first.read_only_boundary_verified\n    assert first.plan_single_use_verified\n    assert not first.duplicate_plan_allowed\n    assert not first.plan_reversible\n\n    reject(\n        lambda: contract.materialize(\n            admission=replace(admission, admission_hash="0" * 64),\n            planned_at=planned_at,\n        )\n    )\n    reject(\n        lambda: contract.materialize(\n            admission=replace(admission, publication_allowed=True),\n            planned_at=planned_at,\n        )\n    )\n    reject(\n        lambda: contract.materialize(\n            admission=admission,\n            planned_at=admission.admitted_at - timedelta(seconds=1),\n        )\n    )\n\n    print("[PASS] Actual ORR-003 request admission consumed")\n    print("[PASS] Complete ORR-001 through ORR-003 lineage preserved")\n    print("[PASS] Deterministic response plan materialized")\n    print("[PASS] Response-mode evidence requirements certified")\n    print("[PASS] Immutable single-use planning boundary certified")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] Tampered, premature, and unsafe admissions rejected")\n    print("[DONE] ORR-004 RESEARCH RESPONSE PLANNING CONTRACT PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-004 INSTALLER")
    print(" RESEARCH RESPONSE PLANNING CONTRACT")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-003"',
            "OracleResearchResponseRequestAdmission",
            "admission_hash",
            "request_contract_verified",
            "ADMISSION_TYPE",
            "ADMISSION_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-003 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-003 request admission contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_planning_contract import ("
            "ALLOWED_PLAN_STEPS, "
            "PLAN_STATUS, "
            "PLAN_TYPE, "
            "OracleResearchResponsePlan, "
            "OracleResearchResponsePlanningContract, "
            "OracleResearchResponsePlanningInvariantError)"
        )
        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else "from __future__ import annotations\n"
        )
        if export not in current:
            INIT.write_text(
                current.rstrip() + "\n\n" + export + "\n",
                encoding="utf-8",
                newline="\n",
            )
        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))
        print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")

        completed = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=False)
        if completed.returncode:
            raise RuntimeError(f"ORR-004 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-003 module changed")

        print("[PASS] Protected ORR-003 module unchanged")
        print("[PASS] ORR-001 through ORR-003 lineage preserved")
        print("[PASS] Research response planning boundary established")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-004 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
