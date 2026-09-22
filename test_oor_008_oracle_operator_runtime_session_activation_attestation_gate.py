from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_gate import (
    ACTIVATION_STATUS,
    ACTIVATION_TYPE,
    OracleOperatorRuntimeSessionActivation,
    stable_hash as activation_hash,
)
from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_attestation_gate import (
    ATTESTATION_STATUS,
    ATTESTATION_TYPE,
    OracleOperatorRuntimeSessionActivationAttestationGate,
    OracleOperatorRuntimeSessionActivationAttestationInvariantError,
    stable_hash,
)


def _activation() -> OracleOperatorRuntimeSessionActivation:
    requested_at = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)
    admitted_at = requested_at + timedelta(seconds=1)
    assembled_at = admitted_at + timedelta(seconds=1)
    authorized_at = assembled_at + timedelta(seconds=1)
    consumed_at = authorized_at + timedelta(seconds=1)
    activated_at = consumed_at + timedelta(seconds=1)
    body = {
        "activation_id": "1" * 64,
        "consumption_id": "2" * 64,
        "consumption_hash": "3" * 64,
        "authorization_id": "4" * 64,
        "authorization_hash": "5" * 64,
        "session_id": "6" * 64,
        "session_hash": "7" * 64,
        "admission_id": "8" * 64,
        "admission_hash": "9" * 64,
        "request_id": "a" * 64,
        "request_hash": "b" * 64,
        "dependency_receipt_id": "c" * 64,
        "dependency_receipt_hash": "d" * 64,
        "source_operator_completion_certification_id": "e" * 64,
        "runtime_namespace": "oracle_operator_runtime",
        "requester_id": "operator:test",
        "correlation_id": "correlation:test",
        "mode": "query",
        "query_text": "Show the highest-priority certified read-only opportunity.",
        "requested_at": requested_at,
        "admitted_at": admitted_at,
        "assembled_at": assembled_at,
        "authorized_at": authorized_at,
        "consumed_at": consumed_at,
        "activated_at": activated_at,
        "consumption_identity_verified": True,
        "consumption_hash_verified": True,
        "consumption_contract_verified": True,
        "single_consumption_scope_verified": True,
        "single_activation_scope_verified": True,
        "read_only_boundary_verified": True,
        "deterministic_boundary_verified": True,
        "immutable_result_boundary_verified": True,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "activation_type": ACTIVATION_TYPE,
        "activation_status": ACTIVATION_STATUS,
    }
    return OracleOperatorRuntimeSessionActivation(
        **body,
        activation_hash=activation_hash(body),
    )


def _reject(callable_):
    try:
        callable_()
        raise AssertionError("unsafe runtime activation attestation accepted")
    except OracleOperatorRuntimeSessionActivationAttestationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOR-008 TEST")
    print(" ORACLE OPERATOR RUNTIME SESSION")
    print(" ACTIVATION ATTESTATION GATE")
    print("=" * 40)
    activation = _activation()
    gate = OracleOperatorRuntimeSessionActivationAttestationGate()
    attested_at = activation.activated_at + timedelta(seconds=1)
    first = gate.attest(activation=activation, attested_at=attested_at)
    repeated = gate.attest(activation=activation, attested_at=attested_at)
    assert first == repeated
    assert first.attestation_type == ATTESTATION_TYPE
    assert first.attestation_status == ATTESTATION_STATUS
    assert first.activation_id == activation.activation_id
    assert first.activation_hash == activation.activation_hash
    assert first.attestation_hash == stable_hash(
        {key: value for key, value in asdict(first).items() if key != "attestation_hash"}
    )
    assert first.activation_identity_verified
    assert first.activation_hash_verified
    assert first.activation_contract_verified
    assert first.complete_runtime_lineage_verified
    assert first.single_activation_scope_verified
    assert first.single_attestation_scope_verified
    assert first.read_only_boundary_verified
    assert first.deterministic_boundary_verified
    assert first.immutable_result_boundary_verified
    assert not any(
        (
            first.runtime_serving_allowed,
            first.network_listener_allowed,
            first.database_connection_allowed,
            first.publication_allowed,
            first.qseries_handoff_allowed,
            first.qseries_execution_allowed,
            first.order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        )
    )
    _reject(
        lambda: gate.attest(
            activation=replace(activation, activation_hash="0" * 64),
            attested_at=attested_at,
        )
    )
    _reject(
        lambda: gate.attest(
            activation=replace(activation, qseries_execution_allowed=True),
            attested_at=attested_at,
        )
    )
    _reject(
        lambda: gate.attest(
            activation=activation,
            attested_at=activation.activated_at - timedelta(seconds=1),
        )
    )
    _reject(
        lambda: gate.attest(
            activation=activation,
            attested_at=datetime(2026, 7, 28, 12, 0),
        )
    )
    print("[PASS] Actual OOR-007 runtime session activation consumed")
    print("[PASS] Activation identity and payload hash verified")
    print("[PASS] Complete OOR-001 through OOR-007 lineage preserved")
    print("[PASS] Deterministic single-activation attestation certified")
    print("[PASS] Immutable read-only activation attestation materialized")
    print("[PASS] Runtime serving and network listener remain disabled")
    print("[PASS] Database connection and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    print("[PASS] Tampered, premature, and unsafe attestation rejected")
    print("[DONE] OOR-008 ORACLE OPERATOR RUNTIME SESSION ACTIVATION ATTESTATION GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
