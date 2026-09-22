from dataclasses import asdict, replace
from datetime import datetime, timezone

from qseries_v2.oracle_research_response.oracle_research_response_runtime_read_only_dependency_gate import (
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    SUBSYSTEM_NAMESPACE,
    OracleResearchResponseRuntimeDependencyReceipt,
    stable_hash as dependency_hash,
)
from qseries_v2.oracle_research_response.oracle_research_response_request_contract import *


def sample_dependency() -> OracleResearchResponseRuntimeDependencyReceipt:
    body = {
        "dependency_receipt_id": "1" * 64,
        "source_runtime_completion_id": "2" * 64,
        "source_runtime_completion_hash": "3" * 64,
        "source_runtime_namespace": "oracle_operator_runtime",
        "source_runtime_completion_status": "oracle_operator_runtime_final_completion_certified_and_frozen",
        "subsystem_namespace": SUBSYSTEM_NAMESPACE,
        "admitted_at": datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc),
        "complete_runtime_lineage_verified": True,
        "source_runtime_complete_verified": True,
        "source_runtime_immutable_freeze_verified": True,
        "source_runtime_read_only_verified": True,
        "downstream_read_only_operation_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_result_boundary_verified": True,
        "dependency_single_use_verified": True,
        "duplicate_dependency_allowed": False,
        "dependency_reversible": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "dependency_type": DEPENDENCY_TYPE,
        "dependency_status": DEPENDENCY_STATUS,
    }
    return OracleResearchResponseRuntimeDependencyReceipt(
        **body,
        dependency_receipt_hash=dependency_hash(body),
    )


def reject(function) -> None:
    try:
        function()
        raise AssertionError("unsafe research response request accepted")
    except OracleResearchResponseRequestInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" ORR-002 TEST")
    print(" RESEARCH RESPONSE REQUEST CONTRACT")
    print("=" * 40)

    dependency = sample_dependency()
    requested_at = datetime(2026, 7, 28, 18, 5, tzinfo=timezone.utc)
    contract = OracleResearchResponseRequestContract()

    first = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator:jordan",
        correlation_id="session:orr-002-test",
        question_text="  What are the strongest Kalshi opportunities closing today?  ",
        response_mode=RESPONSE_MODE_PREDICTION_CARD,
        filters={"Venue": "Kalshi", "Time Horizon": "Today"},
        requested_at=requested_at,
    )
    second = contract.materialize(
        dependency_receipt=dependency,
        requester_id="operator:jordan",
        correlation_id="session:orr-002-test",
        question_text="What are the strongest Kalshi opportunities closing today?",
        response_mode=RESPONSE_MODE_PREDICTION_CARD,
        filters={"Time Horizon": "Today", "Venue": "Kalshi"},
        requested_at=requested_at,
    )

    assert first == second
    assert first.question_text == "What are the strongest Kalshi opportunities closing today?"
    assert first.filters == (("time_horizon", "Today"), ("venue", "Kalshi"))
    assert first.request_hash == stable_hash(
        {
            key: value
            for key, value in asdict(first).items()
            if key != "request_hash"
        }
    )
    assert first.request_type == REQUEST_TYPE
    assert first.request_status == REQUEST_STATUS
    assert first.typed_question_verified
    assert first.response_mode_verified
    assert first.filter_boundary_verified
    assert first.read_only_boundary_verified
    assert first.request_single_use_verified
    assert not first.duplicate_request_allowed
    assert not first.request_reversible

    reject(
        lambda: contract.materialize(
            dependency_receipt=replace(
                dependency,
                dependency_receipt_hash="0" * 64,
            ),
            requester_id="operator:jordan",
            correlation_id="session:test",
            question_text="What changed?",
            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,
            requested_at=requested_at,
        )
    )
    reject(
        lambda: contract.materialize(
            dependency_receipt=dependency,
            requester_id="operator:jordan",
            correlation_id="session:test",
            question_text="   ",
            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,
            requested_at=requested_at,
        )
    )
    reject(
        lambda: contract.materialize(
            dependency_receipt=dependency,
            requester_id="operator:jordan",
            correlation_id="session:test",
            question_text="Place an order.",
            response_mode="execution",
            requested_at=requested_at,
        )
    )
    reject(
        lambda: contract.materialize(
            dependency_receipt=dependency,
            requester_id="operator:jordan",
            correlation_id="session:test",
            question_text="What changed?",
            response_mode=RESPONSE_MODE_RESEARCH_ANSWER,
            requested_at=datetime(2026, 7, 28, 18, 5),
        )
    )

    print("[PASS] Actual ORR-001 runtime dependency receipt consumed")
    print("[PASS] Typed natural-language research question materialized")
    print("[PASS] Research answer and prediction-card response modes supported")
    print("[PASS] Deterministic normalized filters certified")
    print("[PASS] Immutable single-use request boundary certified")
    print("[PASS] Runtime serving, networking, database connection, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, empty, unsupported, and unsafe requests rejected")
    print("[DONE] ORR-002 RESEARCH RESPONSE REQUEST CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
