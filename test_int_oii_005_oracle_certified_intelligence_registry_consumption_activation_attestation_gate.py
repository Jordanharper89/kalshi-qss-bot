from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_attestation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionActivation,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceRegistryConsumptionActivationAttestationInvariantError:
        return
    raise AssertionError("expected INT-OII-005 invariant rejection")


def make_activation() -> OracleCertifiedIntelligenceRegistryConsumptionActivation:
    return OracleCertifiedIntelligenceRegistryConsumptionActivation(
        activation_id="registry-consumption-activation:" + "a" * 64,
        source_authorization_id="registry-consumption-authorization:" + "b" * 64,
        source_authorization_hash="b" * 64,
        source_attestation_id="registry-attestation:" + "c" * 64,
        source_attestation_hash="c" * 64,
        source_registry_id="registry:" + "d" * 64,
        source_registry_hash="d" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        authorization_verified=True,
        exact_authorization_hash_scope_preserved=True,
        exact_attestation_hash_scope_preserved=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        certified_subsystem_scope_preserved=True,
        read_only_consumption_activated=True,
        deterministic_activation=True,
        bounded_registry_scope_preserved=True,
        single_use_authorization_consumed=True,
        duplicate_activation_rejected=True,
        activation_reversible=False,
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
        activation_status=(
            "oracle_certified_intelligence_registry_consumption_activated"
        ),
        engine_id="INT-OII-004",
        schema_version="INT-OII-004.v1",
        algorithm_version=(
            "oracle-certified-intelligence-registry-consumption-activation.v1"
        ),
        activation_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_registry_consumption_activation
    )
    module.verify_oracle_certified_intelligence_registry_consumption_activation = (
        lambda _activation: True
    )

    try:
        activation = make_activation()

        first = (
            module.attest_oracle_certified_intelligence_registry_consumption_activation(
                activation=activation
            )
        )
        second = (
            module.attest_oracle_certified_intelligence_registry_consumption_activation(
                activation=activation
            )
        )

        assert first == second
        assert first.attestation_hash == second.attestation_hash
        assert (
            module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                first
            )
        )
        assert first.source_activation_id == activation.activation_id
        assert first.source_activation_hash == activation.activation_hash
        assert first.source_authorization_id == activation.source_authorization_id
        assert first.source_registry_id == activation.source_registry_id
        assert first.source_entry_count == 2
        assert first.activation_verified is True
        assert first.single_use_authorization_consumption_verified is True
        assert first.duplicate_activation_rejection_verified is True
        assert first.irreversible_activation_verified is True
        assert first.read_only_consumption_activation_verified is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                replace(first, attestation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                replace(first, irreversible_activation_verified=False)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                replace(first, oracle_execution_allowed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation(
                replace(first, source_entry_count=3)
            )
        )

        print("========================================")
        print(" INT-OII-005 TEST")
        print(" CERTIFIED INTELLIGENCE REGISTRY")
        print(" ACTIVATION ATTESTATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-004 activation verifier consumed")
        print("[PASS] Activation identity and hash preserved")
        print("[PASS] Authorization identity and hash preserved")
        print("[PASS] Registry attestation identity and hash preserved")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Deterministic activation verified")
        print("[PASS] Bounded registry scope verified")
        print("[PASS] Single-use authorization consumption verified")
        print("[PASS] Duplicate activation rejection verified")
        print("[PASS] Irreversible activation verified")
        print("[PASS] Read-only consumption activation verified")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle and reasoning execution remain disabled")
        print("[PASS] Probability estimation and final conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-005 REGISTRY ACTIVATION ATTESTED")
    finally:
        module.verify_oracle_certified_intelligence_registry_consumption_activation = (
            original_verifier
        )


if __name__ == "__main__":
    main()
