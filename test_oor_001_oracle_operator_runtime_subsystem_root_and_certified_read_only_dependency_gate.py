from __future__ import annotations

from dataclasses import replace

from test_oop_047_oracle_operator_subsystem_completion_certification_gate import (
    _readiness,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_certification_gate import (
    OracleOperatorSubsystemCompletionCertificationGate,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_certified_read_only_dependency_gate import (
    BOUNDARY_TYPE,
    DEPENDENCY_STATUS,
    DEPENDENCY_TYPE,
    OPERATOR_NAMESPACE,
    QSERIES_EXECUTION_NAMESPACE,
    RUNTIME_NAMESPACE,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyGate,
    OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorSubsystemCompletionCertificationGate().certify(
        readiness=_readiness()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime dependency accepted")
    except OracleOperatorRuntimeCertifiedReadOnlyDependencyInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-001 TEST")
    print(" ORACLE OPERATOR RUNTIME ROOT")
    print(" CERTIFIED READ-ONLY DEPENDENCY")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorRuntimeCertifiedReadOnlyDependencyGate()

    boundary = gate.subsystem_boundary()
    assert boundary.boundary_type == BOUNDARY_TYPE
    assert boundary.runtime_namespace == RUNTIME_NAMESPACE
    assert boundary.operator_namespace == OPERATOR_NAMESPACE
    assert boundary.qseries_execution_namespace == QSERIES_EXECUTION_NAMESPACE
    assert boundary.certified_operator_dependency_required
    assert boundary.frozen_operator_dependency_required
    assert boundary.read_only_runtime_required
    assert boundary.boundary_hash == stable_hash(
        {
            key: value
            for key, value in boundary.__dict__.items()
            if key != "boundary_hash"
        }
    )

    first = gate.consume(certification=certification)
    repeated = gate.consume(certification=certification)

    assert first == repeated
    assert first.dependency_receipt_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "dependency_receipt_hash"
        }
    )
    assert first.dependency_status == DEPENDENCY_STATUS
    assert first.dependency_type == DEPENDENCY_TYPE
    assert first.runtime_namespace == RUNTIME_NAMESPACE
    assert first.operator_namespace == OPERATOR_NAMESPACE
    assert first.qseries_execution_namespace == QSERIES_EXECUTION_NAMESPACE
    assert first.consumer_id == "oracle.operator.runtime.v1"
    assert first.projection == "certified_operator_read_only"

    assert first.source_query_boundary_complete
    assert first.source_research_response_boundary_complete
    assert first.source_session_boundary_complete
    assert first.source_console_boundary_complete
    assert first.source_presentation_boundary_complete
    assert first.source_operator_subsystem_completion_ready
    assert first.source_operator_subsystem_completion_certified
    assert first.source_operator_subsystem_frozen
    assert not first.source_further_operator_builds_required

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
    assert first.freeze_record_type_verified
    assert first.freeze_record_identity_verified
    assert first.freeze_record_payload_hash_verified
    assert first.operator_namespace_verified
    assert first.complete_operator_lineage_verified
    assert first.operator_completion_verified
    assert first.operator_freeze_verified
    assert first.deterministic_dependency_verified
    assert first.immutable_dependency_verified
    assert first.read_only_dependency_verified
    assert first.runtime_subsystem_root_established

    forbidden = (
        boundary.runtime_serving_allowed,
        boundary.runtime_serving_performed,
        boundary.network_listener_allowed,
        boundary.network_listener_started,
        boundary.operator_reexecution_allowed,
        boundary.operator_reexecution_performed,
        boundary.analytics_reexecution_allowed,
        boundary.analytics_reexecution_performed,
        boundary.database_connection_allowed,
        boundary.database_connection_performed,
        boundary.publication_allowed,
        boundary.publication_performed,
        boundary.qseries_handoff_allowed,
        boundary.qseries_execution_allowed,
        boundary.qseries_execution_performed,
        boundary.order_creation_allowed,
        boundary.order_creation_performed,
        boundary.funds_movement_allowed,
        boundary.funds_movement_performed,
        boundary.portfolio_mutation_allowed,
        boundary.portfolio_mutation_performed,
        first.runtime_serving_allowed,
        first.runtime_serving_performed,
        first.network_listener_allowed,
        first.network_listener_started,
        first.operator_reexecution_allowed,
        first.operator_reexecution_performed,
        first.analytics_reexecution_allowed,
        first.analytics_reexecution_performed,
        first.database_connection_allowed,
        first.database_connection_performed,
        first.publication_allowed,
        first.publication_performed,
        first.qseries_handoff_allowed,
        first.qseries_execution_allowed,
        first.qseries_execution_performed,
        first.order_creation_allowed,
        first.order_creation_performed,
        first.funds_movement_allowed,
        first.funds_movement_performed,
        first.portfolio_mutation_allowed,
        first.portfolio_mutation_performed,
    )
    assert not any(forbidden)

    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_completion_certification_hash="0" * 64,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            certification_status="wrong_status",
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            freeze_record_payload_hash="0" * 64,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_completion_certified=False,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            oracle_operator_subsystem_frozen=False,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            further_operator_builds_required=True,
        )
    ))
    _reject(lambda: gate.consume(
        certification=replace(
            certification,
            qseries_execution_allowed=True,
        )
    ))
    _reject(lambda: gate.consume(
        certification=certification,
        consumer_id="wrong.consumer",
    ))
    _reject(lambda: gate.consume(
        certification=certification,
        projection="wrong_projection",
    ))

    print("[PASS] Actual OOP-047 completion certification consumed")
    print("[PASS] OOP-047 identity, hash, status, type, and freeze record verified")
    print("[PASS] Complete Query through Presentation lineage preserved")
    print("[PASS] Terminal Operator completion and freeze verified")
    print("[PASS] Oracle Operator Runtime root boundary established")
    print("[PASS] Deterministic immutable dependency receipt created")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Operator and analytics re-execution remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered and unauthorized dependencies rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
