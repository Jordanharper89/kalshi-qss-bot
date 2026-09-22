from __future__ import annotations

from dataclasses import replace

from test_oop_027_oracle_operator_session_construction_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_result_certification_gate import (
    OracleOperatorSessionConstructionResultCertificationGate,
)
from qseries_v2.oracle_operator.console.oracle_operator_console_construction_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    CONSOLE_INPUT_PACKAGE_TYPE,
    OracleOperatorConsoleConstructionAuthorizationGate,
    OracleOperatorConsoleConstructionAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorSessionConstructionResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe console construction authorization accepted")
    except OracleOperatorConsoleConstructionAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-028 TEST")
    print(" OPERATOR CONSOLE CONSTRUCTION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorConsoleConstructionAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.operator_console_construction_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_console_construction_authorization_hash"
        }
    )

    assert first.source_operator_session_result_certification_id == certification.operator_session_construction_result_certification_id
    assert first.source_operator_session_result_certification_hash == certification.operator_session_construction_result_certification_hash
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.console_input_package_type == CONSOLE_INPUT_PACKAGE_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert first.operator_session_id == certification.operator_session_id
    assert first.operator_session_payload_hash == certification.operator_session_payload_hash
    assert first.operator_session_payload == certification.operator_session_payload

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
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
    assert first.immutable_console_input_verified
    assert first.single_use_authorization_verified
    assert first.deterministic_authorization_verified
    assert first.read_only_boundary_verified

    assert first.operator_session_result_certified
    assert first.operator_console_construction_ready
    assert first.operator_console_construction_authorized
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

    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_session_construction_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_session_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_item_count=certification.research_response_item_count + 1,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_console_rendering_allowed=True,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-027 Operator Session certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Operator Session identity and payload hash verified")
    print("[PASS] Research Response lineage and cardinality preserved")
    print("[PASS] Immutable certified console input preserved")
    print("[PASS] Single-use Operator Console construction authorized")
    print("[PASS] Console construction allowed but not performed")
    print("[PASS] Console rendering remains disabled")
    print("[PASS] Presentation, publication, and Q Series execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe certifications rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
