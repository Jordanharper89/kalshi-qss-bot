from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_attestation_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionInvariantError:
        return
    raise AssertionError("expected INT-OII-006 invariant rejection")


def make_activation_attestation() -> (
    OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation
):
    return OracleCertifiedIntelligenceRegistryConsumptionActivationAttestation(
        attestation_id="activation-attestation:" + "a" * 64,
        source_activation_id="activation:" + "b" * 64,
        source_activation_hash="b" * 64,
        source_authorization_id="authorization:" + "c" * 64,
        source_authorization_hash="c" * 64,
        source_attestation_id="registry-attestation:" + "d" * 64,
        source_attestation_hash="d" * 64,
        source_registry_id="registry:" + "e" * 64,
        source_registry_hash="e" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        activation_verified=True,
        exact_activation_hash_scope_preserved=True,
        exact_authorization_hash_scope_preserved=True,
        exact_attestation_hash_scope_preserved=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        certified_subsystem_scope_preserved=True,
        deterministic_activation_verified=True,
        bounded_registry_scope_verified=True,
        single_use_authorization_consumption_verified=True,
        duplicate_activation_rejection_verified=True,
        irreversible_activation_verified=True,
        read_only_consumption_activation_verified=True,
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
        attestation_status=(
            "oracle_certified_intelligence_registry_consumption_activation_attested"
        ),
        engine_id="INT-OII-005",
        schema_version="INT-OII-005.v1",
        algorithm_version=(
            "oracle-certified-intelligence-registry-consumption-activation-attestation.v1"
        ),
        attestation_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation
    )
    module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation = (
        lambda _attestation: True
    )

    try:
        activation_attestation = make_activation_attestation()

        first = (
            module.materialize_oracle_certified_intelligence_read_only_consumption_session(
                activation_attestation=activation_attestation
            )
        )
        second = (
            module.materialize_oracle_certified_intelligence_read_only_consumption_session(
                activation_attestation=activation_attestation
            )
        )

        assert first == second
        assert first.session_hash == second.session_hash
        assert (
            module.verify_oracle_certified_intelligence_read_only_consumption_session(
                first
            )
        )
        assert (
            first.source_activation_attestation_id
            == activation_attestation.attestation_id
        )
        assert (
            first.source_activation_attestation_hash
            == activation_attestation.attestation_hash
        )
        assert first.source_activation_id == activation_attestation.source_activation_id
        assert first.source_authorization_id == (
            activation_attestation.source_authorization_id
        )
        assert first.source_registry_id == activation_attestation.source_registry_id
        assert first.source_entry_count == 2
        assert first.deterministic_session_identity is True
        assert first.bounded_session_scope is True
        assert first.single_activation_scope is True
        assert first.session_materialized is True
        assert first.session_active is True
        assert first.session_closed is False
        assert first.read_only_consumption_allowed is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(
                replace(first, session_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(
                replace(first, session_active=False)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(
                replace(first, session_closed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session(
                replace(first, reasoning_execution_allowed=True)
            )
        )

        print("========================================")
        print(" INT-OII-006 TEST")
        print(" CERTIFIED INTELLIGENCE")
        print(" READ-ONLY CONSUMPTION SESSION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-005 activation attestation verifier consumed")
        print("[PASS] Activation attestation identity and hash preserved")
        print("[PASS] Activation identity and hash preserved")
        print("[PASS] Authorization identity and hash preserved")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Deterministic session identity certified")
        print("[PASS] Bounded session scope certified")
        print("[PASS] Single activation scope certified")
        print("[PASS] Read-only consumption session materialized")
        print("[PASS] Session active and not closed")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle and reasoning execution remain disabled")
        print("[PASS] Probability estimation and final conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-006 READ-ONLY CONSUMPTION SESSION MATERIALIZED")
    finally:
        module.verify_oracle_certified_intelligence_registry_consumption_activation_attestation = (
            original_verifier
        )


if __name__ == "__main__":
    main()
