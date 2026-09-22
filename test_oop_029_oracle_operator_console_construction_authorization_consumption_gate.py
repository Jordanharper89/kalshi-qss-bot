from __future__ import annotations

from dataclasses import replace

from test_oop_028_oracle_operator_console_construction_authorization_gate import (
    _certification,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_construction_authorization_gate import (
    OracleOperatorConsoleConstructionAuthorizationGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_construction_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorConsoleConstructionAuthorizationConsumptionGate,
    OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorConsoleConstructionAuthorizationGate().authorize(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe console authorization consumption accepted")
    except OracleOperatorConsoleConstructionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-029 TEST")
    print(" OPERATOR CONSOLE CONSTRUCTION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorConsoleConstructionAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.operator_console_construction_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_construction_consumption_hash"
        }
    )

    assert first.source_operator_console_construction_authorization_id == authorization.operator_console_construction_authorization_id
    assert first.source_operator_console_construction_authorization_hash == authorization.operator_console_construction_authorization_hash
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.operator_session_id == authorization.operator_session_id
    assert first.operator_session_payload_hash == authorization.operator_session_payload_hash
    assert first.operator_session_payload == authorization.operator_session_payload

    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.authorization_type_verified
    assert first.console_input_package_type_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.session_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_console_input_verified
    assert first.single_use_consumption_verified
    assert first.immutable_execution_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_boundary_verified

    assert first.operator_session_result_certified
    assert first.operator_console_construction_ready
    assert first.operator_console_construction_authorized
    assert first.operator_console_construction_authorization_consumed
    assert first.operator_console_construction_allowed
    assert not first.operator_console_construction_performed
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

    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_console_construction_authorization_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        authorization_status="wrong_status",
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_session_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_item_count=authorization.research_response_item_count + 1,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_console_construction_performed=True,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-028 console construction authorization consumed")
    print("[PASS] Authorization identity, hash, status, and type verified")
    print("[PASS] Operator Session identity and payload hash verified")
    print("[PASS] Research Response lineage and cardinality preserved")
    print("[PASS] Single-use immutable console execution package created")
    print("[PASS] Console construction authorization marked consumed")
    print("[PASS] Console construction allowed but not performed")
    print("[PASS] Console rendering remains disabled")
    print("[PASS] Presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
