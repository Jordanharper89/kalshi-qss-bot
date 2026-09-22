from __future__ import annotations

from dataclasses import replace

from test_oop_029_oracle_operator_console_construction_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_construction_authorization_consumption_gate import (
    OracleOperatorConsoleConstructionAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_construction_execution_gate import (
    EXECUTION_STATUS,
    OPERATOR_CONSOLE_ARTIFACT_TYPE,
    OPERATOR_CONSOLE_FORMAT,
    OracleOperatorConsoleConstructionExecutionGate,
    OracleOperatorConsoleConstructionExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorConsoleConstructionAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe console execution accepted")
    except OracleOperatorConsoleConstructionExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-030 TEST")
    print(" OPERATOR CONSOLE CONSTRUCTION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorConsoleConstructionExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_console_construction_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_construction_execution_hash"
        }
    )
    assert first.operator_console_payload_hash == stable_hash(first.operator_console_payload)
    assert first.operator_console_artifact_type == OPERATOR_CONSOLE_ARTIFACT_TYPE
    assert first.operator_console_format == OPERATOR_CONSOLE_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    assert first.operator_console_payload["operator_console_id"] == first.operator_console_id
    assert first.operator_console_payload["operator_session_id"] == first.operator_session_id
    assert first.operator_console_payload["operator_session_payload_hash"] == first.operator_session_payload_hash
    assert first.operator_console_payload["read_only"] is True
    assert first.operator_console_payload["rendering_disabled"] is True
    assert first.operator_console_payload["presentation_rendering_disabled"] is True
    assert first.operator_console_payload["publication_disabled"] is True
    assert first.operator_console_payload["qseries_execution_disabled"] is True

    assert first.authorization_consumption_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.execution_package_type_verified
    assert first.operator_session_identity_verified
    assert first.operator_session_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.research_response_cardinality_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_console_construction_verified
    assert first.immutable_console_verified
    assert first.read_only_console_verified

    assert first.operator_session_result_certified
    assert first.operator_console_construction_ready
    assert first.operator_console_construction_authorized
    assert first.operator_console_construction_authorization_consumed
    assert first.operator_console_construction_allowed
    assert first.operator_console_construction_performed
    assert first.operator_console_certification_ready
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

    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_construction_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_session_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_construction_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_console_rendering_allowed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-029 console execution package consumed")
    print("[PASS] OOP-029 identity, hash, status, and scope verified")
    print("[PASS] Operator Session identity and payload hash verified")
    print("[PASS] Deterministic immutable Operator Console created")
    print("[PASS] Operator Console payload hash verified")
    print("[PASS] Read-only console construction performed")
    print("[PASS] Operator Console certification marked ready")
    print("[PASS] Console rendering remains disabled")
    print("[PASS] Presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe console packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
