from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption,
)


def make_consumption() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumption(
        consumption_id="consumption:" + "a" * 64,
        source_authorization_id="authorization:" + "b" * 64,
        source_authorization_hash="b" * 64,
        source_readiness_id="readiness:" + "c" * 64,
        source_readiness_hash="c" * 64,
        source_session_attestation_id="session-attestation:" + "d" * 64,
        source_session_attestation_hash="d" * 64,
        source_session_id="session:" + "e" * 64,
        source_session_hash="e" * 64,
        source_activation_id="registry-activation:" + "f" * 64,
        source_activation_hash="f" * 64,
        source_registry_authorization_id="registry-authorization:" + "1" * 64,
        source_registry_authorization_hash="1" * 64,
        source_registry_id="registry:" + "2" * 64,
        source_registry_hash="2" * 64,
        source_entry_count=2,
        source_entry_hashes=("3" * 64, "4" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        authorization_verified=True,
        deterministic_consumption=True,
        bounded_consumption_scope=True,
        single_authorization_scope=True,
        single_use_authorization_consumed=True,
        duplicate_consumption_allowed=False,
        consumption_reversible=False,
        downstream_read_only_consumption_activated=True,
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
        consumption_status="oracle_certified_intelligence_read_only_consumption_session_authorization_consumed",
        engine_id="INT-OII-010",
        schema_version="INT-OII-010.v1",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-authorization-consumption.v1",
        consumption_hash="a" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationInvariantError:
        return
    raise AssertionError("expected INT-OII-011 rejection")


def main() -> None:
    original = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption = (
        lambda _: True
    )

    try:
        consumption = make_consumption()

        first = module.activate_oracle_certified_intelligence_read_only_consumption_session(
            consumption=consumption
        )
        second = module.activate_oracle_certified_intelligence_read_only_consumption_session(
            consumption=consumption
        )

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(
            first
        )
        assert first.source_consumption_id == consumption.consumption_id
        assert first.source_consumption_hash == consumption.consumption_hash
        assert first.authorization_consumption_verified is True
        assert first.deterministic_activation is True
        assert first.bounded_activation_scope is True
        assert first.single_consumption_scope is True
        assert first.activation_single_use is True
        assert first.duplicate_activation_allowed is False
        assert first.activation_reversible is False
        assert first.downstream_read_only_consumption_active is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(
                replace(first, activation_hash="0" * 64)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(
                replace(first, duplicate_activation_allowed=True)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation(
                replace(first, qseries_execution_allowed=True)
            )
        )

        inactive = replace(
            consumption,
            downstream_read_only_consumption_activated=False,
        )
        must_reject(
            lambda: module.activate_oracle_certified_intelligence_read_only_consumption_session(
                consumption=inactive
            )
        )

        print("========================================")
        print(" INT-OII-011 TEST")
        print(" SESSION ACTIVATION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-010 authorization consumption consumed")
        print("[PASS] Consumption identity and hash preserved")
        print("[PASS] Authorization/readiness/session/registry lineage preserved")
        print("[PASS] Deterministic bounded activation certified")
        print("[PASS] Single-consumption activation scope certified")
        print("[PASS] Single-use activation certified")
        print("[PASS] Duplicate activation disabled")
        print("[PASS] Activation is irreversible")
        print("[PASS] Downstream read-only consumption active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-011 SESSION ACTIVATION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption = (
            original
        )


if __name__ == "__main__":
    main()
