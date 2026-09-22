from __future__ import annotations

from dataclasses import replace

from test_oop_024_oracle_operator_session_construction_authorization_gate import (
    _certification,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_gate import (
    OracleOperatorSessionConstructionAuthorizationGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorSessionConstructionAuthorizationConsumptionGate,
    OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorSessionConstructionAuthorizationGate().authorize(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session authorization consumption accepted")
    except OracleOperatorSessionConstructionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-025 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorSessionConstructionAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.operator_session_construction_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_consumption_hash"
        }
    )

    assert first.source_operator_session_construction_authorization_id == authorization.operator_session_construction_authorization_id
    assert first.source_operator_session_construction_authorization_hash == authorization.operator_session_construction_authorization_hash
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.research_response_id == authorization.research_response_id
    assert first.research_response_payload_hash == authorization.research_response_payload_hash
    assert first.research_response_items == authorization.research_response_items

    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.authorization_type_verified
    assert first.session_package_type_verified
    assert first.research_response_identity_verified
    assert first.research_response_payload_hash_verified
    assert first.response_item_cardinality_verified
    assert first.response_item_identity_verified
    assert first.source_result_hashes_verified
    assert first.certified_payload_preservation_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_session_input_verified
    assert first.single_use_consumption_verified
    assert first.immutable_execution_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_boundary_verified

    assert first.research_response_result_certified
    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
    assert first.operator_session_construction_authorization_consumed
    assert first.operator_session_construction_allowed
    assert not first.operator_session_construction_performed
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
        operator_session_construction_authorization_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        authorization_status="wrong_status",
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_item_count=authorization.research_response_item_count + 1,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_session_construction_performed=True,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-024 session authorization consumed")
    print("[PASS] Authorization identity, hash, status, and type verified")
    print("[PASS] Research Response payload hash recomputed and verified")
    print("[PASS] Session input identities, cardinality, and source hashes verified")
    print("[PASS] Single-use immutable session execution package created")
    print("[PASS] Session authorization marked consumed")
    print("[PASS] Operator Session construction allowed but not performed")
    print("[PASS] Console, presentation, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
