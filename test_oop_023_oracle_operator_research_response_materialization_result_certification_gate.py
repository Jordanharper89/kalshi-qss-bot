from __future__ import annotations

from dataclasses import replace

from test_oop_022_oracle_operator_research_response_materialization_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_execution_gate import (
    OracleOperatorResearchResponseMaterializationExecutionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorResearchResponseMaterializationResultCertificationGate,
    OracleOperatorResearchResponseMaterializationResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorResearchResponseMaterializationExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe certification accepted")
    except OracleOperatorResearchResponseMaterializationResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-023 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorResearchResponseMaterializationResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.research_response_materialization_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_result_certification_hash"
        }
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.research_response_id == execution.research_response_id
    assert first.research_response_payload_hash == execution.research_response_payload_hash
    assert first.research_response_payload == execution.research_response_payload
    assert first.research_response_items == execution.research_response_items

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.response_identity_verified
    assert first.response_payload_hash_verified
    assert first.response_format_verified
    assert first.response_artifact_type_verified
    assert first.response_item_cardinality_verified
    assert first.response_item_identity_verified
    assert first.source_result_hashes_verified
    assert first.certified_payload_preservation_verified
    assert first.read_only_response_verified
    assert first.immutable_response_verified
    assert first.deterministic_certification_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.research_response_result_certified
    assert first.operator_session_construction_ready
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.qseries_execution_allowed
    assert not first.order_creation_allowed
    assert not first.funds_movement_allowed
    assert not first.portfolio_mutation_allowed

    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_materialization_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_construction_allowed=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-022 materialized response consumed")
    print("[PASS] OOP-022 execution identity, hash, and status verified")
    print("[PASS] Research Response payload hash recomputed and verified")
    print("[PASS] Response format, artifact type, identities, and cardinality verified")
    print("[PASS] Certified source payload preservation verified")
    print("[PASS] Immutable read-only Research Response certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Operator Session construction marked ready")
    print("[PASS] Session construction remains unauthorized")
    print("[PASS] Console, presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe execution results rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
