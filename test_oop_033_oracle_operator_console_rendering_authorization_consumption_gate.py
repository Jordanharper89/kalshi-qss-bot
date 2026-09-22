from __future__ import annotations

from dataclasses import replace

from test_oop_032_oracle_operator_console_rendering_authorization_gate import (
    _certification,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_authorization_gate import (
    OracleOperatorConsoleRenderingAuthorizationGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_rendering_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    RENDER_EXECUTION_PACKAGE_TYPE,
    OracleOperatorConsoleRenderingAuthorizationConsumptionGate,
    OracleOperatorConsoleRenderingAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorConsoleRenderingAuthorizationGate().authorize(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe console rendering authorization consumption accepted")
    except OracleOperatorConsoleRenderingAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-033 TEST")
    print(" OPERATOR CONSOLE RENDERING")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorConsoleRenderingAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.operator_console_rendering_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_rendering_consumption_hash"
        }
    )

    assert first.source_operator_console_rendering_authorization_id == authorization.operator_console_rendering_authorization_id
    assert first.source_operator_console_rendering_authorization_hash == authorization.operator_console_rendering_authorization_hash
    assert first.render_execution_package_type == RENDER_EXECUTION_PACKAGE_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.operator_console_id == authorization.operator_console_id
    assert first.operator_console_payload_hash == authorization.operator_console_payload_hash
    assert first.operator_console_payload == authorization.operator_console_payload

    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.authorization_type_verified
    assert first.render_input_package_type_verified
    assert first.operator_console_identity_verified
    assert first.operator_console_payload_hash_verified
    assert first.operator_console_artifact_type_verified
    assert first.operator_console_format_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.console_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_render_input_verified
    assert first.single_use_consumption_verified
    assert first.immutable_render_execution_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_boundary_verified

    assert first.operator_console_result_certified
    assert first.operator_console_rendering_authorization_ready
    assert first.operator_console_rendering_authorized
    assert first.operator_console_rendering_authorization_consumed
    assert first.operator_console_rendering_allowed
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

    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_console_rendering_authorization_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        authorization_status="wrong_status",
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_console_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_item_count=authorization.research_response_item_count + 1,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_console_rendering_performed=True,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-032 rendering authorization consumed")
    print("[PASS] Authorization identity, hash, status, and type verified")
    print("[PASS] Operator Console identity and payload hash verified")
    print("[PASS] Session and Research Response lineage preserved")
    print("[PASS] Single-use immutable render execution package created")
    print("[PASS] Rendering authorization marked consumed")
    print("[PASS] Console rendering allowed but not performed")
    print("[PASS] Presentation rendering remains disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
