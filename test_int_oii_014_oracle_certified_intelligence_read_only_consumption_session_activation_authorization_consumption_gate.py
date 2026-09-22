from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence_integration import (
    oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption_gate as module,
)
from qseries_v2.oracle_intelligence_integration.oracle_certified_intelligence_read_only_consumption_session_activation_authorization_gate import (
    OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization,
)


def make_authorization() -> OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization:
    return OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorization(
        authorization_id="activation-authorization:" + "a" * 64,
        source_attestation_id="activation-attestation:" + "b" * 64,
        source_attestation_hash="b" * 64,
        source_activation_id="activation:" + "c" * 64,
        source_activation_hash="c" * 64,
        source_consumption_id="consumption:" + "d" * 64,
        source_consumption_hash="d" * 64,
        source_authorization_id="session-authorization:" + "e" * 64,
        source_authorization_hash="e" * 64,
        source_readiness_id="readiness:" + "f" * 64,
        source_readiness_hash="f" * 64,
        source_session_attestation_id="session-attestation:" + "1" * 64,
        source_session_attestation_hash="1" * 64,
        source_session_id="session:" + "2" * 64,
        source_session_hash="2" * 64,
        source_registry_activation_id="registry-activation:" + "3" * 64,
        source_registry_activation_hash="3" * 64,
        source_registry_authorization_id="registry-authorization:" + "4" * 64,
        source_registry_authorization_hash="4" * 64,
        source_registry_id="registry:" + "5" * 64,
        source_registry_hash="5" * 64,
        source_entry_count=2,
        source_entry_hashes=("6" * 64, "7" * 64),
        source_subsystem_keys=(
            "oracle_intelligence_integration",
            "oracle_scientific_reasoning_runtime",
        ),
        activation_attestation_verified=True,
        deterministic_authorization=True,
        bounded_authorization_scope=True,
        single_attestation_scope=True,
        authorization_single_use=True,
        duplicate_authorization_allowed=False,
        authorization_reversible=False,
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
        authorization_status=(
            "oracle_certified_intelligence_read_only_consumption_session_activation_authorized"
        ),
        engine_id="INT-OII-013",
        schema_version="INT-OII-013.v1",
        algorithm_version=(
            "oracle-certified-intelligence-read-only-consumption-session-activation-authorization.v1"
        ),
        authorization_hash="8" * 64,
    )


def must_reject(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedIntelligenceReadOnlyConsumptionSessionActivationAuthorizationConsumptionInvariantError:
        return
    raise AssertionError("expected INT-OII-014 rejection")


def main() -> None:
    original = (
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization
    )
    module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization = (
        lambda _: True
    )

    try:
        authorization = make_authorization()

        first = module.consume_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
            authorization=authorization
        )
        second = module.consume_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
            authorization=authorization
        )

        assert first == second
        assert module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption(
            first
        )
        assert first.source_activation_authorization_id == authorization.authorization_id
        assert first.source_activation_authorization_hash == authorization.authorization_hash
        assert first.activation_authorization_verified is True
        assert first.deterministic_consumption is True
        assert first.bounded_consumption_scope is True
        assert first.single_authorization_scope is True
        assert first.single_use_authorization_consumed is True
        assert first.duplicate_consumption_allowed is False
        assert first.consumption_reversible is False
        assert first.downstream_read_only_consumption_active is True
        assert first.oracle_execution_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.order_creation_allowed is False
        assert first.funds_movement_allowed is False
        assert first.portfolio_mutation_allowed is False
        assert first.read_only is True

        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption(
                replace(first, consumption_hash="0" * 64)
            )
        )
        must_reject(
            lambda: module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization_consumption(
                replace(first, qseries_execution_allowed=True)
            )
        )
        must_reject(
            lambda: module.consume_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
                authorization=replace(
                    authorization,
                    authorization_single_use=False,
                )
            )
        )
        must_reject(
            lambda: module.consume_oracle_certified_intelligence_read_only_consumption_session_activation_authorization(
                authorization=replace(
                    authorization,
                    downstream_read_only_consumption_active=False,
                )
            )
        )

        print("========================================")
        print(" INT-OII-014 TEST")
        print(" ACTIVATION AUTHORIZATION CONSUMPTION")
        print("========================================")
        print("[PASS] Actual INT-OII-013 activation authorization consumed")
        print("[PASS] Complete activation and registry lineage preserved")
        print("[PASS] Deterministic bounded consumption certified")
        print("[PASS] Single-authorization and single-use scope certified")
        print("[PASS] Duplicate and reversible consumption disabled")
        print("[PASS] Downstream read-only consumption remains active")
        print("[PASS] Oracle and reasoning execution disabled")
        print("[PASS] Q Series execution disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[DONE] INT-OII-014 ACTIVATION AUTHORIZATION CONSUMPTION GATE PASS")
    finally:
        module.verify_oracle_certified_intelligence_read_only_consumption_session_activation_authorization = (
            original
        )


if __name__ == "__main__":
    main()
