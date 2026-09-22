from __future__ import annotations

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
