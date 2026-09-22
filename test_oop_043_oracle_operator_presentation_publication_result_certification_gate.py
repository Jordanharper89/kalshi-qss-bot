from __future__ import annotations

from dataclasses import replace

from test_oop_042_oracle_operator_presentation_publication_execution_gate import (
    _consumption,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_execution_gate import (
    OracleOperatorPresentationPublicationExecutionGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    OracleOperatorPresentationPublicationResultCertificationGate,
    OracleOperatorPresentationPublicationResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorPresentationPublicationExecutionGate().execute(
        consumption=_consumption()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe publication certification accepted")
    except OracleOperatorPresentationPublicationResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-043 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" RESULT CERTIFICATION GATE")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorPresentationPublicationResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.operator_presentation_publication_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_result_certification_hash"
        }
    )
    assert first.published_presentation_payload_hash == stable_hash(
        first.published_presentation_payload
    )
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.published_presentation_id == execution.published_presentation_id
    assert first.published_presentation_payload == execution.published_presentation_payload

    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.published_presentation_identity_verified
    assert first.published_presentation_payload_hash_verified
    assert first.published_presentation_artifact_type_verified
    assert first.published_presentation_format_verified
    assert first.source_rendered_presentation_identity_verified
    assert first.source_rendered_presentation_payload_hash_verified
    assert first.research_response_identity_verified
    assert first.research_response_cardinality_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_published_presentation_verified
    assert first.read_only_publication_verified
    assert first.deterministic_certification_verified

    assert first.publication_authorization_ready
    assert first.publication_authorized
    assert first.publication_authorization_consumed
    assert first.publication_allowed
    assert first.publication_performed
    assert first.publication_result_certified
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.certify(execution=replace(
        execution,
        operator_presentation_publication_execution_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        execution_status="wrong_status",
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        published_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        research_response_item_count=execution.research_response_item_count + 1,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        publication_performed=False,
    )))
    _reject(lambda: gate.certify(execution=replace(
        execution,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-042 published presentation execution consumed")
    print("[PASS] Execution identity, hash, status, artifact type, and format verified")
    print("[PASS] Published presentation identity and payload hash verified")
    print("[PASS] Source rendered presentation identity and hash verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable read-only publication result certified")
    print("[PASS] Publication completion certified")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe publication executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
