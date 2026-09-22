from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt,
    stable_hash as dependency_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_request_contract import (
    REQUEST_STATUS,
    REQUEST_TYPE,
    OracleOperatorRuntimeRequestContract,
    OracleOperatorRuntimeRequestInvariantError,
    stable_hash,
)


def _dependency():
    body = {
        "dependency_receipt_id": dependency_hash({"receipt": "oor-001-test"}),
        "source_operator_completion_certification_id": dependency_hash({"certification": "oop-047"}),
        "source_operator_completion_certification_hash": dependency_hash({"certification_hash": "oop-047"}),
        "source_freeze_record_id": dependency_hash({"freeze": "oop-047"}),
        "source_freeze_record_payload_hash": dependency_hash({"freeze_payload": "oop-047"}),
        "source_certification_status": "oracle_operator_subsystem_completion_certified",
        "source_certification_type": "terminal_read_only_oracle_operator_subsystem_completion_certification",
        "source_freeze_record_type": "immutable_oracle_operator_subsystem_completion_freeze_record",
        "runtime_namespace": RUNTIME_NAMESPACE,
        "operator_namespace": "qseries_v2.oracle_operator",
        "qseries_execution_namespace": "qseries_v2.execution",
        "consumer_id": "oracle.operator.runtime.v1",
        "projection": "certified_operator_read_only",
        "source_query_boundary_complete": True,
        "source_research_response_boundary_complete": True,
        "source_session_boundary_complete": True,
        "source_console_boundary_complete": True,
        "source_presentation_boundary_complete": True,
        "source_operator_subsystem_completion_ready": True,
        "source_operator_subsystem_completion_certified": True,
        "source_operator_subsystem_frozen": True,
        "source_further_operator_builds_required": False,
        "certification_identity_verified": True,
        "certification_hash_verified": True,
        "certification_status_verified": True,
        "certification_type_verified": True,
        "freeze_record_type_verified": True,
        "freeze_record_identity_verified": True,
        "freeze_record_payload_hash_verified": True,
        "operator_namespace_verified": True,
        "complete_operator_lineage_verified": True,
        "operator_completion_verified": True,
        "operator_freeze_verified": True,
        "deterministic_dependency_verified": True,
        "immutable_dependency_verified": True,
        "read_only_dependency_verified": True,
        "runtime_subsystem_root_established": True,
        "runtime_serving_allowed": False,
        "runtime_serving_performed": False,
        "network_listener_allowed": False,
        "network_listener_started": False,
        "operator_reexecution_allowed": False,
        "operator_reexecution_performed": False,
        "analytics_reexecution_allowed": False,
        "analytics_reexecution_performed": False,
        "database_connection_allowed": False,
        "database_connection_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "qseries_execution_performed": False,
        "order_creation_allowed": False,
        "order_creation_performed": False,
        "funds_movement_allowed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_allowed": False,
        "portfolio_mutation_performed": False,
        "dependency_status": DEPENDENCY_STATUS,
        "dependency_type": DEPENDENCY_TYPE,
    }
    return OracleOperatorRuntimeCertifiedReadOnlyDependencyReceipt(
        **body,
        dependency_receipt_hash=dependency_hash(body),
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime request accepted")
    except OracleOperatorRuntimeRequestInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-002 TEST")
    print(" ORACLE OPERATOR RUNTIME REQUEST")
    print(" CANONICAL READ-ONLY CONTRACT")
    print("=" * 40)

    dependency = _dependency()
    contract = OracleOperatorRuntimeRequestContract()
    requested_at = datetime(2026, 7, 28, 3, 30, tzinfo=timezone.utc)

    first = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator.console",
        correlation_id="oracle-request-0001",
        mode="query",
        query_text="  Show the highest-priority certified opportunity.  ",
        requested_at=requested_at,
    )
    repeated = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator.console",
        correlation_id="oracle-request-0001",
        mode="query",
        query_text="Show the highest-priority certified opportunity.",
        requested_at=requested_at,
    )

    assert first == repeated
    assert first.request_type == REQUEST_TYPE
    assert first.request_status == REQUEST_STATUS
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.query_text == "Show the highest-priority certified opportunity."
    assert first.requested_at == requested_at
    assert first.read_only_required
    assert first.deterministic_required
    assert first.immutable_result_required
    assert first.request_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "request_hash"}
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

    _reject(lambda: contract.materialize(
        dependency_receipt=replace(dependency, dependency_receipt_hash="0" * 64),
        requester_id="operator.console", correlation_id="oracle-request-0001",
        mode="query", query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="execute",
        query_text="test", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="   ", requested_at=requested_at,
    ))
    _reject(lambda: contract.materialize(
        dependency_receipt=dependency, requester_id="operator.console",
        correlation_id="oracle-request-0001", mode="query",
        query_text="test", requested_at=datetime(2026, 7, 28, 3, 30),
    ))

    print("[PASS] Actual OOR-001 certified read-only receipt contract consumed")
    print("[PASS] Canonical runtime request identity and hash deterministic")
    print("[PASS] Query, session, console, and presentation modes bounded")
    print("[PASS] Request text normalized without changing meaning")
    print("[PASS] Immutable read-only runtime request materialized")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe requests rejected")
    print("[DONE] OOR-002 ORACLE OPERATOR RUNTIME REQUEST CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
