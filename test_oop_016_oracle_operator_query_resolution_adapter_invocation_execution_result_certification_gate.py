from __future__ import annotations

from dataclasses import replace

from test_oop_015_oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    _activation,
    _DeterministicReadOnlyAdapter,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFIED_RESULT_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorQueryResolutionAdapterInvocationExecutionGate().execute(
        activation=_activation(),
        adapter=_DeterministicReadOnlyAdapter(),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe execution result certification accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-016 TEST")
    print(" EXECUTION RESULT CERTIFICATION")
    print(" CERTIFIED BOUNDED READ-ONLY RESULT")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.execution_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "execution_result_certification_hash"
        }
    )

    assert first.source_adapter_invocation_execution_id == execution.adapter_invocation_execution_id
    assert first.source_adapter_invocation_execution_hash == execution.adapter_invocation_execution_hash
    assert first.certified_result_type == CERTIFIED_RESULT_TYPE
    assert first.certified_entry_count == execution.executed_entry_count
    assert first.certified_result_count == execution.result_count
    assert first.certified_response_artifact_entry_ids == execution.executed_response_artifact_entry_ids
    assert first.certified_query_response_ids == execution.executed_query_response_ids
    assert first.certified_result_hashes == execution.result_hashes
    assert first.certified_result_payloads == execution.result_payloads

    assert first.execution_type_verified
    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.immutable_execution_package_verified
    assert first.execution_result_type_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.execution_performed_verified
    assert first.artifact_read_performed_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.deterministic_certification_verified

    assert first.adapter_invocation_execution_performed
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
    assert first.certification_status == CERTIFICATION_STATUS

    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                adapter_invocation_execution_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                execution_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                result_count=execution.result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                result_hashes=("0" * 64,) * execution.result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-015 execution result consumed")
    print("[PASS] OOP-015 identity, hash, status, and lineage verified")
    print("[PASS] Result payload hashes recomputed and verified")
    print("[PASS] Result cardinality and exact identities certified")
    print("[PASS] Frozen bounded read scope preserved")
    print("[PASS] First analytics artifact read result certified")
    print("[PASS] No analytics query execution, reexecution, DB, or mutation occurred")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
