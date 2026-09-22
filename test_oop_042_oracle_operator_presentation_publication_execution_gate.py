from __future__ import annotations

from dataclasses import replace

from test_oop_041_oracle_operator_presentation_publication_authorization_consumption_gate import (
    _authorization,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_authorization_consumption_gate import (
    OracleOperatorPresentationPublicationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    EXECUTION_STATUS,
    PUBLISHED_PRESENTATION_ARTIFACT_TYPE,
    PUBLISHED_PRESENTATION_FORMAT,
    OracleOperatorPresentationPublicationExecutionGate,
    OracleOperatorPresentationPublicationExecutionInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorPresentationPublicationAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication execution accepted")
    except OracleOperatorPresentationPublicationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-042 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" EXECUTION GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorPresentationPublicationExecutionGate()

    first = gate.execute(consumption=consumption)
    repeated = gate.execute(consumption=consumption)

    assert first == repeated
    assert first.operator_presentation_publication_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_execution_hash"
        }
    )
    assert first.published_presentation_payload_hash == stable_hash(
        first.published_presentation_payload
    )
    assert first.published_presentation_artifact_type == PUBLISHED_PRESENTATION_ARTIFACT_TYPE
    assert first.published_presentation_format == PUBLISHED_PRESENTATION_FORMAT
    assert first.execution_status == EXECUTION_STATUS

    payload = first.published_presentation_payload
    assert payload["published_presentation_id"] == first.published_presentation_id
    assert payload["source_rendered_presentation_id"] == first.rendered_presentation_id
    assert payload["source_rendered_presentation_payload_hash"] == first.rendered_presentation_payload_hash
    assert payload["research_response_id"] == first.research_response_id
    assert payload["research_response_item_count"] == first.research_response_item_count
    assert payload["read_only"] is True
    assert payload["publication_completed"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.publication_execution_package_type_verified
    assert first.rendered_presentation_identity_verified
    assert first.rendered_presentation_payload_hash_verified
    assert first.rendered_presentation_sections_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_publication_verified
    assert first.immutable_published_presentation_verified
    assert first.read_only_publication_verified

    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_authorization_consumed
    assert first.publication_allowed
    assert first.publication_performed
    assert first.publication_result_certification_ready
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
        operator_presentation_publication_consumption_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        consumption_status="wrong_status",
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        rendered_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        research_response_item_count=consumption.research_response_item_count + 1,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        publication_performed=True,
    )))
    _reject(lambda: gate.execute(consumption=replace(
        consumption,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-041 publication execution package consumed")
    print("[PASS] Consumption identity, hash, status, and package type verified")
    print("[PASS] Rendered presentation identity, payload hash, and sections verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Deterministic immutable published presentation created")
    print("[PASS] Published presentation payload hash verified")
    print("[PASS] Publication performed through read-only boundary")
    print("[PASS] Publication result certification marked ready")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe publication packages rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
