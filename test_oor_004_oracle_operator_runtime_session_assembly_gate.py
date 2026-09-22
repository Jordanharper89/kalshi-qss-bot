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
