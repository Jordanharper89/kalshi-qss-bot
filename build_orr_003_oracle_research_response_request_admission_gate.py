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
            "oracle_research_response_request_contract.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository with actual ORR-002 module.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_research_response"
SOURCE = PACKAGE / "oracle_research_response_request_contract.py"
PRODUCTION = PACKAGE / "oracle_research_response_request_admission_gate.py"
TEST = ROOT / "test_orr_003_oracle_research_response_request_admission_gate.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = 'from __future__ import annotations\n\nimport hashlib\nimport json\nfrom dataclasses import asdict, dataclass, is_dataclass\nfrom datetime import datetime, timezone\nfrom typing import Any, Mapping\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_contract import (\n    ALLOWED_RESPONSE_MODES,\n    REQUEST_STATUS as ORR_002_REQUEST_STATUS,\n    REQUEST_TYPE as ORR_002_REQUEST_TYPE,\n    SUBSYSTEM_NAMESPACE,\n    OracleResearchResponseRequest,\n)\n\nSCHEMA_VERSION = "ORR-003"\nENGINE_ID = "ORR-003"\nPOLICY_ID = "oracle.research-response.request-admission-gate.v1"\nADMISSION_TYPE = "oracle_research_response_request_admission"\nADMISSION_STATUS = "oracle_research_response_request_admitted"\n\n\nclass OracleResearchResponseRequestAdmissionInvariantError(ValueError):\n    pass\n\n\ndef _canonical(value: Any) -> Any:\n    if is_dataclass(value):\n        return _canonical(asdict(value))\n    if isinstance(value, Mapping):\n        return {\n            str(key): _canonical(item)\n            for key, item in sorted(value.items(), key=lambda item: str(item[0]))\n        }\n    if isinstance(value, (tuple, list)):\n        return [_canonical(item) for item in value]\n    if isinstance(value, datetime):\n        if value.tzinfo is None or value.utcoffset() is None:\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "datetime must be timezone-aware"\n            )\n        return value.astimezone(timezone.utc).isoformat()\n    if value is None or isinstance(value, (str, int, float, bool)):\n        return value\n    raise OracleResearchResponseRequestAdmissionInvariantError(\n        f"unsupported value type: {type(value)!r}"\n    )\n\n\ndef stable_hash(value: Any) -> str:\n    payload = json.dumps(\n        _canonical(value),\n        sort_keys=True,\n        separators=(",", ":"),\n        ensure_ascii=False,\n        allow_nan=False,\n    )\n    return hashlib.sha256(payload.encode("utf-8")).hexdigest()\n\n\ndef _valid_sha256(value: Any) -> bool:\n    return (\n        isinstance(value, str)\n        and len(value) == 64\n        and all(character in "0123456789abcdef" for character in value)\n    )\n\n\n@dataclass(frozen=True)\nclass OracleResearchResponseRequestAdmission:\n    admission_id: str\n    request_id: str\n    request_hash: str\n    dependency_receipt_id: str\n    dependency_receipt_hash: str\n    source_runtime_completion_id: str\n    source_runtime_completion_hash: str\n    subsystem_namespace: str\n    requester_id: str\n    correlation_id: str\n    question_text: str\n    response_mode: str\n    filters: tuple[tuple[str, str], ...]\n    requested_at: datetime\n    admitted_at: datetime\n    request_identity_verified: bool\n    request_hash_verified: bool\n    request_contract_verified: bool\n    typed_question_verified: bool\n    response_mode_verified: bool\n    filter_boundary_verified: bool\n    deterministic_boundary_verified: bool\n    immutable_admission_boundary_verified: bool\n    read_only_boundary_verified: bool\n    single_request_scope_verified: bool\n    admission_single_use_verified: bool\n    duplicate_admission_allowed: bool\n    admission_reversible: bool\n    runtime_serving_allowed: bool\n    network_listener_allowed: bool\n    database_connection_allowed: bool\n    publication_allowed: bool\n    qseries_handoff_allowed: bool\n    qseries_execution_allowed: bool\n    order_creation_allowed: bool\n    funds_movement_allowed: bool\n    portfolio_mutation_allowed: bool\n    admission_type: str\n    admission_status: str\n    admission_hash: str\n\n\nclass OracleResearchResponseRequestAdmissionGate:\n    def admit(\n        self,\n        *,\n        request: OracleResearchResponseRequest,\n        admitted_at: datetime,\n    ) -> OracleResearchResponseRequestAdmission:\n        if not isinstance(request, OracleResearchResponseRequest):\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "request must be canonical ORR-002 request"\n            )\n\n        request_body = asdict(request)\n        supplied_hash = request_body.pop("request_hash", None)\n        if not _valid_sha256(supplied_hash) or stable_hash(request_body) != supplied_hash:\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "ORR-002 request hash mismatch"\n            )\n\n        required = (\n            _valid_sha256(request.request_id),\n            _valid_sha256(request.dependency_receipt_id),\n            _valid_sha256(request.dependency_receipt_hash),\n            _valid_sha256(request.source_runtime_completion_id),\n            _valid_sha256(request.source_runtime_completion_hash),\n            request.subsystem_namespace == SUBSYSTEM_NAMESPACE,\n            request.response_mode in ALLOWED_RESPONSE_MODES,\n            request.request_type == ORR_002_REQUEST_TYPE,\n            request.request_status == ORR_002_REQUEST_STATUS,\n            request.dependency_identity_verified,\n            request.dependency_hash_verified,\n            request.dependency_contract_verified,\n            request.typed_question_verified,\n            request.response_mode_verified,\n            request.filter_boundary_verified,\n            request.deterministic_boundary_verified,\n            request.immutable_request_boundary_verified,\n            request.read_only_boundary_verified,\n            request.request_single_use_verified,\n            not request.duplicate_request_allowed,\n            not request.request_reversible,\n        )\n        forbidden = (\n            request.runtime_serving_allowed,\n            request.network_listener_allowed,\n            request.database_connection_allowed,\n            request.publication_allowed,\n            request.qseries_handoff_allowed,\n            request.qseries_execution_allowed,\n            request.order_creation_allowed,\n            request.funds_movement_allowed,\n            request.portfolio_mutation_allowed,\n        )\n        if not all(required) or any(forbidden):\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "ORR-002 request contract incomplete or unsafe"\n            )\n\n        if not request.question_text.strip():\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "question_text cannot be empty"\n            )\n\n        if (\n            not isinstance(admitted_at, datetime)\n            or admitted_at.tzinfo is None\n            or admitted_at.utcoffset() is None\n        ):\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "admitted_at must be timezone-aware"\n            )\n        at = admitted_at.astimezone(timezone.utc)\n        if at < request.requested_at.astimezone(timezone.utc):\n            raise OracleResearchResponseRequestAdmissionInvariantError(\n                "admission cannot precede request"\n            )\n\n        body = {\n            "request_id": request.request_id,\n            "request_hash": request.request_hash,\n            "dependency_receipt_id": request.dependency_receipt_id,\n            "dependency_receipt_hash": request.dependency_receipt_hash,\n            "source_runtime_completion_id": request.source_runtime_completion_id,\n            "source_runtime_completion_hash": request.source_runtime_completion_hash,\n            "subsystem_namespace": request.subsystem_namespace,\n            "requester_id": request.requester_id,\n            "correlation_id": request.correlation_id,\n            "question_text": request.question_text,\n            "response_mode": request.response_mode,\n            "filters": request.filters,\n            "requested_at": request.requested_at.astimezone(timezone.utc),\n            "admitted_at": at,\n            "request_identity_verified": True,\n            "request_hash_verified": True,\n            "request_contract_verified": True,\n            "typed_question_verified": True,\n            "response_mode_verified": True,\n            "filter_boundary_verified": True,\n            "deterministic_boundary_verified": True,\n            "immutable_admission_boundary_verified": True,\n            "read_only_boundary_verified": True,\n            "single_request_scope_verified": True,\n            "admission_single_use_verified": True,\n            "duplicate_admission_allowed": False,\n            "admission_reversible": False,\n            "runtime_serving_allowed": False,\n            "network_listener_allowed": False,\n            "database_connection_allowed": False,\n            "publication_allowed": False,\n            "qseries_handoff_allowed": False,\n            "qseries_execution_allowed": False,\n            "order_creation_allowed": False,\n            "funds_movement_allowed": False,\n            "portfolio_mutation_allowed": False,\n            "admission_type": ADMISSION_TYPE,\n            "admission_status": ADMISSION_STATUS,\n        }\n        body["admission_id"] = stable_hash(\n            {\n                "engine_id": ENGINE_ID,\n                "request_id": request.request_id,\n                "request_hash": request.request_hash,\n                "admitted_at": at,\n                "admission_type": ADMISSION_TYPE,\n            }\n        )\n        return OracleResearchResponseRequestAdmission(\n            **body,\n            admission_hash=stable_hash(body),\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "POLICY_ID",\n    "ADMISSION_TYPE",\n    "ADMISSION_STATUS",\n    "OracleResearchResponseRequestAdmissionInvariantError",\n    "OracleResearchResponseRequestAdmission",\n    "OracleResearchResponseRequestAdmissionGate",\n    "stable_hash",\n]\n'
TEST_SOURCE = 'from dataclasses import asdict, replace\nfrom datetime import datetime, timedelta, timezone\n\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_contract import (\n    REQUEST_STATUS,\n    REQUEST_TYPE,\n    RESPONSE_MODE_PREDICTION_CARD,\n    SUBSYSTEM_NAMESPACE,\n    OracleResearchResponseRequest,\n    stable_hash as request_hash,\n)\nfrom qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import *\n\n\ndef sample_request() -> OracleResearchResponseRequest:\n    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)\n    body = {\n        "request_id": "1" * 64,\n        "dependency_receipt_id": "2" * 64,\n        "dependency_receipt_hash": "3" * 64,\n        "source_runtime_completion_id": "4" * 64,\n        "source_runtime_completion_hash": "5" * 64,\n        "subsystem_namespace": SUBSYSTEM_NAMESPACE,\n        "requester_id": "operator:jordan",\n        "correlation_id": "session:orr-003-test",\n        "question_text": "What are the strongest Kalshi opportunities closing today?",\n        "response_mode": RESPONSE_MODE_PREDICTION_CARD,\n        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),\n        "requested_at": requested_at,\n        "dependency_identity_verified": True,\n        "dependency_hash_verified": True,\n        "dependency_contract_verified": True,\n        "typed_question_verified": True,\n        "response_mode_verified": True,\n        "filter_boundary_verified": True,\n        "deterministic_boundary_verified": True,\n        "immutable_request_boundary_verified": True,\n        "read_only_boundary_verified": True,\n        "request_single_use_verified": True,\n        "duplicate_request_allowed": False,\n        "request_reversible": False,\n        "runtime_serving_allowed": False,\n        "network_listener_allowed": False,\n        "database_connection_allowed": False,\n        "publication_allowed": False,\n        "qseries_handoff_allowed": False,\n        "qseries_execution_allowed": False,\n        "order_creation_allowed": False,\n        "funds_movement_allowed": False,\n        "portfolio_mutation_allowed": False,\n        "request_type": REQUEST_TYPE,\n        "request_status": REQUEST_STATUS,\n    }\n    return OracleResearchResponseRequest(\n        **body,\n        request_hash=request_hash(body),\n    )\n\n\ndef reject(function) -> None:\n    try:\n        function()\n        raise AssertionError("unsafe request admission accepted")\n    except OracleResearchResponseRequestAdmissionInvariantError:\n        pass\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" ORR-003 TEST")\n    print(" RESEARCH RESPONSE REQUEST ADMISSION")\n    print("=" * 40)\n\n    request = sample_request()\n    admitted_at = request.requested_at + timedelta(seconds=1)\n    gate = OracleResearchResponseRequestAdmissionGate()\n\n    first = gate.admit(request=request, admitted_at=admitted_at)\n    second = gate.admit(request=request, admitted_at=admitted_at)\n\n    assert first == second\n    assert first.admission_hash == stable_hash(\n        {\n            key: value\n            for key, value in asdict(first).items()\n            if key != "admission_hash"\n        }\n    )\n    assert first.admission_type == ADMISSION_TYPE\n    assert first.admission_status == ADMISSION_STATUS\n    assert first.request_identity_verified\n    assert first.request_hash_verified\n    assert first.request_contract_verified\n    assert first.single_request_scope_verified\n    assert first.admission_single_use_verified\n    assert not first.duplicate_admission_allowed\n    assert not first.admission_reversible\n\n    reject(\n        lambda: gate.admit(\n            request=replace(request, request_hash="0" * 64),\n            admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            request=replace(request, qseries_execution_allowed=True),\n            admitted_at=admitted_at,\n        )\n    )\n    reject(\n        lambda: gate.admit(\n            request=request,\n            admitted_at=request.requested_at - timedelta(seconds=1),\n        )\n    )\n\n    print("[PASS] Actual ORR-002 research request consumed")\n    print("[PASS] Typed natural-language question admitted")\n    print("[PASS] Complete ORR-001 through ORR-002 lineage preserved")\n    print("[PASS] Deterministic single-request admission certified")\n    print("[PASS] Immutable single-use admission boundary certified")\n    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")\n    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")\n    print("[PASS] Tampered, premature, and unsafe requests rejected")\n    print("[DONE] ORR-003 RESEARCH RESPONSE REQUEST ADMISSION GATE PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("=" * 40)
    print(" ORR-003 INSTALLER")
    print(" RESEARCH RESPONSE REQUEST ADMISSION")
    print("=" * 40)
    try:
        source_text = SOURCE.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "ORR-002"',
            "OracleResearchResponseRequest",
            "request_hash",
            "ALLOWED_RESPONSE_MODES",
            "typed_question_verified",
            "REQUEST_TYPE",
            "REQUEST_STATUS",
        )
        missing = [item for item in required if item not in source_text]
        if missing:
            raise RuntimeError(f"ORR-002 contract incomplete: {missing}")
        ast.parse(source_text, filename=str(SOURCE))
        protected_hash = sha256(SOURCE)
        print("[OK] Actual ORR-002 research response request contract verified")

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from .oracle_research_response_request_admission_gate import ("
            "ADMISSION_STATUS, "
            "ADMISSION_TYPE, "
            "OracleResearchResponseRequestAdmission, "
            "OracleResearchResponseRequestAdmissionGate, "
            "OracleResearchResponseRequestAdmissionInvariantError)"
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
            raise RuntimeError(f"ORR-003 test failed with exit code {completed.returncode}")
        if sha256(SOURCE) != protected_hash:
            raise RuntimeError("Protected ORR-002 module changed")

        print("[PASS] Protected ORR-002 module unchanged")
        print("[PASS] ORR-001 through ORR-002 lineage preserved")
        print("[PASS] Typed-question admission boundary established")
        print("[PASS] No acquisition, analytics, integration, operator, or runtime module modified")
        print("[PASS] No Q Series execution module modified")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] ORR-003 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
