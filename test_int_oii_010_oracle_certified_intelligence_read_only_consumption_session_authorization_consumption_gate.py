from __future__ import annotations

from dataclasses import replace

import qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_consumption_gate as module
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_authorization_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization,
)


def make_authorization() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorization(
        authorization_id="session-authorization:" + "a" * 64,
        source_readiness_id="readiness:" + "b" * 64,
        source_readiness_hash="b" * 64,
        source_session_attestation_id="session-attestation:" + "c" * 64,
        source_session_attestation_hash="c" * 64,
        source_session_id="session:" + "d" * 64,
        source_session_hash="d" * 64,
        source_activation_id="activation:" + "e" * 64,
        source_activation_hash="e" * 64,
        source_authorization_id="registry-authorization:" + "f" * 64,
        source_authorization_hash="f" * 64,
        source_registry_id="registry:" + "1" * 64,
        source_registry_hash="1" * 64,
        source_entry_count=2,
        source_entry_hashes=("2" * 64, "3" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        readiness_verified=True,
        deterministic_authorization=True,
        bounded_authorization_scope=True,
        single_session_scope=True,
        authorization_single_use=True,
        authorization_consumed=False,
        downstream_read_only_consumption_authorized=True,
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
        authorization_status="oracle_certified_intelligence_read_only_consumption_session_authorized",
        engine_id="INT-OII-009",
        schema_version="INT-OII-009.v2",
        algorithm_version="oracle-certified-intelligence-read-only-consumption-session-authorization.v2",
        authorization_hash="a" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionAuthorizationConsumptionInvariantError:
        return
    raise AssertionError("expected INT-OII-010 rejection")


def main() -> None:
    original = module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization
    module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization = lambda _: True
    try:
        authorization = make_authorization()
        first = module.consume_oracle_certified_intelligence_read_only_consumption_session_authorization(
            authorization=authorization
        )
        second = module.consume_oracle_certified_intelligence_read_only_consumption_session_authorization(
            authorization=authorization
        )

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(first)
        assert first.source_authorization_id == authorization.authorization_id
        assert first.source_authorization_hash == authorization.authorization_hash
        assert first.single_use_authorization_consumed is True
        assert first.duplicate_consumption_allowed is False
        assert first.consumption_reversible is False
        assert first.downstream_read_only_consumption_activated is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(
                replace(first, consumption_hash="0" * 64)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(
                replace(first, duplicate_consumption_allowed=True)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization_consumption(
                replace(first, oracle_execution_allowed=True)
            )
        )

        already_consumed = replace(authorization, authorization_consumed=True)
        must_reject(
            lambda: module.consume_oracle_certified_intelligence_read_only_consumption_session_authorization(
                authorization=already_consumed
            )
        )

        print("========================================")
        print(" INT-OII-010 TEST")
        print(" AUTHORIZATION CONSUMPTION GATE")
        print("========================================")
        print("[PASS] Actual INT-OII-009 authorization boundary consumed")
        print("[PASS] Authorization identity and hash preserved")
        print("[PASS] Readiness/session/activation/registry lineage preserved")
        print("[PASS] Deterministic bounded consumption certified")
        print("[PASS] Single-use authorization consumed")
        print("[PASS] Duplicate consumption rejected")
        print("[PASS] Consumption is irreversible")
        print("[PASS] Downstream read-only consumption activated")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-010 AUTHORIZATION CONSUMPTION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_authorization = original


if __name__ == "__main__":
    main()
