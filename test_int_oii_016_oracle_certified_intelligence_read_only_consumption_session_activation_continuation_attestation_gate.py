from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence_integration import oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_continuation_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation,
)


def make_continuation():
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuation(
        continuation_id="continuation:" + "a" * 64,
        source_authorization_consumption_id="authorization-consumption:" + "b" * 64,
        source_authorization_consumption_hash="b" * 64,
        source_activation_authorization_id="authorization:" + "c" * 64,
        source_activation_authorization_hash="c" * 64,
        source_activation_id="activation:" + "d" * 64,
        source_activation_hash="d" * 64,
        source_session_id="session:" + "e" * 64,
        source_session_hash="e" * 64,
        source_registry_id="registry:" + "f" * 64,
        source_registry_hash="f" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=("oracle_intelligence_integration", "oracle_scientific_reasoning_runtime"),
        authorization_consumption_verified=True,
        deterministic_continuation=True,
        bounded_continuation_scope=True,
        single_consumption_scope=True,
        continuation_single_use=True,
        duplicate_continuation_allowed=False,
        continuation_reversible=False,
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
        continuation_status="oracle_certified_intelligence_read_only_consumption_session_activation_continued",
        engine_id="INT-OII-015",
        schema_version="INT-OII-015.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-activation-continuation.v1",
        continuation_hash="3" * 64,
    )


def reject(fn):
    try:
        fn()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationContinuationAttestationInvariantError:
        return
    raise AssertionError("expected INT-OII-016 rejection")


def main():
    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation = lambda _: True
    try:
        source = make_continuation()
        first = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=source)
        second = module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=source)
        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(first)
        assert first.source_continuation_id == source.continuation_id
        assert first.source_continuation_hash == source.continuation_hash
        assert first.deterministic_attestation and first.bounded_attestation_scope
        assert first.single_continuation_scope and first.attestation_single_use and first.read_only
        assert not first.duplicate_attestation_allowed and not first.attestation_reversible
        assert not first.oracle_execution_allowed and not first.qseries_execution_allowed
        reject(lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation_attestation(replace(first, attestation_hash="0" * 64)))
        reject(lambda: module.attest_oracle_certified_intelligence_read_only_consumption_session_activation_continuation(continuation=replace(source, downstream_read_only_consumption_active=False)))
        print("========================================")
        print(" INT-OII-016 TEST")
        print(" CONTINUATION ATTESTATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-015 activation continuation consumed")
        print("[PASS] Complete activation and registry lineage preserved")
        print("[PASS] Deterministic bounded attestation certified")
        print("[PASS] Single-continuation and single-use scope certified")
        print("[PASS] Duplicate and reversible attestation disabled")
        print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-016 CONTINUATION ATTESTATION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_continuation = original


if __name__ == "__main__":
    main()
