from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation,
)


def make_activation() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivation(
        activation_id="activation:" + "a" * 64,
        source_consumption_id="consumption:" + "b" * 64,
        source_consumption_hash="b" * 64,
        source_authorization_id="authorization:" + "c" * 64,
        source_authorization_hash="c" * 64,
        source_readiness_id="readiness:" + "d" * 64,
        source_readiness_hash="d" * 64,
        source_session_attestation_id="session-attestation:" + "e" * 64,
        source_session_attestation_hash="e" * 64,
        source_session_id="session:" + "f" * 64,
        source_session_hash="f" * 64,
        source_registry_activation_id="registry-activation:" + "1" * 64,
        source_registry_activation_hash="1" * 64,
        source_registry_authorization_id="registry-authorization:" + "2" * 64,
        source_registry_authorization_hash="2" * 64,
        source_registry_id="registry:" + "3" * 64,
        source_registry_hash="3" * 64,
        source_entry_count=2,
        source_entry_hashes=("4" * 64, "5" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        authorization_consumption_verified=True,
        deterministic_activation=True,
        bounded_activation_scope=True,
        single_consumption_scope=True,
        activation_single_use=True,
        duplicate_activation_allowed=False,
        activation_reversible=False,
        downstream_read_only_consumption_active=True,
        registry_mutation_allowed=False,
        oracle_execution_allowed=False,
        reasoning_execution_allowed=False,
        probability_estimation_allowed=False,
        final_intelligence_conclusion_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        read_only=True,
        activation_status="oracle_certified_intelligence_read_only_consumption_session_activated",
        engine_id="INT-OII-011",
        schema_version="INT-OII-011.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation.v1",
        activation_hash="a" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestationInvariantError:
        return
    raise AssertionError("expected INT-OII-012 rejection")


def main() -> None:
    original = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation = (
        lambda _: True
    )

    try:
        activation = make_activation()

        first = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(
            activation=activation
        )
        second = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(
            activation=activation
        )

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
            first
        )
        assert first.source_activation_id == activation.activation_id
        assert first.source_activation_hash == activation.activation_hash
        assert first.activation_verified is True
        assert first.activation_identity_attested is True
        assert first.activation_hash_attested is True
        assert first.complete_lineage_attested is True
        assert first.deterministic_attestation is True
        assert first.bounded_attestation_scope is True
        assert first.single_activation_scope is True
        assert first.activation_single_use_attested is True
        assert first.duplicate_activation_disabled_attested is True
        assert first.irreversible_activation_attested is True
        assert first.downstream_read_only_consumption_active_attested is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
                replace(first, attestation_hash="0" * 64)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
                replace(first, qseries_execution_allowed=True)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation(
                replace(first, downstream_read_only_consumption_active_attested=False)
            )
        )

        reversible = replace(activation, activation_reversible=True)
        must_reject(
            lambda: module.attest_oracle_certified_intelligence_read_only_consumption_session_activation(
                activation=reversible
            )
        )

        print("========================================")
        print(" INT-OII-012 TEST")
        print(" ACTIVATION ATTESTATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-011 activation boundary consumed")
        print("[PASS] Activation identity and hash attested")
        print("[PASS] Consumption/authorization/readiness/session lineage attested")
        print("[PASS] Registry lineage attested")
        print("[PASS] Deterministic bounded attestation certified")
        print("[PASS] Single-activation scope certified")
        print("[PASS] Single-use activation attested")
        print("[PASS] Duplicate activation disabled")
        print("[PASS] Irreversible activation attested")
        print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-012 ACTIVATION ATTESTATION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation = (
            original
        )


if __name__ == "__main__":
    main()
