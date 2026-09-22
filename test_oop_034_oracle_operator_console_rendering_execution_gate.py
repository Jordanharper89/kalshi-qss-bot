from __future__ import annotations

from dataclasses import replace

from test_oop_033_oracle_operator_console_rendering_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_authorization_consumption_gate import (
    OracleOperatorConsoleRenderingAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_execution_gate import (
    EXECUTION_STATUS,
    RENDERED_CONSOLE_ARTIFACT_TYPE,
    RENDERED_CONSOLE_FORMAT,
    OracleOperatorConsoleRenderingExecutionGate,
    OracleOperatorConsoleRenderingExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorConsoleRenderingAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe console rendering execution accepted")
    except OracleOperatorConsoleRenderingExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-034 TEST")
    print(" OPERATOR CONSOLE RENDERING")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorConsoleRenderingExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_console_rendering_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_rendering_execution_hash"
        }
    )
    assert first.rendered_console_payload_hash == stable_hash(first.rendered_console_payload)
    assert first.rendered_console_artifact_type == RENDERED_CONSOLE_ARTIFACT_TYPE
    assert first.rendered_console_format == RENDERED_CONSOLE_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    assert first.rendered_console_payload["rendered_console_id"] == first.rendered_console_id
    assert first.rendered_console_payload["operator_console_id"] == first.operator_console_id
    assert first.rendered_console_payload["operator_console_payload_hash"] == first.operator_console_payload_hash
    assert first.rendered_console_payload["operator_session_id"] == first.operator_session_id
    assert first.rendered_console_payload["research_response_id"] == first.research_response_id
    assert first.rendered_console_payload["read_only"] is True
    assert first.rendered_console_payload["presentation_rendering_disabled"] is True
    assert first.rendered_console_payload["publication_disabled"] is True
    assert first.rendered_console_payload["qseries_execution_disabled"] is True
    assert len(first.rendered_console_payload["sections"]) == 3

    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.render_execution_package_type_verified
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
    assert first.deterministic_rendering_verified
    assert first.immutable_rendered_console_verified
    assert first.read_only_rendered_console_verified

    assert first.operator_console_result_certified
    assert first.operator_console_rendering_authorization_ready
    assert first.operator_console_rendering_authorized
    assert first.operator_console_rendering_authorization_consumed
    assert first.operator_console_rendering_allowed
    assert first.operator_console_rendering_performed
    assert first.operator_console_rendering_result_certification_ready
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

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_rendering_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_item_count=consumption.research_response_item_count + 1,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_rendering_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-033 render execution package consumed")
    print("[PASS] Consumption identity, hash, status, and package type verified")
    print("[PASS] Operator Console identity and payload hash verified")
    print("[PASS] Session and Research Response lineage preserved")
    print("[PASS] Deterministic immutable rendered console created")
    print("[PASS] Rendered console payload hash verified")
    print("[PASS] Console rendering performed read-only")
    print("[PASS] Rendering result certification marked ready")
    print("[PASS] Presentation rendering remains disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe render packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
