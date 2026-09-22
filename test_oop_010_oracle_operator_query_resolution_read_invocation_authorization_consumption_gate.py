from __future__ import annotations

from dataclasses import replace

from test_oop_009_oracle_operator_query_resolution_read_invocation_authorization_gate import (
    _readiness,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_gate import (
    OracleOperatorQueryResolutionReadInvocationAuthorizationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    INVOCATION_PACKAGE_TYPE,
    OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate,
    OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorQueryResolutionReadInvocationAuthorizationGate().authorize(
        readiness=_readiness()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe read-authorization consumption accepted")
    except OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-010 TEST")
    print(" READ AUTHORIZATION CONSUMPTION")
    print(" IMMUTABLE ADAPTER INVOCATION PACKAGE")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleOperatorQueryResolutionReadInvocationAuthorizationConsumptionGate()
    )

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.read_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "read_consumption_hash"
        }
    )

    assert first.source_read_authorization_id == authorization.read_authorization_id
    assert first.source_read_authorization_hash == authorization.read_authorization_hash
    assert first.invocation_package_type == INVOCATION_PACKAGE_TYPE
    assert first.read_invocation_mode == authorization.read_invocation_mode
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
    assert first.immutable_manifest_verified
    assert first.single_use_consumption_verified
    assert first.read_invocation_mode_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_authorized
    assert first.immutable_invocation_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_resolution_required

    assert first.read_invocation_allowed
    assert not first.read_invocation_performed
    assert first.query_resolution_allowed
    assert not first.query_resolution_performed
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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                read_authorization_hash="0" * 64,
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
                read_invocation_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                read_invocation_performed=True,
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
                qseries_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                portfolio_mutation_performed=True,
            )
        )
    )

    print("[PASS] Actual OOP-009 read authorization consumed")
    print("[PASS] OOP-009 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic single-use consumption record created")
    print("[PASS] Immutable adapter invocation package materialized")
    print("[PASS] Read invocation allowed but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
