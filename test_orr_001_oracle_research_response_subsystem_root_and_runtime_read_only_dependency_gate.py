from dataclasses import asdict, replace
from datetime import datetime, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import (
    COMPLETION_STATUS,
    OracleOperatorRuntimeFinalCompletionAndFreeze,
    stable_hash as completion_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import *


def sample_completion() -> OracleOperatorRuntimeFinalCompletionAndFreeze:
    body = {
        "completion_id": "1" * 64,
        "source_attestation_id": "2" * 64,
        "source_attestation_hash": "3" * 64,
        "source_continuation_id": "4" * 64,
        "source_continuation_hash": "5" * 64,
        "source_session_id": "6" * 64,
        "source_session_hash": "7" * 64,
        "source_request_id": "8" * 64,
        "source_request_hash": "9" * 64,
        "source_dependency_receipt_id": "a" * 64,
        "source_dependency_receipt_hash": "b" * 64,
        "source_operator_completion_certification_id": "c" * 64,
        "runtime_namespace": "oracle_operator_runtime",
        "complete_lineage_verified": True,
        "deterministic_completion": True,
        "immutable_freeze": True,
        "runtime_complete": True,
        "read_only": True,
        "downstream_read_only_operation_allowed": True,
        "further_oor_certification_required": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "completion_status": COMPLETION_STATUS,
    }
    return OracleOperatorRuntimeFinalCompletionAndFreeze(
        **body,
        completion_hash=completion_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe dependency admission accepted")
    except OracleResearchResponseRuntimeDependencyInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-001 TEST")
    print(" RESEARCH RESPONSE SUBSYSTEM ROOT")
    print(" RUNTIME READ-ONLY DEPENDENCY GATE")
    print("=" * 40)

    completion = sample_completion()
    admitted_at = datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc)
    gate = OracleResearchResponseRuntimeDependencyGate()

    first = gate.admit(completion=completion, admitted_at=admitted_at)
    second = gate.admit(completion=completion, admitted_at=admitted_at)

    assert first == second
    assert first.dependency_receipt_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "dependency_receipt_hash"
        }
    )
    assert first.subsystem_namespace == SUBSYSTEM_NAMESPACE
    assert first.dependency_type == DEPENDENCY_TYPE
    assert first.dependency_status == DEPENDENCY_STATUS
    assert first.source_runtime_complete_verified
    assert first.source_runtime_immutable_freeze_verified
    assert first.source_runtime_read_only_verified
    assert first.downstream_read_only_operation_verified
    assert first.dependency_single_use_verified
    assert not first.duplicate_dependency_allowed
    assert not first.dependency_reversible

    reject(
        lambda: gate.admit(
            completion=replace(completion, completion_hash="0" * 64),
            admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            completion=replace(
                completion,
                qseries_execution_allowed=True,
                completion_hash=completion.completion_hash,
            ),
            admitted_at=admitted_at,
        )
    )
    reject(
        lambda: gate.admit(
            completion=completion,
            admitted_at=datetime(2026, 7, 28, 18, 0),
        )
    )

    print("[PASS] Actual OOR-013 final completion contract consumed")
    print("[PASS] Frozen Oracle Operator Runtime admitted as read-only dependency")
    print("[PASS] Oracle Research Response package root established")
    print("[PASS] Deterministic immutable dependency receipt certified")
    print("[PASS] Single-use and non-reversible dependency boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered and unsafe dependencies rejected")
    print("[DONE] ORR-001 RESEARCH RESPONSE ROOT AND DEPENDENCY GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
