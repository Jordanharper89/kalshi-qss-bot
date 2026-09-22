from __future__ import annotations

from dataclasses import replace

from test_oop_018_oracle_operator_research_response_handoff_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_handoff_authorization_consumption_gate import (
    OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_readiness_gate import (
    READINESS_STATUS,
    READINESS_TYPE,
    OracleOperatorResearchResponseMaterializationReadinessGate,
    OracleOperatorResearchResponseMaterializationReadinessInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe materialization readiness accepted")
    except OracleOperatorResearchResponseMaterializationReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-019 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" READINESS GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorResearchResponseMaterializationReadinessGate()

    first = gate.evaluate(consumption=consumption)
    repeated = gate.evaluate(consumption=consumption)

    assert first == repeated
    assert first.research_response_materialization_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_readiness_hash"
        }
    )

    assert first.source_research_response_handoff_consumption_id == consumption.research_response_handoff_consumption_id
    assert first.source_research_response_handoff_consumption_hash == consumption.research_response_handoff_consumption_hash
    assert first.readiness_type == READINESS_TYPE
    assert first.response_entry_count == consumption.consumed_entry_count
    assert first.response_result_count == consumption.consumed_result_count
    assert first.response_artifact_entry_ids == consumption.consumed_response_artifact_entry_ids
    assert first.response_query_response_ids == consumption.consumed_query_response_ids
    assert first.response_result_hashes == consumption.consumed_result_hashes
    assert first.response_result_payloads == consumption.consumed_result_payloads

    assert first.consumption_type_verified
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.response_input_package_verified
    assert first.response_schema_inputs_verified
    assert first.response_content_inputs_verified
    assert first.deterministic_readiness_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert first.research_response_materialization_ready
    assert not first.research_response_materialization_authorized
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
    assert first.readiness_status == READINESS_STATUS

    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                research_response_handoff_consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumption_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumed_result_hashes=("0" * 64,) * consumption.consumed_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumed_result_count=consumption.consumed_result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                research_response_materialization_ready=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-018 response input package consumed")
    print("[PASS] OOP-018 identity, hash, status, and lineage verified")
    print("[PASS] Response input payload hashes recomputed and verified")
    print("[PASS] Exact response identities and cardinality verified")
    print("[PASS] Frozen Research Response scope preserved")
    print("[PASS] Response schema and content inputs certified ready")
    print("[PASS] Research Response materialization marked ready")
    print("[PASS] Materialization remains unauthorized and unperformed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe readiness inputs rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
