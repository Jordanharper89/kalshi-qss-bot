from __future__ import annotations

from dataclasses import replace

from test_oop_025_oracle_operator_session_construction_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_consumption_gate import (
    OracleOperatorSessionConstructionAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_execution_gate import (
    EXECUTION_STATUS,
    OPERATOR_SESSION_ARTIFACT_TYPE,
    OPERATOR_SESSION_FORMAT,
    OracleOperatorSessionConstructionExecutionGate,
    OracleOperatorSessionConstructionExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorSessionConstructionAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session execution accepted")
    except OracleOperatorSessionConstructionExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-026 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorSessionConstructionExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_session_construction_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_execution_hash"
        }
    )
    assert first.operator_session_payload_hash == stable_hash(first.operator_session_payload)
    assert first.operator_session_artifact_type == OPERATOR_SESSION_ARTIFACT_TYPE
    assert first.operator_session_format == OPERATOR_SESSION_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    assert first.operator_session_payload["operator_session_id"] == first.operator_session_id
    assert first.operator_session_payload["research_response_id"] == first.research_response_id
    assert first.operator_session_payload["research_response_payload_hash"] == first.research_response_payload_hash
    assert first.operator_session_payload["read_only"] is True
    assert first.operator_session_payload["console_rendering_disabled"] is True
    assert first.operator_session_payload["presentation_rendering_disabled"] is True
    assert first.operator_session_payload["publication_disabled"] is True
    assert first.operator_session_payload["qseries_execution_disabled"] is True

    assert first.authorization_consumption_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.execution_package_type_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.response_item_cardinality_verified
    assert first.deterministic_session_construction_verified
    assert first.immutable_session_verified
    assert first.read_only_session_verified

    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
    assert first.operator_session_construction_authorization_consumed
    assert first.operator_session_construction_allowed
    assert first.operator_session_construction_performed
    assert first.operator_session_certification_ready
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
        operator_session_construction_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_item_count=consumption.research_response_item_count + 1,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        operator_session_construction_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-025 session execution package consumed")
    print("[PASS] OOP-025 identity, hash, status, and scope verified")
    print("[PASS] Certified Research Response payload hash verified")
    print("[PASS] Deterministic immutable Operator Session created")
    print("[PASS] Operator Session payload hash verified")
    print("[PASS] Read-only session construction performed")
    print("[PASS] Operator Session certification marked ready")
    print("[PASS] Console, presentation, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe session packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
