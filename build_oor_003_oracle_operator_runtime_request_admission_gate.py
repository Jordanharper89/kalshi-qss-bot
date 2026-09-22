from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
RUNTIME = QSERIES / "oracle_operator_runtime"
SOURCE_002 = RUNTIME / "oracle_operator_runtime_request_contract.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_request_admission_gate.py"
TEST = ROOT / "test_oor_003_oracle_operator_runtime_request_admission_gate.py"
RUNTIME_INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_contract import (
    REQUEST_STATUS as OOR_002_REQUEST_STATUS,
    REQUEST_TYPE as OOR_002_REQUEST_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeRequest,
)

SCHEMA_VERSION = "OOR-003"
ENGINE_ID = "OOR-003"
POLICY_ID = "oracle.operator-runtime-request-admission-gate.v1"
ADMISSION_TYPE = "oracle_operator_runtime_read_only_request_admission"
ADMISSION_STATUS = "oracle_operator_runtime_request_admitted"

_ALLOWED_MODES = frozenset({"query", "session", "console", "presentation"})


class OracleOperatorRuntimeRequestAdmissionInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeRequestAdmissionInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleOperatorRuntimeRequestAdmission:
    admission_id: str
    request_id: str
    request_hash: str
    dependency_receipt_id: str
    dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    requester_id: str
    correlation_id: str
    mode: str
    query_text: str
    requested_at: datetime
    admitted_at: datetime
    request_identity_verified: bool
    request_hash_verified: bool
    request_contract_verified: bool
    request_mode_verified: bool
    request_text_verified: bool
    read_only_boundary_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    admission_type: str
    admission_status: str
    admission_hash: str


