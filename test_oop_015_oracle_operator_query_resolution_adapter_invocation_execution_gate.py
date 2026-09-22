from __future__ import annotations

from dataclasses import replace

from test_oop_014_oracle_operator_query_resolution_adapter_invocation_activation_gate import (
    _consumption,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_activation_gate import (
    OracleOperatorQueryResolutionAdapterInvocationActivationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    EXECUTION_RESULT_TYPE,
    EXECUTION_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError,
    stable_hash,
)


def _activation():
    return OracleOperatorQueryResolutionAdapterInvocationActivationGate().activate(
        consumption=_consumption()
    )


class _DeterministicReadOnlyAdapter:
    def __call__(
        self,
        *,
        response_artifact_entry_ids,
        query_response_ids,
        query_mode,
        query_text,
        time_scope,
        sort_order,
        result_limit,
        requested_tags,
    ):
        return tuple(
            {
                "response_artifact_entry_id": entry_id,
                "query_response_id": response_id,
                "query_mode": query_mode,
                "query_text": query_text,
                "time_scope": time_scope,
                "sort_order": sort_order,
                "result_limit": result_limit,
                "requested_tags": tuple(requested_tags),
                "read_only": True,
                "artifact_payload": {
                    "market_id": f"market-{index + 1}",
                    "venue": "certified_read_only_fixture",
                    "prediction": 0.61,
                    "confidence": 0.78,
                },
            }
            for index, (entry_id, response_id) in enumerate(
                zip(response_artifact_entry_ids, query_response_ids)
            )
        )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe adapter execution accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-015 TEST")
    print(" ADAPTER INVOCATION EXECUTION")
    print(" FIRST CERTIFIED ANALYTICS ARTIFACT READ")
    print("=" * 40)

    activation = _activation()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionGate()
    adapter = _DeterministicReadOnlyAdapter()

    first = gate.execute(activation=activation, adapter=adapter)
    repeated = gate.execute(activation=activation, adapter=adapter)

    assert first == repeated
    assert first.adapter_invocation_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_invocation_execution_hash"
        }
    )

    assert (
        first.source_adapter_invocation_activation_id
        == activation.adapter_invocation_activation_id
    )
    assert (
        first.source_adapter_invocation_activation_hash
        == activation.adapter_invocation_activation_hash
    )
    assert first.execution_result_type == EXECUTION_RESULT_TYPE
    assert first.executed_entry_count == activation.active_entry_count
    assert first.result_count == activation.active_entry_count
    assert len(first.result_hashes) == first.result_count
    assert len(first.result_payloads) == first.result_count
    assert (
        first.executed_response_artifact_entry_ids
        == activation.active_response_artifact_entry_ids
    )
    assert (
        first.executed_query_response_ids
        == activation.active_query_response_ids
    )

    assert first.activation_type_verified
    assert first.activation_identity_verified
    assert first.activation_hash_verified
    assert first.activation_status_verified
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
    assert first.adapter_result_cardinality_verified
    assert first.adapter_result_identity_verified
    assert first.deterministic_execution_verified

    assert first.adapter_invocation_active
    assert first.adapter_invocation_execution_ready
    assert first.adapter_invocation_execution_authorized
    assert first.adapter_invocation_execution_allowed
    assert first.adapter_invocation_execution_performed
    assert first.analytics_artifact_read_allowed
    assert first.analytics_artifact_read_performed
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
    assert first.execution_status == EXECUTION_STATUS

    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                adapter_invocation_activation_hash="0" * 64,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                activation_status="wrong_status",
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                adapter_invocation_execution_performed=True,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                analytics_artifact_read_performed=True,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=activation,
            adapter=lambda **_: (),
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=activation,
            adapter=lambda **_: (
                {
                    "response_artifact_entry_id": "wrong",
                    "query_response_id": "wrong",
                },
            ),
        )
    )

    print("[PASS] Actual OOP-014 active invocation consumed")
    print("[PASS] OOP-014 identity, hash, status, and lineage verified")
    print("[PASS] Frozen activated scope preserved without expansion")
    print("[PASS] Single bounded read-only adapter call performed")
    print("[PASS] First certified analytics artifact read completed")
    print("[PASS] Immutable deterministic execution evidence created")
    print("[PASS] Result cardinality and identities verified")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] No analytics query execution or reexecution occurred")
    print("[PASS] No analytics database connection or mutation occurred")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
