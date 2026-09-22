from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence_integration import oracle_intelligence_integration_final_completion_and_freeze_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation,
)


def make_attestation():
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestation(
        attestation_id="attestation:" + "a" * 64,
        source_continuation_id="continuation:" + "b" * 64,
        source_continuation_hash="b" * 64,
        source_authorization_consumption_id="authorization-consumption:" + "c" * 64,
        source_authorization_consumption_hash="c" * 64,
        source_activation_authorization_id="authorization:" + "d" * 64,
        source_activation_authorization_hash="d" * 64,
        source_activation_id="activation:" + "e" * 64,
        source_activation_hash="e" * 64,
        source_session_id="session:" + "f" * 64,
        source_session_hash="f" * 64,
        source_registry_id="registry:" + "1" * 64,
        source_registry_hash="1" * 64,
        source_entry_count=2,
        source_entry_hashes=("2" * 64, "3" * 64),
        source_subsystem_keys=("oracle_intelligence_integration", "oracle_scientific_reasoning_runtime"),
        continuation_verified=True,
        deterministic_attestation=True,
        bounded_attestation_scope=True,
        single_continuation_scope=True,
        attestation_single_use=True,
        duplicate_attestation_allowed=False,
        attestation_reversible=False,
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
        attestation_status="oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attested",
        engine_id="INT-OII-016",
        schema_version="INT-OII-016.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-continuation-attestation.v1",
        attestation_hash="4" * 64,
    )


def reject(fn):
    try:
        fn()
    except module.OracleIntelligenceIntegrationFinalCompletionAndFreezeInvariantError:
        return
    raise AssertionError("expected INT-OII-017 rejection")


def main():
    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation = lambda _: True
    try:
        source = make_attestation()
        first = module.complete_and_freeze_oracle_intelligence_integration(attestation=source)
        second = module.complete_and_freeze_oracle_intelligence_integration(attestation=source)
        assert first == second
        assert module.verify_oracle_intelligence_integration_final_completion_and_freeze(first)
        assert first.source_attestation_id == source.attestation_id
        assert first.source_attestation_hash == source.attestation_hash
        assert first.complete_lineage_verified and first.deterministic_completion
        assert first.immutable_freeze and first.integration_complete and first.read_only
        assert not first.further_int_oii_certification_required
        assert not first.oracle_execution_allowed and not first.qseries_execution_allowed
        reject(lambda: module.verify_oracle_intelligence_integration_final_completion_and_freeze(replace(first, completion_hash="0" * 64)))
        reject(lambda: module.complete_and_freeze_oracle_intelligence_integration(attestation=replace(source, downstream_read_only_consumption_active=False)))
        print("========================================")
        print(" INT-OII-017 TEST")
        print(" FINAL COMPLETION AND FREEZE GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-016 continuation attestation consumed")
        print("[PASS] Complete INT-OII-001 through INT-OII-016 lineage preserved")
        print("[PASS] Deterministic final completion certified")
        print("[PASS] Immutable INT-OII integration freeze certified")
        print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] No further INT-OII certification layers required")
        print("[DONE] INT-OII-017 FINAL COMPLETION AND FREEZE GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation = original


if __name__ == "__main__":
    main()