class OracleOperatorRuntimeRequestAdmissionGate:
    @staticmethod
    def _verify_request(request: OracleOperatorRuntimeRequest) -> None:
        if not isinstance(request, OracleOperatorRuntimeRequest):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "request must be canonical OOR-002 runtime request"
            )

        body = asdict(request)
        supplied_hash = body.pop("request_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "OOR-002 request hash mismatch"
            )

        required = (
            _valid_sha256(request.request_id),
            _valid_sha256(request.dependency_receipt_id),
            _valid_sha256(request.dependency_receipt_hash),
            _valid_sha256(request.source_operator_completion_certification_id),
            request.runtime_namespace == RUNTIME_NAMESPACE,
            request.mode in _ALLOWED_MODES,
            isinstance(request.query_text, str),
            bool(request.query_text),
            request.query_text == " ".join(request.query_text.split()),
            isinstance(request.requested_at, datetime),
            request.requested_at.tzinfo is not None,
            request.requested_at.utcoffset() is not None,
            request.read_only_required,
            request.deterministic_required,
            request.immutable_result_required,
            request.request_type == OOR_002_REQUEST_TYPE,
            request.request_status == OOR_002_REQUEST_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "OOR-002 request contract is incomplete"
            )

        forbidden = (
            request.runtime_serving_allowed,
            request.network_listener_allowed,
            request.database_connection_allowed,
            request.publication_allowed,
            request.qseries_handoff_allowed,
            request.qseries_execution_allowed,
            request.order_creation_allowed,
            request.funds_movement_allowed,
            request.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "forbidden runtime request capability detected"
            )

    def admit(
        self,
        *,
        request: OracleOperatorRuntimeRequest,
        admitted_at: datetime,
    ) -> OracleOperatorRuntimeRequestAdmission:
        self._verify_request(request)
        if not isinstance(admitted_at, datetime) or admitted_at.tzinfo is None or admitted_at.utcoffset() is None:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "admitted_at must be timezone-aware"
            )
        normalized_time = admitted_at.astimezone(timezone.utc)
        requested_time = request.requested_at.astimezone(timezone.utc)
        if normalized_time < requested_time:
            raise OracleOperatorRuntimeRequestAdmissionInvariantError(
                "admission cannot precede request"
            )

        admission_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "request_id": request.request_id,
                "request_hash": request.request_hash,
                "admitted_at": normalized_time,
                "admission_type": ADMISSION_TYPE,
            }
        )
        body = {
            "admission_id": admission_id,
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "dependency_receipt_id": request.dependency_receipt_id,
            "dependency_receipt_hash": request.dependency_receipt_hash,
            "source_operator_completion_certification_id": request.source_operator_completion_certification_id,
            "runtime_namespace": request.runtime_namespace,
            "requester_id": request.requester_id,
            "correlation_id": request.correlation_id,
            "mode": request.mode,
            "query_text": request.query_text,
            "requested_at": requested_time,
            "admitted_at": normalized_time,
            "request_identity_verified": True,
            "request_hash_verified": True,
            "request_contract_verified": True,
            "request_mode_verified": True,
            "request_text_verified": True,
            "read_only_boundary_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_result_boundary_verified": True,
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
        return OracleOperatorRuntimeRequestAdmission(
            **body,
            admission_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "ADMISSION_TYPE",
    "ADMISSION_STATUS",
    "OracleOperatorRuntimeRequestAdmission",
    "OracleOperatorRuntimeRequestAdmissionGate",
    "OracleOperatorRuntimeRequestAdmissionInvariantError",
    "stable_hash",
]
'''

TEST_SOURCE = r'''from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_contract import (
    REQUEST_STATUS,
    REQUEST_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeRequest,
    stable_hash as request_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_admission_gate import (
    ADMISSION_STATUS,
    ADMISSION_TYPE,
    OracleOperatorRuntimeRequestAdmissionGate,
    OracleOperatorRuntimeRequestAdmissionInvariantError,
    stable_hash,
)


def _request() -> OracleOperatorRuntimeRequest:
    requested_at = datetime(2026, 7, 28, 4, 0, tzinfo=timezone.utc)
    body = {
        "request_id": request_hash({"request": "oor-002-test"}),
        "dependency_receipt_id": request_hash({"receipt": "oor-001-test"}),
        "dependency_receipt_hash": request_hash({"receipt_hash": "oor-001-test"}),
        "source_operator_completion_certification_id": request_hash({"certification": "oop-047"}),
        "runtime_namespace": RUNTIME_NAMESPACE,
        "requester_id": "operator.console",
        "correlation_id": "oracle-request-0002",
        "mode": "query",
        "query_text": "Show the highest-priority certified opportunity.",
        "requested_at": requested_at,
        "read_only_required": True,
        "deterministic_required": True,
        "immutable_result_required": True,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "request_type": REQUEST_TYPE,
        "request_status": REQUEST_STATUS,
    }
    return OracleOperatorRuntimeRequest(**body, request_hash=request_hash(body))


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime request admission accepted")
    except OracleOperatorRuntimeRequestAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-003 TEST")
    print(" ORACLE OPERATOR RUNTIME REQUEST")
    print(" ADMISSION GATE")
    print("=" * 40)

    request = _request()
    gate = OracleOperatorRuntimeRequestAdmissionGate()
    admitted_at = request.requested_at + timedelta(seconds=1)

    first = gate.admit(request=request, admitted_at=admitted_at)
    repeated = gate.admit(request=request, admitted_at=admitted_at)

    assert first == repeated
    assert first.admission_type == ADMISSION_TYPE
    assert first.admission_status == ADMISSION_STATUS
    assert first.request_id == request.request_id
    assert first.request_hash == request.request_hash
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.request_identity_verified
    assert first.request_hash_verified
    assert first.request_contract_verified
    assert first.request_mode_verified
    assert first.request_text_verified
    assert first.read_only_boundary_verified
    assert first.deterministic_boundary_verified
    assert first.immutable_result_boundary_verified
    assert first.admission_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "admission_hash"}
    )

    forbidden = (
        first.runtime_serving_allowed,
        first.network_listener_allowed,
        first.database_connection_allowed,
        first.publication_allowed,
        first.qseries_handoff_allowed,
        first.qseries_execution_allowed,
        first.order_creation_allowed,
        first.funds_movement_allowed,
        first.portfolio_mutation_allowed,
    )
    assert not any(forbidden)

    _reject(lambda: gate.admit(
        request=replace(request, request_hash="0" * 64),
        admitted_at=admitted_at,
    ))
    _reject(lambda: gate.admit(
        request=replace(request, mode="execute", request_hash=request.request_hash),
        admitted_at=admitted_at,
    ))
    _reject(lambda: gate.admit(
        request=replace(request, qseries_execution_allowed=True, request_hash=request.request_hash),
        admitted_at=admitted_at,
    ))
    _reject(lambda: gate.admit(
        request=request,
        admitted_at=request.requested_at - timedelta(seconds=1),
    ))
    _reject(lambda: gate.admit(
        request=request,
        admitted_at=datetime(2026, 7, 28, 4, 0),
    ))

    print("[PASS] Actual OOR-002 canonical runtime request consumed")
    print("[PASS] Request identity and payload hash verified")
    print("[PASS] Query, session, console, and presentation modes bounded")
    print("[PASS] Deterministic single-request admission certified")
    print("[PASS] Immutable read-only runtime boundary preserved")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe admissions rejected")
    print("[DONE] OOR-003 ORACLE OPERATOR RUNTIME REQUEST ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _verify_oor_002() -> None:
    if not SOURCE_002.is_file():
        raise RuntimeError(f"Actual OOR-002 module missing: {SOURCE_002}")
    tree = ast.parse(SOURCE_002.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    required = {
        "OracleOperatorRuntimeRequest",
        "OracleOperatorRuntimeRequestContract",
        "stable_hash",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"OOR-002 contract incomplete: {missing}")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8", newline="\n")


def _update_init() -> None:
    if not RUNTIME_INIT.exists():
        _write(RUNTIME_INIT, "from __future__ import annotations\n")
    line = (
        "from qseries_v2.oracle_operator_runtime."
        "oracle_operator_runtime_request_admission_gate import ("
        "OracleOperatorRuntimeRequestAdmission, "
        "OracleOperatorRuntimeRequestAdmissionGate, "
        "OracleOperatorRuntimeRequestAdmissionInvariantError)"
    )
    current = RUNTIME_INIT.read_text(encoding="utf-8")
    if line not in current:
        with RUNTIME_INIT.open("a", encoding="utf-8", newline="\n") as handle:
            if current and not current.endswith("\n"):
                handle.write("\n")
            handle.write(line + "\n")


def main() -> int:
    print("=" * 40)
    print(" OOR-003 INSTALLER")
    print(" ORACLE OPERATOR RUNTIME REQUEST")
    print(" ADMISSION GATE")
    print("=" * 40)
    try:
        _verify_oor_002()
        print("[OK] Actual OOR-002 runtime request contract verified")
        _write(PRODUCTION, PRODUCTION_SOURCE)
        _write(TEST, TEST_SOURCE)
        _update_init()
        print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
        print(f"[OK] FULL REPLACEMENT: {TEST}")
        print(f"[OK] PACKAGE UPDATED: {RUNTIME_INIT}")
        subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=True)
        print("[DONE] OOR-003 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
