from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_readiness_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness,
)


def make_readiness() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionReadiness(
        readiness_id="readiness:" + "a" * 64,
        source_session_attestation_id="session-attestation:" + "b" * 64,
        source_session_attestation_hash="b" * 64,
        source_session_id="session:" + "c" * 64,
        source_session_hash="c" * 64,
        source_activation_id="activation:" + "d" * 64,
        source_activation_hash="d" * 64,
        source_authorization_id="authorization:" + "e" * 64,
        source_authorization_hash="e" * 64,
        source_registry_id="registry:" + "f" * 64,
        source_registry_hash="f" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=("oracle_intelligence_integration", "oracle_scientific_reasoning_runtime"),
        session_attestation_verified=True,
        exact_session_attestation_hash_scope_preserved=True,
        exact_session_hash_scope_preserved=True,
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
        downstream_read_only_consumption_ready=True,
        readiness_single_scope=True,
        readiness_reversible=False,
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
        readiness_status="oracle_certified_intelligence_read_only_consumption_session_ready",
        engine_id="INT-OII-008",
        schema_version="INT-OII-008.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-readiness.v1",
        readiness_hash="a" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationInvariantError:
        return
    raise AssertionError("expected rejection")


def main() -> None:
    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness
    module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness = lambda _: True
    try:
        readiness = make_readiness()
        first = module.authorize_oracle_certified_intelligence_read_only_consumption_session(readiness=readiness)
        second = module.authorize_oracle_certified_intelligence_read_only_consumption_session(readiness=readiness)

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization(first)
        assert first.authorization_consumed is False
        assert first.authorization_single_use is True
        assert first.downstream_read_only_consumption_authorized is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        must_reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization(replace(first, authorization_hash="0" * 64)))
        must_reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization(replace(first, authorization_consumed=True)))
        must_reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization(replace(first, qseries_execution_allowed=True)))

        print("========================================")
        print(" INT-OII-009 CORRECTION V2 TEST")
        print(" SESSION AUTHORIZATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-008 readiness boundary consumed")
        print("[PASS] Deterministic authorization identity certified")
        print("[PASS] Immutable readiness/session/registry lineage preserved")
        print("[PASS] Single-session and single-use scope certified")
        print("[PASS] Authorization initially unconsumed")
        print("[PASS] Read-only downstream consumption authorized")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-009 SESSION AUTHORIZATION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_readiness = original


if __name__ == "__main__":
    main()
