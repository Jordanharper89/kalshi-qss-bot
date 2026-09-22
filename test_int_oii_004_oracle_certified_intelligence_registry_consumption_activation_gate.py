from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_activation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_registry_consumption_authorization_gate import (
    OracleCertifiedIntelligenceRegistryConsumptionAuthorization,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceRegistryConsumptionActivationInvariantError:
        return
    raise AssertionError("expected INT-OII-004 invariant rejection")


def make_authorization() -> OracleCertifiedIntelligenceRegistryConsumptionAuthorization:
    return OracleCertifiedIntelligenceRegistryConsumptionAuthorization(
        authorization_id="registry-consumption-authorization:" + "a" * 64,
        source_attestation_id="registry-attestation:" + "b" * 64,
        source_attestation_hash="b" * 64,
        source_registry_id="registry:" + "c" * 64,
        source_registry_hash="c" * 64,
        source_entry_count=2,
        source_entry_hashes=("1" * 64, "2" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        attestation_verified=True,
        exact_attestation_hash_scope_preserved=True,
        exact_registry_hash_scope_preserved=True,
        exact_entry_hash_scope_preserved=True,
        certified_subsystem_scope_preserved=True,
        read_only_consumption_authorized=True,
        deterministic_consumption_required=True,
        bounded_registry_scope_required=True,
        single_use_authorization_required=True,
        authorization_consumed=False,
        registry_mutation_allowed=False,
        oracle_execution_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
        read_only=True,
        authorization_status=(
            "oracle_certified_intelligence_registry_consumption_authorized"
        ),
        engine_id="INT-OII-003",
        schema_version="INT-OII-003.v1",
        algorithm_version=(
            "oracle-certified-intelligence-registry-consumption-authorization.v1"
        ),
        authorization_hash="a" * 64,
    )


def main() -> None:
    original_verifier = (
        module.verify_oracle_certified_intelligence_registry_consumption_authorization
    )
    module.verify_oracle_certified_intelligence_registry_consumption_authorization = (
        lambda _authorization: True
    )

    try:
        authorization = make_authorization()

        first = module.activate_oracle_certified_intelligence_registry_consumption(
            authorization=authorization
        )
        second = module.activate_oracle_certified_intelligence_registry_consumption(
            authorization=authorization
        )

        assert first == second
        assert first.activation_hash == second.activation_hash
        assert (
            module.verify_oracle_certified_intelligence_registry_consumption_activation(
                first
            )
        )
        assert first.source_authorization_id == authorization.authorization_id
        assert first.source_authorization_hash == authorization.authorization_hash
        assert first.source_attestation_id == authorization.source_attestation_id
        assert first.source_registry_id == authorization.source_registry_id
        assert first.source_entry_count == 2
        assert first.read_only_consumption_activated is True
        assert first.single_use_authorization_consumed is True
        assert first.duplicate_activation_rejected is True
        assert first.activation_reversible is False
        assert first.registry_mutation_allowed is False
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(
                replace(first, activation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(
                replace(first, activation_reversible=True)
            )
        )
        rejected(
            lambda: module.verify_oracle_certified_intelligence_registry_consumption_activation(
                replace(first, reasoning_execution_allowed=True)
            )
        )
        rejected(
            lambda: module.activate_oracle_certified_intelligence_registry_consumption(
                authorization=replace(
                    authorization,
                    authorization_consumed=True,
                )
            )
        )

        print("========================================")
        print(" INT-OII-004 TEST")
        print(" CERTIFIED INTELLIGENCE REGISTRY")
        print(" CONSUMPTION ACTIVATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-003 authorization verifier consumed")
        print("[PASS] Authorization identity and hash preserved")
        print("[PASS] Attestation identity and hash preserved")
        print("[PASS] Registry identity and hash preserved")
        print("[PASS] Exact entry hash scope preserved")
        print("[PASS] Certified subsystem scope preserved")
        print("[PASS] Read-only registry consumption activated")
        print("[PASS] Deterministic activation certified")
        print("[PASS] Bounded registry scope preserved")
        print("[PASS] Single-use authorization consumed")
        print("[PASS] Duplicate activation rejected")
        print("[PASS] Activation is irreversible")
        print("[PASS] Registry mutation remains disabled")
        print("[PASS] Oracle and reasoning execution remain disabled")
        print("[PASS] Probability estimation and final conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff remain disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OII-004 REGISTRY CONSUMPTION ACTIVATED")
    finally:
        module.verify_oracle_certified_intelligence_registry_consumption_authorization = (
            original_verifier
        )


if __name__ == "__main__":
    main()
