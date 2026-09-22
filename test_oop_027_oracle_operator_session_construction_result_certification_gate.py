from __future__ import annotations

from dataclasses import replace

from test_oop_026_oracle_operator_session_construction_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_execution_gate import (
    OracleOperatorSessionConstructionExecutionGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorSessionConstructionResultCertificationGate,
    OracleOperatorSessionConstructionResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorSessionConstructionExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session certification accepted")
    except OracleOperatorSessionConstructionResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-027 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorSessionConstructionResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_session_construction_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_result_certification_hash"
        }
    )
    assert first.operator_session_payload_hash == stable_hash(first.operator_session_payload)
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.operator_session_id == execution.operator_session_id
    assert first.operator_session_payload == execution.operator_session_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.execution_package_type_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.operator_session_artifact_type_verified
    assert first.operator_session_format_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.session_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_session_verified
    assert first.read_only_session_verified
    assert first.deterministic_certification_verified

    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
    assert first.operator_session_construction_authorization_consumed
    assert first.operator_session_construction_allowed
    assert first.operator_session_construction_performed
    assert first.operator_session_result_certified
    assert first.operator_console_construction_ready
    assert not first.operator_console_rendering_allowed
    assert not first.operator_console_rendering_performed
    assert not first.operator_presentation_rendering_allowed
    assert not first.operator_presentation_rendering_performed
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

    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_construction_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_session_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_console_rendering_allowed=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-026 Operator Session consumed")
    print("[PASS] OOP-026 execution identity, hash, and status verified")
    print("[PASS] Operator Session payload hash recomputed and verified")
    print("[PASS] Session artifact type, format, and identity verified")
    print("[PASS] Research Response lineage and cardinality preserved")
    print("[PASS] Immutable read-only Operator Session certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Operator Console construction marked ready")
    print("[PASS] Console rendering remains unauthorized")
    print("[PASS] Presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe session executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
