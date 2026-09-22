from __future__ import annotations

from dataclasses import replace

from test_oop_023_oracle_operator_research_response_materialization_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_result_certification_gate import (
    OracleOperatorResearchResponseMaterializationResultCertificationGate,
)
from qseries_v2.oracle_operator.session.oracle_operator_session_construction_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    SESSION_PACKAGE_TYPE,
    OracleOperatorSessionConstructionAuthorizationGate,
    OracleOperatorSessionConstructionAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorResearchResponseMaterializationResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe session authorization accepted")
    except OracleOperatorSessionConstructionAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-024 TEST")
    print(" OPERATOR SESSION CONSTRUCTION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorSessionConstructionAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.operator_session_construction_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_session_construction_authorization_hash"
        }
    )

    assert first.source_research_response_result_certification_id == certification.research_response_materialization_result_certification_id
    assert first.source_research_response_result_certification_hash == certification.research_response_materialization_result_certification_hash
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.session_package_type == SESSION_PACKAGE_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert first.research_response_id == certification.research_response_id
    assert first.research_response_payload_hash == certification.research_response_payload_hash
    assert first.research_response_items == certification.research_response_items

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
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
    assert first.single_use_authorization_verified
    assert first.deterministic_authorization_verified
    assert first.read_only_boundary_verified

    assert first.research_response_result_certified
    assert first.operator_session_construction_ready
    assert first.operator_session_construction_authorized
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

    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_materialization_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_item_count=certification.research_response_item_count + 1,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        operator_session_construction_allowed=True,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-023 Research Response certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Research Response payload hash recomputed and verified")
    print("[PASS] Response identities, cardinality, and source hashes verified")
    print("[PASS] Immutable certified session input preserved")
    print("[PASS] Single-use Operator Session construction authorized")
    print("[PASS] Operator Session construction allowed but not performed")
    print("[PASS] Console, presentation, and publication remain disabled")
    print("[PASS] Q Series execution, orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe certifications rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
