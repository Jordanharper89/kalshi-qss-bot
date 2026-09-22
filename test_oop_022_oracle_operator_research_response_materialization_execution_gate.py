from __future__ import annotations

from dataclasses import replace

from test_oop_021_oracle_operator_research_response_materialization_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import (
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_execution_gate import (
    EXECUTION_STATUS,
    RESEARCH_RESPONSE_ARTIFACT_TYPE,
    RESPONSE_FORMAT,
    OracleOperatorResearchResponseMaterializationExecutionGate,
    OracleOperatorResearchResponseMaterializationExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe execution accepted")
    except OracleOperatorResearchResponseMaterializationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-022 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorResearchResponseMaterializationExecutionGate()
    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.research_response_materialization_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_execution_hash"
        }
    )
    assert first.research_response_payload_hash == stable_hash(first.research_response_payload)
    assert first.research_response_artifact_type == RESEARCH_RESPONSE_ARTIFACT_TYPE
    assert first.response_format == RESPONSE_FORMAT
    assert first.source_result_count == consumption.consumed_result_count
    assert first.research_response_item_count == consumption.consumed_result_count
    assert first.source_result_hashes == consumption.consumed_result_hashes

    for index, item in enumerate(first.research_response_items):
        assert item["ordinal"] == index + 1
        assert item["response_artifact_entry_id"] == consumption.consumed_response_artifact_entry_ids[index]
        assert item["query_response_id"] == consumption.consumed_query_response_ids[index]
        assert item["source_result_hash"] == consumption.consumed_result_hashes[index]
        assert item["certified_payload"] == consumption.consumed_result_payloads[index]

    assert first.deterministic_materialization_verified
    assert first.immutable_response_verified
    assert first.read_only_materialization_verified
    assert first.research_response_materialization_performed
    assert first.research_response_certification_ready
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.qseries_execution_allowed
    assert not first.order_creation_allowed
    assert not first.funds_movement_allowed
    assert not first.portfolio_mutation_allowed
    assert first.execution_status == EXECUTION_STATUS

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_materialization_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumed_result_hashes=("0" * 64,) * consumption.consumed_result_count,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_materialization_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-021 execution package consumed")
    print("[PASS] OOP-021 hash, status, scope, and cardinality verified")
    print("[PASS] Source result payload hashes recomputed")
    print("[PASS] Deterministic immutable Research Response created")
    print("[PASS] Research Response payload hash verified")
    print("[PASS] Read-only materialization performed")
    print("[PASS] Research Response certification marked ready")
    print("[PASS] Session, console, presentation, and publication remain gated")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe execution packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
