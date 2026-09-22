from __future__ import annotations

from dataclasses import replace

from test_oop_038_oracle_operator_presentation_rendering_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_execution_gate import (
    OracleOperatorPresentationRenderingExecutionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorPresentationRenderingResultCertificationGate,
    OracleOperatorPresentationRenderingResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorPresentationRenderingExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe presentation certification accepted")
    except OracleOperatorPresentationRenderingResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-039 TEST")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorPresentationRenderingResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_presentation_rendering_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_rendering_result_certification_hash"
        }
    )
    assert first.rendered_presentation_payload_hash == stable_hash(
        first.rendered_presentation_payload
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.rendered_presentation_id == execution.rendered_presentation_id
    assert first.rendered_presentation_payload == execution.rendered_presentation_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.rendered_presentation_identity_verified
    assert first.rendered_presentation_payload_hash_verified
    assert first.rendered_presentation_artifact_type_verified
    assert first.rendered_presentation_format_verified
    assert first.rendered_presentation_sections_verified
    assert first.rendered_console_identity_verified
    assert first.rendered_console_payload_hash_verified
    assert first.operator_console_identity_verified
    assert first.operator_console_payload_hash_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_rendered_presentation_verified
    assert first.read_only_rendered_presentation_verified
    assert first.deterministic_certification_verified

    assert first.operator_console_rendering_result_certified
    assert first.operator_presentation_rendering_authorized
    assert first.operator_presentation_rendering_authorization_consumed
    assert first.operator_presentation_rendering_allowed
    assert first.operator_presentation_rendering_performed
    assert first.operator_presentation_rendering_result_certified
    assert first.publication_authorization_ready
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
        operator_presentation_rendering_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        publication_authorization_ready=True,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-038 rendered presentation execution consumed")
    print("[PASS] Execution identity, hash, status, artifact type, and format verified")
    print("[PASS] Rendered presentation identity and payload hash verified")
    print("[PASS] Presentation header, results, context, and lineage sections verified")
    print("[PASS] Rendered Console, Operator Console, Session, and Research Response lineage preserved")
    print("[PASS] Immutable read-only rendered presentation certified")
    print("[PASS] Complete frozen lineage preserved")
    print("[PASS] Publication authorization marked ready")
    print("[PASS] Publication remains unauthorized and unperformed")
    print("[PASS] Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe presentation executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
