from __future__ import annotations

from dataclasses import replace

from test_oop_046_oracle_operator_subsystem_completion_readiness_gate import (
    _presentation_certification,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_readiness_gate import (
    OracleOperatorSubsystemCompletionReadinessGate,
)
from qseries_v2.oracle_operator.oracle_operator_subsystem_completion_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFICATION_TYPE,
    FREEZE_RECORD_TYPE,
    OracleOperatorSubsystemCompletionCertificationGate,
    OracleOperatorSubsystemCompletionCertificationInvariantError,
    stable_hash,
)


def _readiness():
    return OracleOperatorSubsystemCompletionReadinessGate().evaluate(
        certification=_presentation_certification()
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe operator subsystem certification accepted")
    except OracleOperatorSubsystemCompletionCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-047 TEST")
    print(" ORACLE OPERATOR SUBSYSTEM")
    print(" COMPLETION CERTIFICATION GATE")
    print("=" * 40)

    readiness = _readiness()
    gate = OracleOperatorSubsystemCompletionCertificationGate()

    first = gate.certify(readiness=readiness)
    repeated = gate.certify(readiness=readiness)

    assert first == repeated
    assert first.oracle_operator_subsystem_completion_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "oracle_operator_subsystem_completion_certification_hash"
        }
    )
    assert first.freeze_record_payload_hash == stable_hash(first.freeze_record_payload)
    assert first.certification_status == CERTIFICATION_STATUS
    assert first.certification_type == CERTIFICATION_TYPE
    assert first.freeze_record_type == FREEZE_RECORD_TYPE

    payload = first.freeze_record_payload
    assert payload["freeze_record_id"] == first.freeze_record_id
    assert payload["source_completion_readiness_id"] == first.source_completion_readiness_id
    assert payload["source_completion_readiness_hash"] == first.source_completion_readiness_hash
    assert payload["query_boundary_complete"] is True
    assert payload["research_response_boundary_complete"] is True
    assert payload["session_boundary_complete"] is True
    assert payload["console_boundary_complete"] is True
    assert payload["presentation_boundary_complete"] is True
    assert payload["operator_subsystem_complete"] is True
    assert payload["operator_subsystem_completion_certified"] is True
    assert payload["operator_subsystem_frozen"] is True
    assert payload["further_operator_builds_required"] is False
    assert payload["read_only"] is True
    assert payload["qseries_handoff_disabled"] is True
    assert payload["qseries_execution_disabled"] is True
    assert payload["orders_disabled"] is True
    assert payload["funds_movement_disabled"] is True
    assert payload["portfolio_mutation_disabled"] is True

    assert first.readiness_identity_verified
    assert first.readiness_hash_verified
    assert first.readiness_status_verified
    assert first.readiness_type_verified
    assert first.readiness_record_type_verified
    assert first.readiness_record_identity_verified
    assert first.readiness_record_payload_hash_verified
    assert first.operator_namespace_verified
    assert first.query_boundary_verified
    assert first.research_response_boundary_verified
    assert first.session_boundary_verified
    assert first.console_boundary_verified
    assert first.presentation_boundary_verified
    assert first.publication_chain_completion_verified
    assert first.presentation_subsystem_completion_verified
    assert first.complete_lineage_verified
    assert first.deterministic_certification_verified
    assert first.immutable_freeze_record_verified
    assert first.read_only_operator_subsystem_verified

    assert first.operator_query_boundary_complete
    assert first.operator_research_response_boundary_complete
    assert first.operator_session_boundary_complete
    assert first.operator_console_boundary_complete
    assert first.operator_presentation_boundary_complete
    assert first.operator_presentation_subsystem_completion_certified
    assert first.operator_presentation_subsystem_frozen
    assert first.oracle_operator_subsystem_completion_ready
    assert first.oracle_operator_subsystem_completion_certified
    assert first.oracle_operator_subsystem_frozen
    assert not first.further_operator_builds_required

    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed

    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        oracle_operator_subsystem_completion_readiness_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        readiness_status="wrong_status",
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        readiness_record_payload_hash="0" * 64,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        oracle_operator_subsystem_completion_ready=False,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        further_operator_builds_required=False,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        qseries_execution_allowed=True,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        order_creation_allowed=True,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        funds_movement_allowed=True,
    )))
    _reject(lambda: gate.certify(readiness=replace(
        readiness,
        portfolio_mutation_allowed=True,
    )))

    print("[PASS] Actual OOP-046 completion readiness consumed")
    print("[PASS] Readiness identity, hash, status, type, and record verified")
    print("[PASS] Query, Research Response, Session, Console, and Presentation lineage preserved")
    print("[PASS] Immutable terminal Oracle Operator freeze record created")
    print("[PASS] Oracle Operator subsystem completion certified")
    print("[PASS] Oracle Operator subsystem frozen")
    print("[PASS] No further Oracle Operator builds required")
    print("[PASS] Read-only guarantees preserved")
    print("[PASS] Q Series handoff and execution disabled")
    print("[PASS] Orders, funds, and portfolio mutation disabled")
    print("[PASS] Tampered and unsafe readiness inputs rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
