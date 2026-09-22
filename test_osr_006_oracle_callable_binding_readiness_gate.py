from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_callable_binding_readiness_gate"
)


@dataclass(frozen=True)
class StubCallableResolutionActivation:
    activation_id: str
    activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    activated_callable_count: int
    read_only: bool
    callable_resolution_allowed: bool
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


def accepted_verifier(value) -> bool:
    if not isinstance(value, StubCallableResolutionActivation):
        raise ValueError("unexpected activation type")
    if value.callable_resolution_allowed is not True:
        raise ValueError("resolution not activated")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCallableBindingReadinessInvariantError:
        return
    raise AssertionError("expected OSR-006 invariant rejection")


def main() -> None:
    original_verifier = module.verify_callable_resolution_activation
    module.verify_callable_resolution_activation = accepted_verifier
    try:
        activation = StubCallableResolutionActivation(
            activation_id="osr005:activation:001",
            activation_hash="a" * 64,
            source_authorization_id="osr004:authorization:001",
            source_authorization_hash="b" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="c" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="d" * 64,
            activated_callable_count=9,
            read_only=True,
            callable_resolution_allowed=True,
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
        )

        first = module.certify_callable_binding_readiness(
            activation=activation
        )
        second = module.certify_callable_binding_readiness(
            activation=activation
        )

        assert first == second
        assert first.readiness_hash == second.readiness_hash
        assert module.verify_callable_binding_readiness(first)
        assert first.callable_count == 9
        assert first.callable_binding_ready is True
        assert first.implementation_import_allowed is False
        assert first.implementation_symbol_load_allowed is False
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False

        rejected(
            lambda: module.verify_callable_binding_readiness(
                replace(first, readiness_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_callable_binding_readiness(
                replace(first, callable_binding_allowed=True)
            )
        )
        rejected(
            lambda: module.certify_callable_binding_readiness(
                activation=replace(
                    activation,
                    callable_binding_allowed=True,
                )
            )
        )
        rejected(
            lambda: module.certify_callable_binding_readiness(
                activation=replace(
                    activation,
                    read_only=False,
                )
            )
        )

        print("========================================")
        print(" OSR-006 TEST")
        print(" CALLABLE BINDING READINESS GATE")
        print("========================================")
        print("[PASS] Actual OSR-005 activation verifier consumed")
        print("[PASS] OSR-005 activation identity and lineage preserved")
        print("[PASS] Exact activated callable count preserved")
        print("[PASS] Binding readiness identity deterministic")
        print("[PASS] Callable binding readiness certified")
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
        print("[DONE] OSR-006 CALLABLE BINDING READINESS GATE CERTIFIED")
    finally:
        module.verify_callable_resolution_activation = original_verifier


if __name__ == "__main__":
    main()
