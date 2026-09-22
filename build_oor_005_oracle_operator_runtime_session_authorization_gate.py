from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QSERIES = ROOT / "qseries_v2"
RUNTIME = QSERIES / "oracle_operator_runtime"
SOURCE_004 = RUNTIME / "oracle_operator_runtime_session_assembly_gate.py"
PRODUCTION = RUNTIME / "oracle_operator_runtime_session_authorization_gate.py"
TEST = ROOT / "test_oor_005_oracle_operator_runtime_session_authorization_gate.py"
RUNTIME_INIT = RUNTIME / "__init__.py"

PRODUCTION_SOURCE = r'''from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_assembly_gate import (
    SESSION_STATUS as OOR_004_SESSION_STATUS,
    SESSION_TYPE as OOR_004_SESSION_TYPE,
    OracleOperatorRuntimeSession,
)

SCHEMA_VERSION = "OOR-005"
ENGINE_ID = "OOR-005"
POLICY_ID = "oracle.operator-runtime-session-authorization-gate.v1"
AUTHORIZATION_TYPE = "oracle_operator_runtime_read_only_session_authorization"
AUTHORIZATION_STATUS = "oracle_operator_runtime_session_authorized"


class OracleOperatorRuntimeSessionAuthorizationInvariantError(ValueError):
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
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
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
class OracleOperatorRuntimeSessionAuthorization:
    authorization_id: str
    session_id: str
    session_hash: str
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
    authorized_at: datetime
    session_identity_verified: bool
    session_hash_verified: bool
    session_contract_verified: bool
    single_session_scope_verified: bool
    single_authorization_scope_verified: bool
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
    authorization_type: str
    authorization_status: str
    authorization_hash: str


class OracleOperatorRuntimeSessionAuthorizationGate:
    @staticmethod
    def _verify_session(session: OracleOperatorRuntimeSession) -> None:
        if not isinstance(session, OracleOperatorRuntimeSession):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "session must be canonical OOR-004 runtime session"
            )

        body = asdict(session)
        supplied_hash = body.pop("session_hash", None)
        if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "OOR-004 session hash mismatch"
            )

        required = (
            _valid_sha256(session.session_id),
            _valid_sha256(session.admission_id),
            _valid_sha256(session.admission_hash),
            _valid_sha256(session.request_id),
            _valid_sha256(session.request_hash),
            _valid_sha256(session.dependency_receipt_id),
            _valid_sha256(session.dependency_receipt_hash),
            _valid_sha256(session.source_operator_completion_certification_id),
            isinstance(session.runtime_namespace, str),
            bool(session.runtime_namespace),
            isinstance(session.requester_id, str),
            bool(session.requester_id),
            isinstance(session.correlation_id, str),
            bool(session.correlation_id),
            session.mode in {"query", "session", "console", "presentation"},
            isinstance(session.query_text, str),
            bool(session.query_text),
            isinstance(session.requested_at, datetime),
            session.requested_at.tzinfo is not None,
            session.requested_at.utcoffset() is not None,
            isinstance(session.admitted_at, datetime),
            session.admitted_at.tzinfo is not None,
            session.admitted_at.utcoffset() is not None,
            isinstance(session.assembled_at, datetime),
            session.assembled_at.tzinfo is not None,
            session.assembled_at.utcoffset() is not None,
            session.admitted_at.astimezone(timezone.utc)
            >= session.requested_at.astimezone(timezone.utc),
            session.assembled_at.astimezone(timezone.utc)
            >= session.admitted_at.astimezone(timezone.utc),
            session.request_identity_verified,
            session.admission_identity_verified,
            session.admission_hash_verified,
            session.admission_contract_verified,
            session.single_request_scope_verified,
            session.single_session_scope_verified,
            session.read_only_boundary_verified,
            session.deterministic_boundary_verified,
            session.immutable_result_boundary_verified,
            session.session_type == OOR_004_SESSION_TYPE,
            session.session_status == OOR_004_SESSION_STATUS,
        )
        if not all(required):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "OOR-004 session contract is incomplete"
            )

        forbidden = (
            session.runtime_serving_allowed,
            session.network_listener_allowed,
            session.database_connection_allowed,
            session.publication_allowed,
            session.qseries_handoff_allowed,
            session.qseries_execution_allowed,
            session.order_creation_allowed,
            session.funds_movement_allowed,
            session.portfolio_mutation_allowed,
        )
        if any(forbidden):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "forbidden runtime capability detected"
            )

    def authorize(
        self,
        *,
        session: OracleOperatorRuntimeSession,
        authorized_at: datetime,
    ) -> OracleOperatorRuntimeSessionAuthorization:
        self._verify_session(session)
        if (
            not isinstance(authorized_at, datetime)
            or authorized_at.tzinfo is None
            or authorized_at.utcoffset() is None
        ):
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "authorized_at must be timezone-aware"
            )

        normalized_time = authorized_at.astimezone(timezone.utc)
        assembled_time = session.assembled_at.astimezone(timezone.utc)
        if normalized_time < assembled_time:
            raise OracleOperatorRuntimeSessionAuthorizationInvariantError(
                "session authorization cannot precede assembly"
            )

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "session_id": session.session_id,
                "session_hash": session.session_hash,
                "authorized_at": normalized_time,
                "authorization_type": AUTHORIZATION_TYPE,
            }
        )
        body = {
            "authorization_id": authorization_id,
            "session_id": session.session_id,
            "session_hash": session.session_hash,
            "admission_id": session.admission_id,
            "admission_hash": session.admission_hash,
            "request_id": session.request_id,
            "request_hash": session.request_hash,
            "dependency_receipt_id": session.dependency_receipt_id,
            "dependency_receipt_hash": session.dependency_receipt_hash,
            "source_operator_completion_certification_id": session.source_operator_completion_certification_id,
            "runtime_namespace": session.runtime_namespace,
            "requester_id": session.requester_id,
            "correlation_id": session.correlation_id,
            "mode": session.mode,
            "query_text": session.query_text,
            "requested_at": session.requested_at.astimezone(timezone.utc),
            "admitted_at": session.admitted_at.astimezone(timezone.utc),
            "assembled_at": assembled_time,
            "authorized_at": normalized_time,
            "session_identity_verified": True,
            "session_hash_verified": True,
            "session_contract_verified": True,
            "single_session_scope_verified": True,
            "single_authorization_scope_verified": True,
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
            "authorization_type": AUTHORIZATION_TYPE,
            "authorization_status": AUTHORIZATION_STATUS,
        }
        return OracleOperatorRuntimeSessionAuthorization(
            **body,
            authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_TYPE",
    "AUTHORIZATION_STATUS",
    "OracleOperatorRuntimeSessionAuthorization",
    "OracleOperatorRuntimeSessionAuthorizationGate",
    "OracleOperatorRuntimeSessionAuthorizationInvariantError",
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
    OracleOperatorRuntimeSession,
    stable_hash as session_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    OracleOperatorRuntimeSessionAuthorizationGate,
    OracleOperatorRuntimeSessionAuthorizationInvariantError,
    stable_hash,
)


def _request() -> OracleOperatorRuntimeRequest:
    requested_at = datetime(2026, 7, 28, 6, 0, tzinfo=timezone.utc)
    body = {
        "request_id": request_hash({"request": "oor-005-test"}),
        "dependency_receipt_id": request_hash({"receipt": "oor-001-test"}),
        "dependency_receipt_hash": request_hash({"receipt_hash": "oor-001-test"}),
        "source_operator_completion_certification_id": request_hash({"certification": "oop-047"}),
        "runtime_namespace": RUNTIME_NAMESPACE,
        "requester_id": "operator.console",
        "correlation_id": "oracle-session-0005",
        "mode": "session",
        "query_text": "Authorize a certified read-only operator runtime session.",
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
    return OracleOperatorRuntimeRequestAdmission(**body, admission_hash=admission_hash(body))


def _session() -> OracleOperatorRuntimeSession:
    admission = _admission()
    assembled_at = admission.admitted_at + timedelta(seconds=1)
    session_id = session_hash({
        "engine_id": "OOR-004",
        "admission_id": admission.admission_id,
        "admission_hash": admission.admission_hash,
        "assembled_at": assembled_at,
        "session_type": SESSION_TYPE,
    })
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
        "requested_at": admission.requested_at,
        "admitted_at": admission.admitted_at,
        "assembled_at": assembled_at,
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
    return OracleOperatorRuntimeSession(**body, session_hash=session_hash(body))


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime session authorization accepted")
    except OracleOperatorRuntimeSessionAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-005 TEST")
    print(" ORACLE OPERATOR RUNTIME SESSION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    session = _session()
    gate = OracleOperatorRuntimeSessionAuthorizationGate()
    authorized_at = session.assembled_at + timedelta(seconds=1)

    first = gate.authorize(session=session, authorized_at=authorized_at)
    repeated = gate.authorize(session=session, authorized_at=authorized_at)

    assert first == repeated
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert first.session_id == session.session_id
    assert first.session_hash == session.session_hash
    assert first.request_id == session.request_id
    assert first.request_hash == session.request_hash
    assert first.session_identity_verified
    assert first.session_hash_verified
    assert first.session_contract_verified
    assert first.single_session_scope_verified
    assert first.single_authorization_scope_verified
    assert first.read_only_boundary_verified
    assert first.deterministic_boundary_verified
    assert first.immutable_result_boundary_verified
    assert first.authorization_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "authorization_hash"}
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

    _reject(lambda: gate.authorize(
        session=replace(session, session_hash="0" * 64),
        authorized_at=authorized_at,
    ))
    _reject(lambda: gate.authorize(
        session=replace(session, session_status="revoked", session_hash=session.session_hash),
        authorized_at=authorized_at,
    ))
    _reject(lambda: gate.authorize(
        session=replace(session, publication_allowed=True, session_hash=session.session_hash),
        authorized_at=authorized_at,
    ))
    _reject(lambda: gate.authorize(
        session=session,
        authorized_at=session.assembled_at - timedelta(seconds=1),
    ))
    _reject(lambda: gate.authorize(
        session=session,
        authorized_at=datetime(2026, 7, 28, 6, 0),
    ))

    print("[PASS] Actual OOR-004 runtime session consumed")
    print("[PASS] Session identity and payload hash verified")
    print("[PASS] Complete OOR-001 through OOR-004 lineage preserved")
    print("[PASS] Deterministic single-session authorization certified")
    print("[PASS] Immutable read-only runtime authorization materialized")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe authorization rejected")
    print("[DONE] OOR-005 ORACLE OPERATOR RUNTIME SESSION AUTHORIZATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _verify_oor_004() -> None:
    if not SOURCE_004.is_file():
        raise RuntimeError(f"Actual OOR-004 module missing: {SOURCE_004}")
    tree = ast.parse(SOURCE_004.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    required = {
        "OracleOperatorRuntimeSession",
        "OracleOperatorRuntimeSessionAssemblyGate",
        "stable_hash",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"OOR-004 contract incomplete: {missing}")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip(), encoding="utf-8", newline="\n")


def _update_init() -> None:
    if not RUNTIME_INIT.exists():
        _write(RUNTIME_INIT, "from __future__ import annotations\n")
    line = (
        "from qseries_v2.oracle_operator_runtime."
        "oracle_operator_runtime_session_authorization_gate import ("
        "OracleOperatorRuntimeSessionAuthorization, "
        "OracleOperatorRuntimeSessionAuthorizationGate, "
        "OracleOperatorRuntimeSessionAuthorizationInvariantError)"
    )
    current = RUNTIME_INIT.read_text(encoding="utf-8")
    if line not in current:
        with RUNTIME_INIT.open("a", encoding="utf-8", newline="\n") as handle:
            if current and not current.endswith("\n"):
                handle.write("\n")
            handle.write(line + "\n")


def main() -> int:
    print("=" * 40)
    print(" OOR-005 INSTALLER")
    print(" ORACLE OPERATOR RUNTIME SESSION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)
    try:
        _verify_oor_004()
        print("[OK] Actual OOR-004 runtime session contract verified")
        _write(PRODUCTION, PRODUCTION_SOURCE)
        _write(TEST, TEST_SOURCE)
        _update_init()
        print(f"[OK] FULL REPLACEMENT: {PRODUCTION}")
        print(f"[OK] FULL REPLACEMENT: {TEST}")
        print(f"[OK] PACKAGE UPDATED: {RUNTIME_INIT}")
        subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=True)
        print("[DONE] OOR-005 INSTALLED AND VERIFIED")
        return 0
    except (RuntimeError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
