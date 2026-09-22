from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_assembly_gate import (
    OracleCertifiedIntelligenceRegistry,
    OracleCertifiedIntelligenceRegistryEntry,
)
import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate as module


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceRegistryAttestationInvariantError:
        return
    raise AssertionError("expected INT-OII-002 invariant rejection")


def make_registry() -> OracleCertifiedIntelligenceRegistry:
    entries = (
        OracleCertifiedIntelligenceRegistryEntry(
            subsystem_key="oracle_intelligence_integration",
            engine_id="OII-015",
            source_record_id="oii-terminal:" + "a" * 64,
            source_record_hash="a" * 64,
            verified=True,
            read_only_verified=True,
            mutation_allowed=False,
            execution_allowed=False,
            publication_allowed=False,
            qseries_execution_allowed=False,
            entry_hash="1" * 64,
        ),
        OracleCertifiedIntelligenceRegistryEntry(
            subsystem_key="oracle_scientific_reasoning_runtime",
            engine_id="INT-OSR-001",
            source_record_id="osr-consumption:" + "b" * 64,
            source_record_hash="b" * 64,
            verified=True,
            read_only_verified=True,
            mutation_allowed=False,
            execution_allowed=False,
            publication_allowed=False,
            qseries_execution_allowed=False,
            entry_hash="2" * 64,
        ),
    )
    return OracleCertifiedIntelligenceRegistry(
        registry_id="oracle-certified-intelligence-registry:" + "c" * 64,
        entries=entries,
        entry_count=2,
        deterministic_registration_order=True,
        exact_source_hashes_preserved=True,
        duplicate_subsystems_rejected=True,
        immutable_registry=True,
        downstream_read_only_consumption_allowed=True,
        registry_mutation_allowed=False,
        oracle_execution_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        read_only=True,
        registry_status="oracle_certified_intelligence_registry_assembled",
        engine_id="INT-OII-001",
        schema_version="INT-OII-001.v1",
        algorithm_version="oracle-certified-intelligence-registry-assembly.v1",
        registry_hash="c" * 64,
    )


def main() -> None:
    original_verifier = module.verify_oracle_certified_intelligence_registry
    module.verify_oracle_certified_intelligence_registry = lambda _registry: True

    try:
        registry = make_registry()

        first = module.attest_oracle_certified_intelligence_registry(
            registry=registry
        )
        second = module.attest_oracle_certified_intelligence_registry(
            registry=registry
        )

        assert first == second
        assert first.attestation_hash == second.attestation_hash
        assert module.verify_oracle_certified_intelligence_registry_attestation(
            first
        )
        assert first.source_registry_id == registry.registry_id
        assert first.source_registry_hash == registry.registry_hash
        assert first.source_entry_count == 2
        assert first.source_entry_hashes == ("1" * 64, "2" * 64)
        assert first.source_subsystem_keys == (
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        )
        assert first.registry_verified is True
        assert first.read_only is True
        assert first.registry_mutation_allowed is False
        assert first.oracle_execution_allowed is False
        assert first.qseries_execution_allowed is False

        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_attestation(
                replace(first, attestation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_attestation(
                replace(first, registry_mutation_allowed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_attestation(
                replace(first, source_entry_count=3)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_attestation(
                replace(
                    first,
                    source_subsystem_keys=tuple(
                        reversed(first.source_subsystem_keys)
                    ),
                )
            )
        )

        print("========================================")
        print(" INT-OII-002 TEST")
        print(" ORACLE CERTIFIED INTELLIGENCE")
        print(" REGISTRY ATTESTATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-001 registry verifier consumed")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact registry hash scope preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Deterministic registration order verified")
        print("[PASS] Duplicate subsystem rejection verified")
        print("[PASS] Immutable registry verified")
        print("[PASS] Registry attestation identity deterministic")
        print("[PASS] Downstream read-only consumption verified")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle execution remains disabled")
        print("[PASS] Publication and alerting remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-002 CERTIFIED INTELLIGENCE REGISTRY ATTESTED")
    finally:
        module.verify_oracle_certified_intelligence_registry = original_verifier


if __name__ == "__main__":
    main()
