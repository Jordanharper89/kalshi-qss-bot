from __future__ import annotations

from dataclasses import replace

from test_oop_034_oracle_operator_console_rendering_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_execution_gate import (
    OracleOperatorConsoleRenderingExecutionGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorConsoleRenderingResultCertificationGate,
    OracleOperatorConsoleRenderingResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorConsoleRenderingExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe rendered console certification accepted")
    except OracleOperatorConsoleRenderingResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-035 TEST")
    print(" OPERATOR CONSOLE RENDERING")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorConsoleRenderingResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_console_rendering_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_rendering_result_certification_hash"
        }
    )
    assert first.rendered_console_payload_hash == stable_hash(first.rendered_console_payload)
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.rendered_console_id == execution.rendered_console_id
    assert first.rendered_console_payload == execution.rendered_console_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.rendered_console_identity_verified
    assert first.rendered_console_payload_hash_verified
    assert first.rendered_console_artifact_type_verified
    assert first.rendered_console_format_verified
    assert first.operator_console_identity_verified
    assert first.operator_console_payload_hash_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.rendered_sections_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_rendered_console_verified
    assert first.read_only_rendered_console_verified
    assert first.deterministic_certification_verified

    assert first.operator_console_result_certified
    assert first.operator_console_rendering_authorized
    assert first.operator_console_rendering_authorization_consumed
    assert first.operator_console_rendering_allowed
    assert first.operator_console_rendering_performed
    assert first.operator_console_rendering_result_certified
    assert first.operator_presentation_rendering_authorization_ready
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
        operator_console_rendering_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        rendered_console_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_presentation_rendering_allowed=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-034 rendered console execution consumed")
    print("[PASS] Execution identity, hash, status, artifact type, and format verified")
    print("[PASS] Rendered console identity and payload hash verified")
    print("[PASS] Query context, research results, and lineage sections verified")
    print("[PASS] Operator Console, Session, and Research Response lineage preserved")
    print("[PASS] Immutable read-only rendered console certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Presentation rendering authorization marked ready")
    print("[PASS] Presentation rendering remains unauthorized")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe rendered console executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
