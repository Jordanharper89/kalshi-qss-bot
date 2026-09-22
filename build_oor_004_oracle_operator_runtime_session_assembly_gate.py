from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
RUNTIME = QSERIES / "oracle_operator_runtime"
SOURCE_003 = RUNTIME / "oracle_operator_runtime_request_admission_gate.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_session_assembly_gate.py"
TEST = ROOT / "test_oor_004_oracle_operator_runtime_session_assembly_gate.py"
RUNTIME_INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_admission_gate import (
    ADMISSION_STATUS as OOR_003_ADMISSION_STATUS,
    ADMISSION_TYPE as OOR_003_ADMISSION_TYPE,
    OracleOperatorRuntimeRequestAdmission,
)

SCHEMA_VERSION = "OOR-004"
ENGINE_ID = "OOR-004"
POLICY_ID = "oracle.operator-runtime-session-assembly-gate.v1"
SESSION_TYPE = "oracle_operator_runtime_read_only_session"
SESSION_STATUS = "oracle_operator_runtime_session_assembled"


class OracleOperatorRuntimeSessionAssemblyInvariantError(ValueError):
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
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionAssemblyInvariantError(
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
class OracleOperatorRuntimeSession:
    session_id: str
    admission_id: str
    admission_hash: str
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
    assembled_at: datetime
    request_identity_verified: bool
    admission_identity_verified: bool
    admission_hash_verified: bool
    admission_contract_verified: bool
    single_request_scope_verified: bool
    single_session_scope_verified: bool
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
    session_type: str
    session_status: str
    session_hash: str


class OracleOperatorRuntimeSessionAssemblyGate:
    @staticmethod
    def _verify_admission(admission: OracleOperatorRuntimeRequestAdmission) -> None:
        if not isinstance(admission, OracleOperatorRuntimeRequestAdmission):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "admission must be canonical OOR-003 request admission"
            )

        body = asdict(admission)
        supplied_hash = body.pop("admission_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "OOR-003 admission hash mismatch"
            )

        required = (
            _valid_sha256(admission.admission_id),
            _valid_sha256(admission.request_id),
            _valid_sha256(admission.request_hash),
            _valid_sha256(admission.dependency_receipt_id),
            _valid_sha256(admission.dependency_receipt_hash),
            _valid_sha256(admission.source_operator_completion_certification_id),
            isinstance(admission.runtime_namespace, str),
            bool(admission.runtime_namespace),
            isinstance(admission.requester_id, str),
            bool(admission.requester_id),
            isinstance(admission.correlation_id, str),
            bool(admission.correlation_id),
            admission.mode in {"query", "session", "console", "presentation"},
            isinstance(admission.query_text, str),
            bool(admission.query_text),
            isinstance(admission.requested_at, datetime),
            admission.requested_at.tzinfo is not None,
            admission.requested_at.utcoffset() is not None,
            isinstance(admission.admitted_at, datetime),
            admission.admitted_at.tzinfo is not None,
            admission.admitted_at.utcoffset() is not None,
            admission.admitted_at.astimezone(timezone.utc)
            >= admission.requested_at.astimezone(timezone.utc),
            admission.request_identity_verified,
            admission.request_hash_verified,
            admission.request_contract_verified,
            admission.request_mode_verified,
            admission.request_text_verified,
            admission.read_only_boundary_verified,
            admission.deterministic_boundary_verified,
            admission.immutable_result_boundary_verified,
            admission.admission_type == OOR_003_ADMISSION_TYPE,
            admission.admission_status == OOR_003_ADMISSION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "OOR-003 admission contract is incomplete"
            )

        forbidden = (
            admission.runtime_serving_allowed,
            admission.network_listener_allowed,
            admission.database_connection_allowed,
            admission.publication_allowed,
            admission.qseries_handoff_allowed,
            admission.qseries_execution_allowed,
            admission.order_creation_allowed,
            admission.funds_movement_allowed,
            admission.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "forbidden runtime capability detected"
            )

    def assemble(
        self,
        *,
        admission: OracleOperatorRuntimeRequestAdmission,
        assembled_at: datetime,
    ) -> OracleOperatorRuntimeSession:
        self._verify_admission(admission)
        if (
            not isinstance(assembled_at, datetime)
            or assembled_at.tzinfo is None
            or assembled_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "assembled_at must be timezone-aware"
            )

        normalized_time = assembled_at.astimezone(timezone.utc)
        admitted_time = admission.admitted_at.astimezone(timezone.utc)
        if normalized_time < admitted_time:
            raise OracleOperatorRuntimeSessionAssemblyInvariantError(
                "session assembly cannot precede admission"
            )

        session_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "admission_id": admission.admission_id,
                "admission_hash": admission.admission_hash,
                "assembled_at": normalized_time,
                "session_type": SESSION_TYPE,
            }
        )
        body = {
            "session_id": session_id,
            "admission_id": admission.admission_id,
            "admission_hash": admission.admission_hash,
            "request_id": admission.request_id,
            "request_hash": admission.request_hash,
            "dependency_receipt_id": admission.dependency_receipt_id,
            "dependency_receipt_hash": admission.dependency_receipt_hash,
            "source_operator_completion_certification_id": admission.source_operator_completion_certification_id,
            "runtime_namespace": admission.runtime_namespace,
            "requester_id": admission.requester_id,
            "correlation_id": admission.correlation_id,
            "mode": admission.mode,
            "query_text": admission.query_text,
            "requested_at": admission.requested_at.astimezone(timezone.utc),
            "admitted_at": admitted_time,
            "assembled_at": normalized_time,
            "request_identity_verified": True,
            "admission_identity_verified": True,
            "admission_hash_verified": True,
            "admission_contract_verified": True,
            "single_request_scope_verified": True,
            "single_session_scope_verified": True,
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
            "session_type": SESSION_TYPE,
            "session_status": SESSION_STATUS,
        }
        return OracleOperatorRuntimeSession(
            **body,
            session_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "SESSION_TYPE",
    "SESSION_STATUS",
    "OracleOperatorRuntimeSession",
    "OracleOperatorRuntimeSessionAssemblyGate",
    "OracleOperatorRuntimeSessionAssemblyInvariantError",
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
    OracleOperatorRuntimeRequestAdmission,
    stable_hash as admission_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_assembly_gate import (
    SESSION_STATUS,
    SESSION_TYPE,
    OracleOperatorRuntimeSessionAssemblyGate,
    OracleOperatorRuntimeSessionAssemblyInvariantError,
    stable_hash,
)


def _request() -> OracleOperatorRuntimeRequest:
    requested_at = datetime(2026, 7, 28, 5, 0, tzinfo=timezone.utc)
    body = {
        "request_id": request_hash({"request": "oor-004-test"}),
        "dependency_receipt_id": request_hash({"receipt": "oor-001-test"}),
        "dependency_receipt_hash": request_hash({"receipt_hash": "oor-001-test"}),
        "source_operator_completion_certification_id": request_hash({"certification": "oop-047"}),
        "runtime_namespace": RUNTIME_NAMESPACE,
        "requester_id": "operator.console",
        "correlation_id": "oracle-session-0004",
        "mode": "session",
        "query_text": "Assemble a certified read-only operator session.",
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


def _admission() -> OracleOperatorRuntimeRequestAdmission:
    request = _request()
    admitted_at = request.requested_at + timedelta(seconds=1)
    admission_id = admission_hash({
        "engine_id": "OOR-003",
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "admitted_at": admitted_at,
        "admission_type": ADMISSION_TYPE,
    })
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
        "requested_at": request.requested_at,
        "admitted_at": admitted_at,
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
        admission_hash=admission_hash(body),
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime session assembly accepted")
    except OracleOperatorRuntimeSessionAssemblyInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-004 TEST")
    print(" ORACLE OPERATOR RUNTIME SESSION")
    print(" ASSEMBLY GATE")
    print("=" * 40)

    admission = _admission()
    gate = OracleOperatorRuntimeSessionAssemblyGate()
    assembled_at = admission.admitted_at + timedelta(seconds=1)

    first = gate.assemble(admission=admission, assembled_at=assembled_at)
    repeated = gate.assemble(admission=admission, assembled_at=assembled_at)

    assert first == repeated
    assert first.session_type == SESSION_TYPE
    assert first.session_status == SESSION_STATUS
    assert first.admission_id == admission.admission_id
    assert first.admission_hash == admission.admission_hash
    assert first.request_id == admission.request_id
    assert first.request_hash == admission.request_hash
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.request_identity_verified
    assert first.admission_identity_verified
    assert first.admission_hash_verified
    assert first.admission_contract_verified
    assert first.single_request_scope_verified
    assert first.single_session_scope_verified
    assert first.read_only_boundary_verified
    assert first.deterministic_boundary_verified
    assert first.immutable_result_boundary_verified
    assert first.session_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "session_hash"}
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

    _reject(lambda: gate.assemble(
        admission=replace(admission, admission_hash="0" * 64),
        assembled_at=assembled_at,
    ))
    _reject(lambda: gate.assemble(
        admission=replace(admission, admission_status="revoked", admission_hash=admission.admission_hash),
        assembled_at=assembled_at,
    ))
    _reject(lambda: gate.assemble(
        admission=replace(admission, qseries_execution_allowed=True, admission_hash=admission.admission_hash),
        assembled_at=assembled_at,
    ))
    _reject(lambda: gate.assemble(
        admission=admission,
        assembled_at=admission.admitted_at - timedelta(seconds=1),
    ))
    _reject(lambda: gate.assemble(
        admission=admission,
        assembled_at=datetime(2026, 7, 28, 5, 0),
    ))

    print("[PASS] Actual OOR-003 request admission consumed")
    print("[PASS] Admission identity and payload hash verified")
    print("[PASS] Complete OOR-001 through OOR-003 lineage preserved")
    print("[PASS] Deterministic single-session assembly certified")
    print("[PASS] Immutable read-only runtime session materialized")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe session assembly rejected")
    print("[DONE] OOR-004 ORACLE OPERATOR RUNTIME SESSION ASSEMBLY GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _verify_oor_003() -> None:
    if not SOURCE_003.is_file():
        raise RuntimeError(f"Actual OOR-003 module missing: {SOURCE_003}")
    tree = ast.parse(SOURCE_003.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    required = {
        "OracleOperatorRuntimeRequestAdmission",
        "OracleOperatorRuntimeRequestAdmissionGate",
        "stable_hash",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"OOR-003 contract incomplete: {missing}")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8", newline="\n")


def _update_init() -> None:
    if not RUNTIME_INIT.exists():
        _write(RUNTIME_INIT, "from __future__ import annotations\n")
    line = (
        "from qseries_v2.oracle_operator_runtime."
        "oracle_operator_runtime_session_assembly_gate import ("
        "OracleOperatorRuntimeSession, "
        "OracleOperatorRuntimeSessionAssemblyGate, "
        "OracleOperatorRuntimeSessionAssemblyInvariantError)"
    )
    current = RUNTIME_INIT.read_text(encoding="utf-8")
    if line not in current:
        with RUNTIME_INIT.open("a", encoding="utf-8", newline="\n") as handle:
            if current and not current.endswith("\n"):
                handle.write("\n")
            handle.write(line + "\n")


def main() -> int:
    print("=" * 40)
    print(" OOR-004 INSTALLER")
    print(" ORACLE OPERATOR RUNTIME SESSION")
    print(" ASSEMBLY GATE")
    print("=" * 40)
    try:
        _verify_oor_003()
        print("[OK] Actual OOR-003 request admission contract verified")
        _write(PRODUCTION, PRODUCTION_SOURCE)
        _write(TEST, TEST_SOURCE)
        _update_init()
        print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
        print(f"[OK] FULL REPLACEMENT: {TEST}")
        print(f"[OK] PACKAGE UPDATED: {RUNTIME_INIT}")
        subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=True)
        print("[DONE] OOR-004 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
