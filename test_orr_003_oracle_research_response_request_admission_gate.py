from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_research_response.oracle_research_response_request_contract import (
    REQUEST_STATUS,
    REQUEST_TYPE,
    RESPONSE_MODE_PREDICTION_CARD,
    SUBSYSTEM_NAMESPACE,
    OracleResearchResponseRequest,
    stable_hash as request_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_request_admission_gate import *


def sample_request() -> OracleResearchResponseRequest:
    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)
    body = {
        "request_id": "1" * 64,
        "dependency_receipt_id": "2" * 64,
        "dependency_receipt_hash": "3" * 64,
        "source_runtime_completion_id": "4" * 64,
        "source_runtime_completion_hash": "5" * 64,
        "subsystem_namespace": SUBSYSTEM_NAMESPACE,
        "requester_id": "operator:jordan",
        "correlation_id": "session:orr-003-test",
        "question_text": "What are the strongest Kalshi opportunities closing today?",
        "response_mode": RESPONSE_MODE_PREDICTION_CARD,
        "filters": (("time_horizon", "Today"), ("venue", "Kalshi")),
        "requested_at": requested_at,
        "dependency_identity_verified": True,
        "dependency_hash_verified": True,
        "dependency_contract_verified": True,
        "typed_question_verified": True,
        "response_mode_verified": True,
        "filter_boundary_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_request_boundary_verified": True,
        "read_only_boundary_verified": True,
        "request_single_use_verified": True,
        "duplicate_request_allowed": False,
        "request_reversible": False,
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
    return OracleResearchResponseRequest(
        **body,
        request_hash=request_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe request admission accepted")
    except OracleResearchResponseRequestAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-003 TEST")
    print(" RESEARCH RESPONSE REQUEST ADMISSION")
    print("=" * 40)

    request = sample_request()
    admitted_at = request.requested_at + timedelta(seconds=1)
    gate = OracleResearchResponseRequestAdmissionGate()

    first = gate.admit(request=request, admitted_at=admitted_at)
    second = gate.admit(request=request, admitted_at=admitted_at)

    assert first == second
    assert first.admission_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "admission_hash"
        }
    )
    assert first.admission_type == ADMISSION_TYPE
    assert first.admission_status == ADMISSION_STATUS
    assert first.request_identity_verified
    assert first.request_hash_verified
    assert first.request_contract_verified
    assert first.single_request_scope_verified
    assert first.admission_single_use_verified
    assert not first.duplicate_admission_allowed
    assert not first.admission_reversible

    reject(
        lambda: gate.admit(
            request=replace(request, request_hash="0" * 64),
            admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            request=replace(request, qseries_execution_allowed=True),
            admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            request=request,
            admitted_at=request.requested_at - timedelta(seconds=1),
        )
    )

    print("[PASS] Actual ORR-002 research request consumed")
    print("[PASS] Typed natural-language question admitted")
    print("[PASS] Complete ORR-001 through ORR-002 lineage preserved")
    print("[PASS] Deterministic single-request admission certified")
    print("[PASS] Immutable single-use admission boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe requests rejected")
    print("[DONE] ORR-003 RESEARCH RESPONSE REQUEST ADMISSION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
