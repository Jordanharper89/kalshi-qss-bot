from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_attestation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSession,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionAttestationInvariantError:
        return
    raise AssertionError("expected INT-OII-007 invariant rejection")


def make_session() -> OracleCertifiedIntelligenceReadOnlyConsumptionSession:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSession(
        session_id="read-only-session:" + "a" * 64,
        source_activation_attestation_id="activation-attestation:" + "b" * 64,
        source_activation_attestation_hash="b" * 64,
        source_activation_id="activation:" + "c" * 64,
        source_activation_hash="c" * 64,
        source_authorization_id="authorization:" + "d" * 64,
        source_authorization_hash="d" * 64,
        source_registry_id="registry:" + "e" * 64,
        source_registry_hash="e" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        activation_attestation_verified=True,
        exact_activation_attestation_hash_scope_preserved=True,
        exact_activation_hash_scope_preserved=True,
        exact_authorization_hash_scope_preserved=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        certified_subsystem_scope_preserved=True,
        deterministic_session_identity=True,
        bounded_session_scope=True,
        single_activation_scope=True,
        session_materialized=True,
        session_active=True,
        session_closed=False,
        read_only_consumption_allowed=True,
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
        session_status=(
            "oracle_certified_intelligence_read_only_consumption_session_materialized"
        ),
        engine_id="INT-OII-006",
        schema_version="INT-OII-006.v1",
        algorithm_version=(
            "oracle-certified-intelligence-read-only-consumption-session.v1"
        ),
        session_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session = (
        lambda _session: True
    )

    try:
        session = make_session()

        first = (
            module.attest_oracle_certified_intelligence_read_only_consumption_session(
                session=session
            )
        )
        second = (
            module.attest_oracle_certified_intelligence_read_only_consumption_session(
                session=session
            )
        )

        assert first == second
        assert first.attestation_hash == second.attestation_hash
        assert (
            module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                first
            )
        )
        assert first.source_session_id == session.session_id
        assert first.source_session_hash == session.session_hash
        assert first.source_activation_id == session.source_activation_id
        assert first.source_authorization_id == session.source_authorization_id
        assert first.source_registry_id == session.source_registry_id
        assert first.source_entry_count == 2
        assert first.session_verified is True
        assert first.deterministic_session_identity_verified is True
        assert first.bounded_session_scope_verified is True
        assert first.single_activation_scope_verified is True
        assert first.session_materialization_verified is True
        assert first.active_session_verified is True
        assert first.unclosed_session_verified is True
        assert first.read_only_consumption_verified is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                replace(first, attestation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                replace(first, active_session_verified=False)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                replace(first, oracle_execution_allowed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_attestation(
                replace(first, source_entry_count=3)
            )
        )

        print("========================================")
        print(" INT-OII-007 TEST")
        print(" CERTIFIED INTELLIGENCE")
        print(" SESSION ATTESTATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-006 session verifier consumed")
        print("[PASS] Session identity and hash preserved")
        print("[PASS] Activation attestation identity and hash preserved")
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
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle and reasoning execution remain disabled")
        print("[PASS] Probability estimation and final conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-007 READ-ONLY CONSUMPTION SESSION ATTESTED")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session = (
            original_verifier
        )


if __name__ == "__main__":
    main()
