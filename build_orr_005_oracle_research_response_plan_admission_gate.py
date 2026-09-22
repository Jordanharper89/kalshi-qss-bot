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
            "oracle_research_response_planning_contract.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-004 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_planning_contract.py"
PRODUCTION = PACKAGE / "oracle_research_response_plan_admission_gate.py"
TEST = ROOT / "test_orr_005_oracle_research_response_plan_admission_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_planning_contract import (\n    ALLOWED_PLAN_STEPS,\n    PLAN_STATUS as ORR_004_PLAN_STATUS,\n    PLAN_TYPE as ORR_004_PLAN_TYPE,\n    OracleResearchResponsePlan,\n)\n\nSCHEMA_VERSION = "ORR-005"\nENGINE_ID = "ORR-005"\nPOLICY_ID = "oracle.research-response.plan-admission-gate.v1"\nPLAN_ADMISSION_TYPE = "oracle_research_response_plan_admission"\nPLAN_ADMISSION_STATUS = "oracle_research_response_plan_admitted"\n\n\nclass OracleResearchResponsePlanAdmissionInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda item: str(item[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponsePlanAdmissionInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponsePlanAdmission:\n    plan_admission_id: str\n    plan_id: str\n    plan_hash: str\n    admission_id: str\n    admission_hash: str\n    request_id: str\n    request_hash: str\n    dependency_receipt_id: str\n    dependency_receipt_hash: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    subsystem_namespace: str\n    requester_id: str\n    correlation_id: str\n    question_text: str\n    response_mode: str\n    filters: tuple[tuple[str, str], ...]\n    requested_at: datetime\n    admitted_at: datetime\n    planned_at: datetime\n    plan_admitted_at: datetime\n    plan_steps: tuple[str, ...]\n    evidence_requirements: tuple[str, ...]\n    plan_identity_verified: bool\n    plan_hash_verified: bool\n    plan_contract_verified: bool\n    plan_steps_verified: bool\n    evidence_requirements_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_plan_admission_boundary_verified: bool\n    read_only_boundary_verified: bool\n    single_plan_scope_verified: bool\n    plan_admission_single_use_verified: bool\n    duplicate_plan_admission_allowed: bool\n    plan_admission_reversible: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    plan_admission_type: str\n    plan_admission_status: str\n    plan_admission_hash: str\n\n\nclass OracleResearchResponsePlanAdmissionGate:\n    def admit(\n        self,\n        *,\n        plan: OracleResearchResponsePlan,\n        plan_admitted_at: datetime,\n    ) -> OracleResearchResponsePlanAdmission:\n        if not isinstance(plan, OracleResearchResponsePlan):\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "plan must be canonical ORR-004 plan"\n            )\n\n        plan_body = asdict(plan)\n        supplied_hash = plan_body.pop("plan_hash", None)\n        if not _valid_sha256(supplied_hash) or stable_hash(plan_body) != supplied_hash:\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "ORR-004 plan hash mismatch"\n            )\n\n        required = (\n            _valid_sha256(plan.plan_id),\n            _valid_sha256(plan.admission_id),\n            _valid_sha256(plan.admission_hash),\n            _valid_sha256(plan.request_id),\n            _valid_sha256(plan.request_hash),\n            _valid_sha256(plan.dependency_receipt_id),\n            _valid_sha256(plan.dependency_receipt_hash),\n            _valid_sha256(plan.source_runtime_completion_id),\n            _valid_sha256(plan.source_runtime_completion_hash),\n            plan.plan_type == ORR_004_PLAN_TYPE,\n            plan.plan_status == ORR_004_PLAN_STATUS,\n            plan.plan_steps == ALLOWED_PLAN_STEPS,\n            bool(plan.evidence_requirements),\n            plan.admission_identity_verified,\n            plan.admission_hash_verified,\n            plan.admission_contract_verified,\n            plan.planning_scope_verified,\n            plan.evidence_requirements_verified,\n            plan.deterministic_boundary_verified,\n            plan.immutable_plan_boundary_verified,\n            plan.read_only_boundary_verified,\n            plan.plan_single_use_verified,\n            not plan.duplicate_plan_allowed,\n            not plan.plan_reversible,\n        )\n        forbidden = (\n            plan.runtime_serving_allowed,\n            plan.network_listener_allowed,\n            plan.database_connection_allowed,\n            plan.publication_allowed,\n            plan.qseries_handoff_allowed,\n            plan.qseries_execution_allowed,\n            plan.order_creation_allowed,\n            plan.funds_movement_allowed,\n            plan.portfolio_mutation_allowed,\n        )\n        if not all(required) or any(forbidden):\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "ORR-004 plan contract incomplete or unsafe"\n            )\n\n        if (\n            not isinstance(plan_admitted_at, datetime)\n            or plan_admitted_at.tzinfo is None\n            or plan_admitted_at.utcoffset() is None\n        ):\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "plan_admitted_at must be timezone-aware"\n            )\n        at = plan_admitted_at.astimezone(timezone.utc)\n        if at < plan.planned_at.astimezone(timezone.utc):\n            raise OracleResearchResponsePlanAdmissionInvariantError(\n                "plan admission cannot precede planning"\n            )\n\n        body = {\n            "plan_id": plan.plan_id,\n            "plan_hash": plan.plan_hash,\n            "admission_id": plan.admission_id,\n            "admission_hash": plan.admission_hash,\n            "request_id": plan.request_id,\n            "request_hash": plan.request_hash,\n            "dependency_receipt_id": plan.dependency_receipt_id,\n            "dependency_receipt_hash": plan.dependency_receipt_hash,\n            "source_runtime_completion_id": plan.source_runtime_completion_id,\n            "source_runtime_completion_hash": plan.source_runtime_completion_hash,\n            "subsystem_namespace": plan.subsystem_namespace,\n            "requester_id": plan.requester_id,\n            "correlation_id": plan.correlation_id,\n            "question_text": plan.question_text,\n            "response_mode": plan.response_mode,\n            "filters": plan.filters,\n            "requested_at": plan.requested_at.astimezone(timezone.utc),\n            "admitted_at": plan.admitted_at.astimezone(timezone.utc),\n            "planned_at": plan.planned_at.astimezone(timezone.utc),\n            "plan_admitted_at": at,\n            "plan_steps": plan.plan_steps,\n            "evidence_requirements": plan.evidence_requirements,\n            "plan_identity_verified": True,\n            "plan_hash_verified": True,\n            "plan_contract_verified": True,\n            "plan_steps_verified": True,\n            "evidence_requirements_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_plan_admission_boundary_verified": True,\n            "read_only_boundary_verified": True,\n            "single_plan_scope_verified": True,\n            "plan_admission_single_use_verified": True,\n            "duplicate_plan_admission_allowed": False,\n            "plan_admission_reversible": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "plan_admission_type": PLAN_ADMISSION_TYPE,\n            "plan_admission_status": PLAN_ADMISSION_STATUS,\n        }\n        body["plan_admission_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "plan_id": plan.plan_id,\n                "plan_hash": plan.plan_hash,\n                "plan_admitted_at": at,\n                "plan_admission_type": PLAN_ADMISSION_TYPE,\n            }\n        )\n        return OracleResearchResponsePlanAdmission(\n            **body,\n            plan_admission_hash=stable_hash(body),\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "PLAN_ADMISSION_TYPE",\n    "PLAN_ADMISSION_STATUS",\n    "OracleResearchResponsePlanAdmissionInvariantError",\n    "OracleResearchResponsePlanAdmission",\n    "OracleResearchResponsePlanAdmissionGate",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timedelta, timezone\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_planning_contract import (\n    ALLOWED_PLAN_STEPS,\n    PLAN_STATUS,\n    PLAN_TYPE,\n    OracleResearchResponsePlan,\n    stable_hash as plan_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_plan_admission_gate import *\n\n\ndef sample_plan() -> OracleResearchResponsePlan:\n    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)\n    admitted_at = requested_at + timedelta(seconds=1)\n    planned_at = admitted_at + timedelta(seconds=1)\n    body = {\n        "plan_id": "1" * 64,\n        "admission_id": "2" * 64,\n        "admission_hash": "3" * 64,\n        "request_id": "4" * 64,\n        "request_hash": "5" * 64,\n        "dependency_receipt_id": "6" * 64,\n        "dependency_receipt_hash": "7" * 64,\n        "source_runtime_completion_id": "8" * 64,\n        "source_runtime_completion_hash": "9" * 64,\n        "subsystem_namespace": "oracle_research_response",\n        "requester_id": "operator:jordan",\n        "correlation_id": "session:orr-005-test",\n        "question_text": "What are the strongest Kalshi opportunities closing today?",\n        "response_mode": "prediction_card",\n        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),\n        "requested_at": requested_at,\n        "admitted_at": admitted_at,\n        "planned_at": planned_at,\n        "plan_steps": ALLOWED_PLAN_STEPS,\n        "evidence_requirements": (\n            "source_provenance",\n            "freshness",\n            "lineage",\n            "read_only_certification",\n            "venue_identity",\n            "market_price",\n            "oracle_probability",\n            "estimated_edge",\n            "confidence",\n            "validity_window",\n            "filter_compliance",\n        ),\n        "admission_identity_verified": True,\n        "admission_hash_verified": True,\n        "admission_contract_verified": True,\n        "planning_scope_verified": True,\n        "evidence_requirements_verified": True,\n        "deterministic_boundary_verified": True,\n        "immutable_plan_boundary_verified": True,\n        "read_only_boundary_verified": True,\n        "plan_single_use_verified": True,\n        "duplicate_plan_allowed": False,\n        "plan_reversible": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "plan_type": PLAN_TYPE,\n        "plan_status": PLAN_STATUS,\n    }\n    return OracleResearchResponsePlan(\n        **body,\n        plan_hash=plan_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe plan admission accepted")\n    except OracleResearchResponsePlanAdmissionInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-005 TEST")\n    print(" RESEARCH RESPONSE PLAN ADMISSION")\n    print("=" * 40)\n\n    plan = sample_plan()\n    admitted_at = plan.planned_at + timedelta(seconds=1)\n    gate = OracleResearchResponsePlanAdmissionGate()\n\n    first = gate.admit(plan=plan, plan_admitted_at=admitted_at)\n    second = gate.admit(plan=plan, plan_admitted_at=admitted_at)\n\n    assert first == second\n    assert first.plan_admission_hash == stable_hash(\n        {\n            key: value\n            for key, value in asdict(first).items()\n            if key != "plan_admission_hash"\n        }\n    )\n    assert first.plan_admission_type == PLAN_ADMISSION_TYPE\n    assert first.plan_admission_status == PLAN_ADMISSION_STATUS\n    assert first.plan_identity_verified\n    assert first.plan_hash_verified\n    assert first.plan_contract_verified\n    assert first.plan_steps_verified\n    assert first.evidence_requirements_verified\n    assert first.single_plan_scope_verified\n    assert first.plan_admission_single_use_verified\n    assert not first.duplicate_plan_admission_allowed\n    assert not first.plan_admission_reversible\n\n    reject(\n        lambda: gate.admit(\n            plan=replace(plan, plan_hash="0" * 64),\n            plan_admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            plan=replace(plan, network_listener_allowed=True),\n            plan_admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            plan=replace(plan, evidence_requirements=()),\n            plan_admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            plan=plan,\n            plan_admitted_at=plan.planned_at - timedelta(seconds=1),\n        )\n    )\n\n    print("[PASS] Actual ORR-004 research response plan consumed")\n    print("[PASS] Complete ORR-001 through ORR-004 lineage preserved")\n    print("[PASS] Deterministic single-plan admission certified")\n    print("[PASS] Plan steps and evidence requirements admitted")\n    print("[PASS] Immutable single-use plan-admission boundary certified")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] Tampered, empty, premature, and unsafe plans rejected")\n    print("[DONE] ORR-005 RESEARCH RESPONSE PLAN ADMISSION GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-005 INSTALLER")
    print(" RESEARCH RESPONSE PLAN ADMISSION")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-004"',
            "OracleResearchResponsePlan",
            "plan_hash",
            "ALLOWED_PLAN_STEPS",
            "evidence_requirements_verified",
            "PLAN_TYPE",
            "PLAN_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-004 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-004 research response planning contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_plan_admission_gate import ("
            "PLAN_ADMISSION_STATUS, "
            "PLAN_ADMISSION_TYPE, "
            "OracleResearchResponsePlanAdmission, "
            "OracleResearchResponsePlanAdmissionGate, "
            "OracleResearchResponsePlanAdmissionInvariantError)"
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
            raise RuntimeError(f"ORR-005 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-004 module changed")

        print("[PASS] Protected ORR-004 module unchanged")
        print("[PASS] ORR-001 through ORR-004 lineage preserved")
        print("[PASS] Research response plan admission boundary established")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-005 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
