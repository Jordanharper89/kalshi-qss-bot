from __future__ import annotations

from dataclasses import replace

from test_oop_011_oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import (
    _consumption,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_authorization_gate import (
    AUTHORIZATION_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError,
    stable_hash,
)


def _readiness():
    return OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate().certify(
        consumption=_consumption()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe adapter execution authorization accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-012 TEST")
    print(" ADAPTER INVOCATION EXECUTION AUTHORIZATION")
    print(" SINGLE BOUNDED READ-ONLY CALL")
    print("=" * 40)

    readiness = _readiness()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate()

    first = gate.authorize(readiness=readiness)
    repeated = gate.authorize(readiness=readiness)

    assert first == repeated
    assert first.adapter_execution_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_execution_authorization_hash"
        }
    )

    assert (
        first.source_adapter_execution_readiness_id
        == readiness.adapter_execution_readiness_id
    )
    assert (
        first.source_adapter_execution_readiness_hash
        == readiness.adapter_execution_readiness_hash
    )
    assert first.execution_mode == readiness.execution_mode
    assert first.read_adapter_contract_id == readiness.read_adapter_contract_id
    assert first.authorized_entry_count == readiness.ready_entry_count
    assert (
        first.authorized_response_artifact_entry_ids
        == readiness.ready_response_artifact_entry_ids
    )
    assert (
        first.authorized_query_response_ids
        == readiness.ready_query_response_ids
    )

    assert first.readiness_type_verified
    assert first.readiness_identity_verified
    assert first.readiness_hash_verified
    assert first.readiness_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.deterministic_authorization_verified
    assert first.adapter_invocation_execution_ready
    assert first.adapter_invocation_execution_authorized
    assert first.adapter_invocation_execution_allowed
    assert not first.adapter_invocation_execution_performed

    assert first.analytics_artifact_read_allowed
    assert not first.analytics_artifact_read_performed
    assert not first.analytics_query_execution_allowed
    assert not first.analytics_query_execution_performed
    assert not first.analytics_reexecution_allowed
    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_allowed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
    assert not first.research_response_materialization_allowed
    assert not first.research_response_materialization_performed
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed
    assert first.authorization_status == AUTHORIZATION_STATUS

    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                adapter_execution_readiness_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                readiness_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                execution_mode="wrong_mode",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                adapter_invocation_execution_ready=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                adapter_invocation_execution_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-011 execution-readiness record consumed")
    print("[PASS] OOP-011 identity, hash, status, and lineage verified")
    print("[PASS] Immutable invocation package and adapter contract verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic adapter execution authorization created")
    print("[PASS] Single bounded read-only adapter call authorized")
    print("[PASS] Adapter invocation authorized but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] No analytics execution, reexecution, DB, or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed readiness rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
