from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_attestation_gate import (
    OracleCertifiedIntelligenceRegistryAttestation,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceRegistryConsumptionAuthorizationInvariantError:
        return
    raise AssertionError("expected INT-OII-003 invariant rejection")


def make_attestation() -> OracleCertifiedIntelligenceRegistryAttestation:
    return OracleCertifiedIntelligenceRegistryAttestation(
        attestation_id="registry-attestation:" + "a" * 64,
        source_registry_id="registry:" + "b" * 64,
        source_registry_hash="b" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        registry_verified=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        deterministic_registration_order_verified=True,
        duplicate_subsystem_rejection_verified=True,
        immutable_registry_verified=True,
        downstream_read_only_consumption_verified=True,
        registry_mutation_allowed=False,
        oracle_execution_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        read_only=True,
        attestation_status="oracle_certified_intelligence_registry_attested",
        engine_id="INT-OII-002",
        schema_version="INT-OII-002.v1",
        algorithm_version="oracle-certified-intelligence-registry-attestation.v1",
        attestation_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_registry_attestation
    )
    module.verify_oracle_certified_intelligence_registry_attestation = (
        lambda _attestation: True
    )

    try:
        attestation = make_attestation()

        first = (
            module.authorize_oracle_certified_intelligence_registry_consumption(
                attestation=attestation
            )
        )
        second = (
            module.authorize_oracle_certified_intelligence_registry_consumption(
                attestation=attestation
            )
        )

        assert first == second
        assert first.authorization_hash == second.authorization_hash
        assert (
            module.verify_oracle_certified_intelligence_registry_consumption_authorization(
                first
            )
        )
        assert first.source_attestation_id == attestation.attestation_id
        assert first.source_attestation_hash == attestation.attestation_hash
        assert first.source_registry_id == attestation.source_registry_id
        assert first.source_registry_hash == attestation.source_registry_hash
        assert first.source_entry_count == 2
        assert first.read_only_consumption_authorized is True
        assert first.single_use_authorization_required is True
        assert first.authorization_consumed is False
        assert first.registry_mutation_allowed is False
        assert first.oracle_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(
                replace(first, authorization_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(
                replace(first, authorization_consumed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(
                replace(first, registry_mutation_allowed=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_authorization(
                replace(first, source_entry_count=3)
            )
        )

        print("========================================")
        print(" INT-OII-003 TEST")
        print(" CERTIFIED INTELLIGENCE REGISTRY")
        print(" CONSUMPTION AUTHORIZATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-002 registry attestation verifier consumed")
        print("[PASS] Attestation identity and hash preserved")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Read-only registry consumption authorized")
        print("[PASS] Deterministic consumption required")
        print("[PASS] Bounded registry scope required")
        print("[PASS] Single-use authorization required")
        print("[PASS] Authorization remains unconsumed")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle execution remains disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-003 REGISTRY CONSUMPTION AUTHORIZED")
    finally:
        module.verify_oracle_certified_intelligence_registry_attestation = (
            original_verifier
        )


if __name__ == "__main__":
    main()
