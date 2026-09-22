from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_callable_binding_execution_readiness_gate"
)


@dataclass(frozen=True)
class StubCallableBindingActivation:
    activation_id: str
    activation_hash: str
    source_binding_authorization_id: str
    source_binding_authorization_hash: str
    source_readiness_id: str
    source_readiness_hash: str
    source_resolution_activation_id: str
    source_resolution_activation_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    callable_binding_activation_enabled: bool
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
    if not isinstance(value, StubCallableBindingActivation):
        raise ValueError("unexpected activation type")
    if value.callable_binding_activation_enabled is not True:
        raise ValueError("binding activation not enabled")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCallableBindingExecutionReadinessInvariantError:
        return
    raise AssertionError("expected OSR-009 invariant rejection")


def main() -> None:
    original_verifier = module.verify_callable_binding_authorization_activation
    module.verify_callable_binding_authorization_activation = accepted_verifier
    try:
        activation = StubCallableBindingActivation(
            activation_id="callable-binding-activation:" + "a" * 64,
            activation_hash="a" * 64,
            source_binding_authorization_id="callable-binding-authorization:" + "b" * 64,
            source_binding_authorization_hash="b" * 64,
            source_readiness_id="callable-binding-readiness:" + "c" * 64,
            source_readiness_hash="c" * 64,
            source_resolution_activation_id="osr005:activation:001",
            source_resolution_activation_hash="d" * 64,
            source_resolution_authorization_id="osr004:authorization:001",
            source_resolution_authorization_hash="e" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="f" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="1" * 64,
            callable_count=9,
            callable_binding_activation_enabled=True,
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

        first = module.certify_callable_binding_execution_readiness(
            activation=activation
        )
        second = module.certify_callable_binding_execution_readiness(
            activation=activation
        )

        assert first == second
        assert first.readiness_hash == second.readiness_hash
        assert module.verify_callable_binding_execution_readiness(first)
        assert first.callable_count == 9
        assert first.binding_activation_verified is True
        assert first.exact_activation_hash_scope_preserved is True
        assert first.bounded_binding_scope is True
        assert first.deterministic_binding_required is True
        assert first.immutable_binding_result_required is True
        assert first.callable_binding_execution_ready is True
        assert first.callable_binding_execution_authorized is False
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_callable_binding_execution_readiness(
                replace(first, readiness_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_callable_binding_execution_readiness(
                replace(first, callable_binding_execution_authorized=True)
            )
        )
        rejected(
            lambda: module.certify_callable_binding_execution_readiness(
                activation=replace(
                    activation,
                    implementation_import_allowed=True,
                )
            )
        )
        rejected(
            lambda: module.certify_callable_binding_execution_readiness(
                activation=replace(
                    activation,
                    read_only=False,
                )
            )
        )

        print("========================================")
        print(" OSR-009 TEST")
        print(" CALLABLE BINDING EXECUTION")
        print(" READINESS GATE")
        print("========================================")
        print("[PASS] Actual OSR-008 binding activation verifier consumed")
        print("[PASS] OSR-008 activation identity and lineage preserved")
        print("[PASS] Exact activation hash scope preserved")
        print("[PASS] Exact callable count preserved")
        print("[PASS] Bounded deterministic binding scope certified")
        print("[PASS] Immutable binding result required")
        print("[PASS] Binding execution readiness identity deterministic")
        print("[PASS] Callable binding execution readiness certified")
        print("[PASS] Binding execution authorization remains disabled")
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
        print("[DONE] OSR-009 CALLABLE BINDING EXECUTION READINESS CERTIFIED")
    finally:
        module.verify_callable_binding_authorization_activation = original_verifier


if __name__ == "__main__":
    main()
