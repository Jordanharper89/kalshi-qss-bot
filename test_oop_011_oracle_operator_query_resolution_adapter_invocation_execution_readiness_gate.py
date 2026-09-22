from __future__ import annotations

from dataclasses import replace

from test_oop_010_oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate import (
    EXECUTION_MODE,
    READINESS_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError,
    stable_hash,
)


def _consumption():
    return (
        OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate()
    ).consume(
        authorization=_authorization()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe adapter execution readiness accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-011 TEST")
    print(" ADAPTER INVOCATION EXECUTION READINESS")
    print(" SINGLE BOUNDED READ-ONLY CALL")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionReadinessGate()

    first = gate.certify(consumption=consumption)
    repeated = gate.certify(consumption=consumption)

    assert first == repeated
    assert first.adapter_execution_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_execution_readiness_hash"
        }
    )

    assert first.source_read_consumption_id == consumption.read_consumption_id
    assert first.source_read_consumption_hash == consumption.read_consumption_hash
    assert first.execution_mode == EXECUTION_MODE
    assert first.read_adapter_contract_id == consumption.read_adapter_contract_id
    assert first.ready_entry_count == consumption.consumed_entry_count
    assert (
        first.ready_response_artifact_entry_ids
        == consumption.consumed_response_artifact_entry_ids
    )
    assert (
        first.ready_query_response_ids
        == consumption.consumed_query_response_ids
    )

    assert first.consumption_type_verified
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.deterministic_readiness_verified

    assert first.adapter_invocation_execution_ready
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
    assert first.readiness_status == READINESS_STATUS

    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                read_consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                consumption_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                invocation_package_type="wrong_package",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                immutable_invocation_package_verified=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                read_invocation_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-010 invocation package consumed")
    print("[PASS] OOP-010 identity, hash, status, and lineage verified")
    print("[PASS] Immutable adapter invocation package verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic adapter execution readiness certified")
    print("[PASS] Single bounded read-only adapter call allowed")
    print("[PASS] Adapter invocation ready but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
