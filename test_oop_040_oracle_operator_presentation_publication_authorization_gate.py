from __future__ import annotations

from dataclasses import replace

from test_oop_039_oracle_operator_presentation_rendering_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_rendering_result_certification_gate import (
    OracleOperatorPresentationRenderingResultCertificationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_gate import (
    AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE,
    PUBLICATION_INPUT_PACKAGE_TYPE,
    OracleOperatorPresentationPublicationAuthorizationGate,
    OracleOperatorPresentationPublicationAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorPresentationRenderingResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication authorization accepted")
    except OracleOperatorPresentationPublicationAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-040 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorPresentationPublicationAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.operator_presentation_publication_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_authorization_hash"
        }
    )

    assert first.source_operator_presentation_rendering_result_certification_id == certification.operator_presentation_rendering_result_certification_id
    assert first.source_operator_presentation_rendering_result_certification_hash == certification.operator_presentation_rendering_result_certification_hash
    assert first.authorization_type == AUTHORIZATION_TYPE
    assert first.publication_input_package_type == PUBLICATION_INPUT_PACKAGE_TYPE
    assert first.authorization_status == AUTHORIZATION_STATUS
    assert first.rendered_presentation_id == certification.rendered_presentation_id
    assert first.rendered_presentation_payload_hash == certification.rendered_presentation_payload_hash
    assert first.rendered_presentation_payload == certification.rendered_presentation_payload

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
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
    assert first.immutable_publication_input_verified
    assert first.single_use_authorization_verified
    assert first.deterministic_authorization_verified
    assert first.read_only_boundary_verified

    assert first.operator_presentation_rendering_result_certified
    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_allowed
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
        operator_presentation_rendering_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        research_response_item_count=certification.research_response_item_count + 1,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        publication_allowed=True,
    )))
    _reject(lambda: gate.authorize(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-039 presentation certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Rendered presentation identity, payload hash, format, and sections verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable certified publication input preserved")
    print("[PASS] Single-use presentation publication authorized")
    print("[PASS] Publication allowed but not performed")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe certifications rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
