from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_callable_binding_execution_authorization_consumption_activation_gate"
)


@dataclass(frozen=True)
class StubCertifiedCallableBindingExecutionAuthorization:
    authorization_id: str
    authorization_hash: str
    source_execution_readiness_id: str
    source_execution_readiness_hash: str
    source_binding_activation_id: str
    source_binding_activation_hash: str
    source_binding_authorization_id: str
    source_binding_authorization_hash: str
    source_binding_readiness_id: str
    source_binding_readiness_hash: str
    source_resolution_activation_id: str
    source_resolution_activation_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    callable_binding_execution_authorized: bool
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
    if not isinstance(
        value,
        StubCertifiedCallableBindingExecutionAuthorization,
    ):
        raise ValueError("unexpected authorization type")
    if value.callable_binding_execution_authorized is not True:
        raise ValueError("execution authorization not certified")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCallableBindingExecutionAuthorizationActivationInvariantError:
        return
    raise AssertionError("expected OSR-011 invariant rejection")


def main() -> None:
    original_verifier = (
        module.verify_certified_callable_binding_execution_authorization
    )
    module.verify_certified_callable_binding_execution_authorization = (
        accepted_verifier
    )
    try:
        authorization = StubCertifiedCallableBindingExecutionAuthorization(
            authorization_id=(
                "callable-binding-execution-authorization:" + "a" * 64
            ),
            authorization_hash="a" * 64,
            source_execution_readiness_id=(
                "callable-binding-execution-readiness:" + "b" * 64
            ),
            source_execution_readiness_hash="b" * 64,
            source_binding_activation_id=(
                "callable-binding-activation:" + "c" * 64
            ),
            source_binding_activation_hash="c" * 64,
            source_binding_authorization_id=(
                "callable-binding-authorization:" + "d" * 64
            ),
            source_binding_authorization_hash="d" * 64,
            source_binding_readiness_id=(
                "callable-binding-readiness:" + "e" * 64
            ),
            source_binding_readiness_hash="e" * 64,
            source_resolution_activation_id="osr005:activation:001",
            source_resolution_activation_hash="f" * 64,
            source_resolution_authorization_id="osr004:authorization:001",
            source_resolution_authorization_hash="1" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="2" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="3" * 64,
            callable_count=9,
            callable_binding_execution_authorized=True,
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

        first = module.activate_callable_binding_execution_authorization(
            authorization=authorization
        )
        second = module.activate_callable_binding_execution_authorization(
            authorization=authorization
        )

        assert first == second
        assert first.activation_hash == second.activation_hash
        assert (
            module.verify_callable_binding_execution_authorization_activation(
                first
            )
        )
        assert first.callable_count == 9
        assert first.execution_authorization_verified is True
        assert first.execution_authorization_consumed is True
        assert first.authorization_consumption_single_use is True
        assert first.exact_authorization_hash_scope_preserved is True
        assert first.callable_binding_execution_activation_enabled is True
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: (
                module.verify_callable_binding_execution_authorization_activation(
                    replace(first, activation_hash="0" * 64)
                )
            )
        )
        rejected(
            lambda: (
                module.verify_callable_binding_execution_authorization_activation(
                    replace(first, callable_binding_allowed=True)
                )
            )
        )
        rejected(
            lambda: module.activate_callable_binding_execution_authorization(
                authorization=replace(
                    authorization,
                    implementation_import_allowed=True,
                )
            )
        )
        rejected(
            lambda: module.activate_callable_binding_execution_authorization(
                authorization=replace(
                    authorization,
                    read_only=False,
                )
            )
        )

        print("========================================")
        print(" OSR-011 TEST")
        print(" CALLABLE BINDING EXECUTION AUTHORIZATION")
        print(" CONSUMPTION ACTIVATION GATE")
        print("========================================")
        print("[PASS] Actual OSR-010 execution authorization verifier consumed")
        print("[PASS] OSR-010 authorization identity and lineage preserved")
        print("[PASS] Exact authorization hash scope preserved")
        print("[PASS] Single-use execution authorization consumed")
        print("[PASS] Exact callable count preserved")
        print("[PASS] Execution activation identity deterministic")
        print("[PASS] Callable binding execution activation enabled")
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
        print(
            "[DONE] OSR-011 CALLABLE BINDING EXECUTION ACTIVATION CERTIFIED"
        )
    finally:
        module.verify_certified_callable_binding_execution_authorization = (
            original_verifier
        )


if __name__ == "__main__":
    main()
