from __future__ import annotations

from dataclasses import replace

from test_oop_040_oracle_operator_presentation_publication_authorization_gate import (
    _certification,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_gate import (
    OracleOperatorPresentationPublicationAuthorizationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    PUBLICATION_EXECUTION_PACKAGE_TYPE,
    OracleOperatorPresentationPublicationAuthorizationConsumptionGate,
    OracleOperatorPresentationPublicationAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorPresentationPublicationAuthorizationGate().authorize(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication authorization consumption accepted")
    except OracleOperatorPresentationPublicationAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-041 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorPresentationPublicationAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.operator_presentation_publication_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_consumption_hash"
        }
    )

    assert first.source_operator_presentation_publication_authorization_id == authorization.operator_presentation_publication_authorization_id
    assert first.source_operator_presentation_publication_authorization_hash == authorization.operator_presentation_publication_authorization_hash
    assert first.publication_execution_package_type == PUBLICATION_EXECUTION_PACKAGE_TYPE
    assert first.consumption_status == CONSUMPTION_STATUS
    assert first.rendered_presentation_id == authorization.rendered_presentation_id
    assert first.rendered_presentation_payload_hash == authorization.rendered_presentation_payload_hash
    assert first.rendered_presentation_payload == authorization.rendered_presentation_payload

    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.authorization_type_verified
    assert first.publication_input_package_type_verified
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
    assert first.single_use_consumption_verified
    assert first.immutable_publication_execution_package_verified
    assert first.deterministic_consumption_verified
    assert first.read_only_boundary_verified

    assert first.operator_presentation_rendering_result_certified
    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_authorization_consumed
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

    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        operator_presentation_publication_authorization_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        authorization_status="wrong_status",
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        research_response_item_count=authorization.research_response_item_count + 1,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        publication_performed=True,
    )))
    _reject(lambda: gate.consume(authorization=replace(
        authorization,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-040 publication authorization consumed")
    print("[PASS] Authorization identity, hash, status, and type verified")
    print("[PASS] Rendered presentation identity, payload hash, format, and sections verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Single-use immutable publication execution package created")
    print("[PASS] Publication authorization marked consumed")
    print("[PASS] Publication allowed but not performed")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
