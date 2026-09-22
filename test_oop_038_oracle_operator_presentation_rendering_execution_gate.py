from __future__ import annotations

from dataclasses import replace

from test_oop_037_oracle_operator_presentation_rendering_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_authorization_consumption_gate import (
    OracleOperatorPresentationRenderingAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_execution_gate import (
    EXECUTION_STATUS,
    RENDERED_PRESENTATION_ARTIFACT_TYPE,
    RENDERED_PRESENTATION_FORMAT,
    OracleOperatorPresentationRenderingExecutionGate,
    OracleOperatorPresentationRenderingExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorPresentationRenderingAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe presentation rendering execution accepted")
    except OracleOperatorPresentationRenderingExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-038 TEST")
    print(" OPERATOR PRESENTATION RENDERING")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorPresentationRenderingExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_presentation_rendering_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_rendering_execution_hash"
        }
    )
    assert first.rendered_presentation_payload_hash == stable_hash(
        first.rendered_presentation_payload
    )
    assert first.rendered_presentation_artifact_type == RENDERED_PRESENTATION_ARTIFACT_TYPE
    assert first.rendered_presentation_format == RENDERED_PRESENTATION_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    payload = first.rendered_presentation_payload
    assert payload["rendered_presentation_id"] == first.rendered_presentation_id
    assert payload["rendered_console_id"] == first.rendered_console_id
    assert payload["rendered_console_payload_hash"] == first.rendered_console_payload_hash
    assert payload["operator_console_id"] == first.operator_console_id
    assert payload["operator_session_id"] == first.operator_session_id
    assert payload["research_response_id"] == first.research_response_id
    assert payload["read_only"] is True
    assert payload["publication_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert tuple(section["section_id"] for section in payload["sections"]) == (
        "presentation_header",
        "presentation_results",
        "presentation_context",
        "presentation_lineage",
    )

    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.presentation_execution_package_type_verified
    assert first.rendered_console_identity_verified
    assert first.rendered_console_payload_hash_verified
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
    assert first.deterministic_rendering_verified
    assert first.immutable_rendered_presentation_verified
    assert first.read_only_rendered_presentation_verified

    assert first.operator_console_rendering_result_certified
    assert first.operator_presentation_rendering_authorization_ready
    assert first.operator_presentation_rendering_authorized
    assert first.operator_presentation_rendering_authorization_consumed
    assert first.operator_presentation_rendering_allowed
    assert first.operator_presentation_rendering_performed
    assert first.operator_presentation_rendering_result_certification_ready
    assert not first.publication_authorization_ready
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

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_presentation_rendering_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        rendered_console_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_item_count=consumption.research_response_item_count + 1,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_presentation_rendering_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-037 presentation execution package consumed")
    print("[PASS] Consumption identity, hash, status, and package type verified")
    print("[PASS] Rendered console identity, payload hash, format, and sections verified")
    print("[PASS] Operator Console, Session, and Research Response lineage preserved")
    print("[PASS] Deterministic immutable rendered presentation created")
    print("[PASS] Rendered presentation payload hash verified")
    print("[PASS] Presentation rendering performed read-only")
    print("[PASS] Presentation result certification marked ready")
    print("[PASS] Publication authorization remains not ready")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe presentation packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
