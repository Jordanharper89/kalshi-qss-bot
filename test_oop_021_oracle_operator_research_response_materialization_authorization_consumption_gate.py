from __future__ import annotations

from dataclasses import replace

from test_oop_020_oracle_operator_research_response_materialization_authorization_gate import (
    _readiness,
)

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_gate import (
    OracleOperatorResearchResponseMaterializationAuthorizationGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate,
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorResearchResponseMaterializationAuthorizationGate().authorize(
        readiness=_readiness()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe materialization authorization consumption accepted")
    except OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-021 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.research_response_materialization_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_consumption_hash"
        }
    )

    assert first.source_research_response_materialization_authorization_id == authorization.research_response_materialization_authorization_id
    assert first.source_research_response_materialization_authorization_hash == authorization.research_response_materialization_authorization_hash
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.consumed_entry_count == authorization.authorized_entry_count
    assert first.consumed_result_count == authorization.authorized_result_count
    assert first.consumed_response_artifact_entry_ids == authorization.authorized_response_artifact_entry_ids
    assert first.consumed_query_response_ids == authorization.authorized_query_response_ids
    assert first.consumed_result_hashes == authorization.authorized_result_hashes
    assert first.consumed_result_payloads == authorization.authorized_result_payloads

    assert first.authorization_type_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.response_input_package_verified
    assert first.response_schema_inputs_verified
    assert first.response_content_inputs_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.single_use_consumption_verified
    assert first.immutable_execution_package_verified
    assert first.deterministic_consumption_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert first.research_response_materialization_ready
    assert first.research_response_materialization_authorized
    assert first.research_response_materialization_authorization_consumed
    assert first.research_response_materialization_allowed
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
                research_response_materialization_authorization_hash="0" * 64,
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
                authorized_result_hashes=("0" * 64,) * authorization.authorized_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_result_count=authorization.authorized_result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_materialization_performed=True,
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

    print("[PASS] Actual OOP-020 materialization authorization consumed")
    print("[PASS] OOP-020 identity, hash, status, and lineage verified")
    print("[PASS] Authorized response payload hashes recomputed and verified")
    print("[PASS] Exact response identities and cardinality preserved")
    print("[PASS] Frozen Research Response scope preserved")
    print("[PASS] Single-use immutable execution package created")
    print("[PASS] Materialization authorization marked consumed")
    print("[PASS] Research Response construction remains unperformed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
