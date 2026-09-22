from __future__ import annotations

from dataclasses import replace

from test_oop_043_oracle_operator_presentation_publication_result_certification_gate import (
    _execution,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_result_certification_gate import (
    OracleOperatorPresentationPublicationResultCertificationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_completion_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    COMPLETION_RECORD_TYPE,
    OracleOperatorPresentationPublicationCompletionAttestationGate,
    OracleOperatorPresentationPublicationCompletionAttestationInvariantError,
    stable_hash,
)


def _certification():
    return OracleOperatorPresentationPublicationResultCertificationGate().certify(
        execution=_execution()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe completion attestation accepted")
    except OracleOperatorPresentationPublicationCompletionAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-044 TEST")
    print(" OPERATOR PRESENTATION PUBLICATION")
    print(" COMPLETION ATTESTATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorPresentationPublicationCompletionAttestationGate()

    first = gate.attest(certification=certification)
    repeated = gate.attest(certification=certification)

    assert first == repeated
    assert first.operator_presentation_publication_completion_attestation_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "operator_presentation_publication_completion_attestation_hash"
        }
    )
    assert first.completion_record_payload_hash == stable_hash(
        first.completion_record_payload
    )
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.completion_record_type == COMPLETION_RECORD_TYPE
    assert first.attestation_status == ATTESTATION_STATUS

    payload = first.completion_record_payload
    assert payload["completion_record_id"] == first.completion_record_id
    assert payload["published_presentation_id"] == first.published_presentation_id
    assert payload["published_presentation_payload_hash"] == first.published_presentation_payload_hash
    assert payload["publication_complete"] is True
    assert payload["presentation_publication_chain_complete"] is True
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.certification_type_verified
    assert first.published_presentation_identity_verified
    assert first.published_presentation_payload_hash_verified
    assert first.published_presentation_artifact_type_verified
    assert first.published_presentation_format_verified
    assert first.publication_completion_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_attestation_verified
    assert first.immutable_completion_record_verified
    assert first.read_only_completion_verified
    assert first.publication_result_certified
    assert first.publication_completion_attested
    assert first.presentation_publication_chain_complete
    assert first.operator_presentation_subsystem_completion_ready

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.attest(certification=replace(
        certification,
        operator_presentation_publication_result_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        published_presentation_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        publication_result_certified=False,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        qseries_handoff_allowed=True,
    )))
    _reject(lambda: gate.attest(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-043 publication certification consumed")
    print("[PASS] Certification identity, hash, status, and type verified")
    print("[PASS] Published presentation identity, payload hash, artifact type, and format verified")
    print("[PASS] Publication completion and safety boundaries verified")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable terminal completion record created")
    print("[PASS] Presentation publication chain marked complete")
    print("[PASS] Operator presentation subsystem completion marked ready")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe completion inputs rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
