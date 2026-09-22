from __future__ import annotations

from dataclasses import replace

from test_oop_044_oracle_operator_presentation_publication_completion_attestation_gate import (
    _certification,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_publication_completion_attestation_gate import (
    OracleOperatorPresentationPublicationCompletionAttestationGate,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_subsystem_completion_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    FREEZE_RECORD_TYPE,
    OracleOperatorPresentationSubsystemCompletionCertificationGate,
    OracleOperatorPresentationSubsystemCompletionCertificationInvariantError,
    stable_hash,
)


def _attestation():
    return OracleOperatorPresentationPublicationCompletionAttestationGate().attest(
        certification=_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe subsystem completion certification accepted")
    except OracleOperatorPresentationSubsystemCompletionCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-045 TEST")
    print(" OPERATOR PRESENTATION SUBSYSTEM")
    print(" COMPLETION CERTIFICATION GATE")
    print("=" * 40)

    attestation = _attestation()
    gate = OracleOperatorPresentationSubsystemCompletionCertificationGate()

    first = gate.certify(attestation=attestation)
    repeated = gate.certify(attestation=attestation)

    assert first == repeated
    assert first.oracle_operator_presentation_subsystem_completion_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "oracle_operator_presentation_subsystem_completion_certification_hash"
        }
    )
    assert first.freeze_record_payload_hash == stable_hash(first.freeze_record_payload)
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.freeze_record_type == FREEZE_RECORD_TYPE
    assert first.certification_status == CERTIFICATION_STATUS

    payload = first.freeze_record_payload
    assert payload["freeze_record_id"] == first.freeze_record_id
    assert payload["completion_record_id"] == first.completion_record_id
    assert payload["published_presentation_id"] == first.published_presentation_id
    assert payload["publication_chain_complete"] is True
    assert payload["presentation_subsystem_complete"] is True
    assert payload["presentation_subsystem_frozen"] is True
    assert payload["further_presentation_certification_required"] is False
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.attestation_identity_verified
    assert first.attestation_hash_verified
    assert first.attestation_status_verified
    assert first.attestation_type_verified
    assert first.completion_record_type_verified
    assert first.completion_record_identity_verified
    assert first.completion_record_payload_hash_verified
    assert first.published_presentation_identity_verified
    assert first.published_presentation_payload_hash_verified
    assert first.publication_chain_completion_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_certification_verified
    assert first.immutable_freeze_record_verified
    assert first.read_only_subsystem_verified

    assert first.publication_result_certified
    assert first.publication_completion_attested
    assert first.presentation_publication_chain_complete
    assert first.operator_presentation_subsystem_completion_ready
    assert first.operator_presentation_subsystem_completion_certified
    assert first.operator_presentation_subsystem_frozen
    assert not first.further_presentation_certification_required

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        operator_presentation_publication_completion_attestation_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        attestation_status="wrong_status",
    )))
    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        completion_record_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        presentation_publication_chain_complete=False,
    )))
    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        qseries_handoff_allowed=True,
    )))
    _reject(lambda: gate.certify(attestation=replace(
        attestation,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-044 completion attestation consumed")
    print("[PASS] Attestation identity, hash, status, and type verified")
    print("[PASS] Completion record identity and payload hash verified")
    print("[PASS] Published presentation identity and payload hash preserved")
    print("[PASS] Complete Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable terminal presentation freeze record created")
    print("[PASS] Operator Presentation subsystem completion certified")
    print("[PASS] Operator Presentation subsystem frozen")
    print("[PASS] No further presentation certification required")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe completion attestations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
