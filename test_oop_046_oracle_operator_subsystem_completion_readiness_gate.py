from __future__ import annotations

from dataclasses import replace

from test_oop_045_oracle_operator_presentation_subsystem_completion_certification_gate import (
    _attestation,
)
from qseries_v2.oracle_operator.presentation.oracle_operator_presentation_subsystem_completion_certification_gate import (
    OracleOperatorPresentationSubsystemCompletionCertificationGate,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_readiness_gate import (
    READINESS_RECORD_TYPE,
    READINESS_STATUS,
    READINESS_TYPE,
    OracleOperatorSubsystemCompletionReadinessGate,
    OracleOperatorSubsystemCompletionReadinessInvariantError,
    stable_hash,
)


def _presentation_certification():
    return OracleOperatorPresentationSubsystemCompletionCertificationGate().certify(
        attestation=_attestation()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe operator subsystem readiness accepted")
    except OracleOperatorSubsystemCompletionReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-046 TEST")
    print(" ORACLE OPERATOR SUBSYSTEM")
    print(" COMPLETION READINESS GATE")
    print("=" * 40)

    certification = _presentation_certification()
    gate = OracleOperatorSubsystemCompletionReadinessGate()

    first = gate.evaluate(certification=certification)
    repeated = gate.evaluate(certification=certification)

    assert first == repeated
    assert first.oracle_operator_subsystem_completion_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "oracle_operator_subsystem_completion_readiness_hash"
        }
    )
    assert first.readiness_record_payload_hash == stable_hash(first.readiness_record_payload)
    assert first.readiness_type == READINESS_TYPE
    assert first.readiness_record_type == READINESS_RECORD_TYPE
    assert first.readiness_status == READINESS_STATUS

    payload = first.readiness_record_payload
    assert payload["readiness_record_id"] == first.readiness_record_id
    assert payload["operator_namespace"] == first.operator_namespace
    assert payload["presentation_subsystem_completion_certification_id"] == first.source_presentation_subsystem_completion_certification_id
    assert payload["query_boundary_complete"] is True
    assert payload["research_response_boundary_complete"] is True
    assert payload["session_boundary_complete"] is True
    assert payload["console_boundary_complete"] is True
    assert payload["presentation_boundary_complete"] is True
    assert payload["operator_subsystem_completion_ready"] is True
    assert payload["operator_subsystem_completion_certified"] is False
    assert payload["further_operator_builds_required"] is True
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.presentation_certification_identity_verified
    assert first.presentation_certification_hash_verified
    assert first.presentation_certification_status_verified
    assert first.presentation_certification_type_verified
    assert first.presentation_freeze_record_type_verified
    assert first.presentation_freeze_record_identity_verified
    assert first.presentation_freeze_record_payload_hash_verified
    assert first.operator_namespace_verified
    assert first.presentation_namespace_verified
    assert first.query_boundary_verified
    assert first.research_response_boundary_verified
    assert first.session_boundary_verified
    assert first.console_boundary_verified
    assert first.presentation_boundary_verified
    assert first.publication_chain_completion_verified
    assert first.complete_lineage_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.deterministic_readiness_verified
    assert first.immutable_readiness_record_verified
    assert first.read_only_operator_subsystem_verified

    assert first.operator_presentation_subsystem_completion_certified
    assert first.operator_presentation_subsystem_frozen
    assert first.operator_query_boundary_complete
    assert first.operator_research_response_boundary_complete
    assert first.operator_session_boundary_complete
    assert first.operator_console_boundary_complete
    assert first.operator_presentation_boundary_complete
    assert first.oracle_operator_subsystem_completion_ready
    assert not first.oracle_operator_subsystem_completion_certified
    assert first.further_operator_builds_required

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        oracle_operator_presentation_subsystem_completion_certification_hash="0" * 64,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        certification_status="wrong_status",
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        freeze_record_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        operator_presentation_subsystem_frozen=False,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        further_presentation_certification_required=True,
    )))
    _reject(lambda: gate.evaluate(certification=replace(
        certification,
        qseries_execution_allowed=True,
    )))

    print("[PASS] Actual OOP-045 Presentation subsystem certification consumed")
    print("[PASS] Presentation certification identity, hash, status, and type verified")
    print("[PASS] Presentation freeze record identity and payload hash verified")
    print("[PASS] Query, Research Response, Session, Console, and Presentation boundaries verified")
    print("[PASS] Complete Oracle Operator lineage preserved")
    print("[PASS] Immutable terminal subsystem readiness record created")
    print("[PASS] Oracle Operator subsystem marked completion-ready")
    print("[PASS] Final subsystem certification remains pending")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe readiness inputs rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
