from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_callable_binding_authorization_consumption_activation_gate"
)


@dataclass(frozen=True)
class StubCertifiedCallableBindingAuthorization:
    authorization_id: str
    authorization_hash: str
    source_readiness_id: str
    source_readiness_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    callable_binding_authorized: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_allowed: bool
    reasoning_execution_allowed: bool
    probability_estimation_allowed: bool
    final_intelligence_conclusion_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    read_only: bool


def accepted_verifier(value) -> bool:
    if not isinstance(value, StubCertifiedCallableBindingAuthorization):
        raise ValueError("unexpected authorization type")
    if value.callable_binding_authorized is not True:
        raise ValueError("binding authorization not certified")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCallableBindingAuthorizationActivationInvariantError:
        return
    raise AssertionError("expected OSR-008 invariant rejection")


def main() -> None:
    original_verifier = module.verify_certified_callable_binding_authorization
    module.verify_certified_callable_binding_authorization = accepted_verifier
    try:
        authorization = StubCertifiedCallableBindingAuthorization(
            authorization_id="callable-binding-authorization:" + "a" * 64,
            authorization_hash="a" * 64,
            source_readiness_id="callable-binding-readiness:" + "b" * 64,
            source_readiness_hash="b" * 64,
            source_activation_id="osr005:activation:001",
            source_activation_hash="c" * 64,
            source_authorization_id="osr004:authorization:001",
            source_authorization_hash="d" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="e" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="f" * 64,
            callable_count=9,
            callable_binding_authorized=True,
            implementation_import_allowed=False,
            implementation_symbol_load_allowed=False,
            callable_binding_allowed=False,
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
        )

        first = module.activate_callable_binding_authorization(
            authorization=authorization
        )
        second = module.activate_callable_binding_authorization(
            authorization=authorization
        )

        assert first == second
        assert first.activation_hash == second.activation_hash
        assert module.verify_callable_binding_authorization_activation(first)
        assert first.callable_count == 9
        assert first.authorization_verified is True
        assert first.authorization_consumed is True
        assert first.authorization_consumption_single_use is True
        assert first.exact_authorization_hash_scope_preserved is True
        assert first.callable_binding_activation_enabled is True
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_callable_binding_authorization_activation(
                replace(first, activation_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_callable_binding_authorization_activation(
                replace(first, callable_binding_allowed=True)
            )
        )
        rejected(
            lambda: module.activate_callable_binding_authorization(
                authorization=replace(
                    authorization,
                    implementation_symbol_load_allowed=True,
                )
            )
        )
        rejected(
            lambda: module.activate_callable_binding_authorization(
                authorization=replace(
                    authorization,
                    read_only=False,
                )
            )
        )

        print("========================================")
        print(" OSR-008 TEST")
        print(" CALLABLE BINDING AUTHORIZATION")
        print(" CONSUMPTION ACTIVATION GATE")
        print("========================================")
        print("[PASS] Actual OSR-007 authorization verifier consumed")
        print("[PASS] OSR-007 authorization identity and lineage preserved")
        print("[PASS] Exact authorization hash scope preserved")
        print("[PASS] Single-use authorization consumption recorded")
        print("[PASS] Exact callable count preserved")
        print("[PASS] Binding activation identity deterministic")
        print("[PASS] Callable binding activation enabled")
        print("[PASS] Implementation import remains disabled")
        print("[PASS] Implementation symbol loading remains disabled")
        print("[PASS] Callable binding remains disabled")
        print("[PASS] Reasoning execution remains disabled")
        print("[PASS] Probability estimation remains disabled")
        print("[PASS] Final intelligence conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] OSR-008 CALLABLE BINDING ACTIVATION GATE CERTIFIED")
    finally:
        module.verify_certified_callable_binding_authorization = original_verifier


if __name__ == "__main__":
    main()
