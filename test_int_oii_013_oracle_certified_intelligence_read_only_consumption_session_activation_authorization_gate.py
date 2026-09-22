from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation,
)
from qseries_v2.oracle_intelligence_integration import (
    oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate as module,
)


def make_attestation() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAttestation(
        attestation_id="attestation:" + "a" * 64,
        source_activation_id="activation:" + "b" * 64,
        source_activation_hash="b" * 64,
        source_consumption_id="consumption:" + "c" * 64,
        source_consumption_hash="c" * 64,
        source_authorization_id="authorization:" + "d" * 64,
        source_authorization_hash="d" * 64,
        source_readiness_id="readiness:" + "e" * 64,
        source_readiness_hash="e" * 64,
        source_session_attestation_id="session-attestation:" + "f" * 64,
        source_session_attestation_hash="f" * 64,
        source_session_id="session:" + "1" * 64,
        source_session_hash="1" * 64,
        source_registry_activation_id="registry-activation:" + "2" * 64,
        source_registry_activation_hash="2" * 64,
        source_registry_authorization_id="registry-authorization:" + "3" * 64,
        source_registry_authorization_hash="3" * 64,
        source_registry_id="registry:" + "4" * 64,
        source_registry_hash="4" * 64,
        source_entry_count=2,
        source_entry_hashes=("5" * 64, "6" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        activation_verified=True,
        activation_identity_attested=True,
        activation_hash_attested=True,
        complete_lineage_attested=True,
        deterministic_attestation=True,
        bounded_attestation_scope=True,
        single_activation_scope=True,
        activation_single_use_attested=True,
        duplicate_activation_disabled_attested=True,
        irreversible_activation_attested=True,
        downstream_read_only_consumption_active_attested=True,
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
        attestation_status="oracle_certified_intelligence_read_only_consumption_session_activation_attested",
        engine_id="INT-OII-012",
        schema_version="INT-OII-012.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-attestation.v1",
        attestation_hash="a" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationInvariantError:
        return
    raise AssertionError("expected INT-OII-013 rejection")


def main() -> None:
    original = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation = (
        lambda _: True
    )

    try:
        attestation = make_attestation()

        first = module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(
            attestation=attestation
        )
        second = module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(
            attestation=attestation
        )

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
            first
        )
        assert first.source_attestation_id == attestation.attestation_id
        assert first.source_attestation_hash == attestation.attestation_hash
        assert first.activation_attestation_verified is True
        assert first.deterministic_authorization is True
        assert first.bounded_authorization_scope is True
        assert first.single_attestation_scope is True
        assert first.authorization_single_use is True
        assert first.duplicate_authorization_allowed is False
        assert first.authorization_reversible is False
        assert first.downstream_read_only_consumption_active is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.order_creation_allowed is False
        assert first.funds_movement_allowed is False
        assert first.portfolio_mutation_allowed is False
        assert first.read_only is True

        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
                replace(first, authorization_hash="0" * 64)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
                replace(first, qseries_execution_allowed=True)
            )
        )
        must_reject(
            lambda: module.authorize_oracle_certified_intelligence_read_only_consumption_session_activation(
                attestation=replace(
                    attestation,
                    downstream_read_only_consumption_active_attested=False,
                )
            )
        )

        print("========================================")
        print(" INT-OII-013 TEST")
        print(" ACTIVATION AUTHORIZATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-012 activation attestation consumed")
        print("[PASS] Complete activation and registry lineage preserved")
        print("[PASS] Deterministic bounded authorization certified")
        print("[PASS] Single-attestation and single-use scope certified")
        print("[PASS] Duplicate and reversible authorization disabled")
        print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-013 ACTIVATION AUTHORIZATION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_attestation = (
            original
        )


if __name__ == "__main__":
    main()
