from __future__ import annotations

from dataclasses import replace

from test_oop_012_oracle_operator_query_resolution_adapter_invocation_execution_authorization_gate import (
    _readiness,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_authorization_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumptionGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationGate().authorize(
        readiness=_readiness()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe execution-authorization consumption accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-013 TEST")
    print(" EXECUTION AUTHORIZATION CONSUMPTION")
    print(" SINGLE-USE ADAPTER EXECUTION PACKAGE")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleOperatorQueryResolutionAdapterInvocationExecutionAuthorizationConsumptionGate()
    )

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.adapter_execution_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_execution_consumption_hash"
        }
    )

    assert (
        first.source_adapter_execution_authorization_id
        == authorization.adapter_execution_authorization_id
    )
    assert (
        first.source_adapter_execution_authorization_hash
        == authorization.adapter_execution_authorization_hash
    )
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.execution_mode == authorization.execution_mode
    assert first.read_adapter_contract_id == authorization.read_adapter_contract_id
    assert first.consumed_entry_count == authorization.authorized_entry_count
    assert (
        first.consumed_response_artifact_entry_ids
        == authorization.authorized_response_artifact_entry_ids
    )
    assert (
        first.consumed_query_response_ids
        == authorization.authorized_query_response_ids
    )

    assert first.authorization_type_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.immutable_execution_package_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.single_use_execution_consumption_verified
    assert first.deterministic_consumption_verified

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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                adapter_execution_authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorization_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                adapter_invocation_execution_authorized=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                adapter_invocation_execution_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-012 execution authorization consumed")
    print("[PASS] OOP-012 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic single-use execution consumption created")
    print("[PASS] Immutable adapter execution package materialized")
    print("[PASS] Adapter execution authorized but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] No analytics execution, reexecution, DB, or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
