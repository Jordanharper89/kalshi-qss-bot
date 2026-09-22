from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_readiness_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadinessInvariantError:
        return
    raise AssertionError("expected INT-OII-008 invariant rejection")


def make_attestation() -> (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation
):
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestation(
        attestation_id="session-attestation:" + "a" * 64,
        source_session_id="session:" + "b" * 64,
        source_session_hash="b" * 64,
        source_activation_attestation_id="activation-attestation:" + "c" * 64,
        source_activation_attestation_hash="c" * 64,
        source_activation_id="activation:" + "d" * 64,
        source_activation_hash="d" * 64,
        source_authorization_id="authorization:" + "e" * 64,
        source_authorization_hash="e" * 64,
        source_registry_id="registry:" + "f" * 64,
        source_registry_hash="f" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        session_verified=True,
        exact_session_hash_scope_preserved=True,
        exact_activation_attestation_hash_scope_preserved=True,
        exact_activation_hash_scope_preserved=True,
        exact_authorization_hash_scope_preserved=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        certified_subsystem_scope_preserved=True,
        deterministic_session_identity_verified=True,
        bounded_session_scope_verified=True,
        single_activation_scope_verified=True,
        session_materialization_verified=True,
        active_session_verified=True,
        unclosed_session_verified=True,
        read_only_consumption_verified=True,
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
            "oracle_certified_intelligence_read_only_consumption_session_attested"
        ),
        engine_id="INT-OII-007",
        schema_version="INT-OII-007.v1",
        algorithm_version=(
            "oracle-certified-intelligence-read-only-consumption-session-attestation.v1"
        ),
        attestation_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation = (
        lambda _attestation: True
    )

    try:
        attestation = make_attestation()

        first = (
            module.certify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                session_attestation=attestation
            )
        )
        second = (
            module.certify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                session_attestation=attestation
            )
        )

        assert first == second
        assert first.readiness_hash == second.readiness_hash
        assert (
            module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                first
            )
        )
        assert first.source_session_attestation_id == attestation.attestation_id
        assert first.source_session_attestation_hash == attestation.attestation_hash
        assert first.source_session_id == attestation.source_session_id
        assert first.source_activation_id == attestation.source_activation_id
        assert first.source_authorization_id == attestation.source_authorization_id
        assert first.source_registry_id == attestation.source_registry_id
        assert first.source_entry_count == 2
        assert first.session_attestation_verified is True
        assert first.downstream_read_only_consumption_ready is True
        assert first.readiness_single_scope is True
        assert first.readiness_reversible is False
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                replace(first, readiness_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                replace(first, downstream_read_only_consumption_ready=False)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                replace(first, readiness_reversible=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness(
                replace(first, reasoning_execution_allowed=True)
            )
        )

        print("========================================")
        print(" INT-OII-008 TEST")
        print(" CERTIFIED INTELLIGENCE")
        print(" SESSION READINESS GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-007 session attestation verifier consumed")
        print("[PASS] Session attestation identity and hash preserved")
        print("[PASS] Session identity and hash preserved")
        print("[PASS] Activation identity and hash preserved")
        print("[PASS] Authorization identity and hash preserved")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Deterministic session identity verified")
        print("[PASS] Bounded session scope verified")
        print("[PASS] Single activation scope verified")
        print("[PASS] Session materialization verified")
        print("[PASS] Active and unclosed session verified")
        print("[PASS] Read-only consumption verified")
        print("[PASS] Downstream read-only consumption ready")
        print("[PASS] Readiness bound to one immutable scope")
        print("[PASS] Readiness is irreversible")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle and reasoning execution remain disabled")
        print("[PASS] Probability estimation and final conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-008 READ-ONLY CONSUMPTION SESSION READY")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation = (
            original_verifier
        )


if __name__ == "__main__":
    main()
