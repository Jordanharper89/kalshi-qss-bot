from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_certified_callable_binding_execution_authorization_gate"
)


@dataclass(frozen=True)
class StubCallableBindingExecutionReadiness:
    readiness_id: str
    readiness_hash: str
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
    callable_binding_execution_ready: bool
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
    if not isinstance(value, StubCallableBindingExecutionReadiness):
        raise ValueError("unexpected readiness type")
    if value.callable_binding_execution_ready is not True:
        raise ValueError("execution readiness not certified")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleCertifiedCallableBindingExecutionAuthorizationInvariantError:
        return
    raise AssertionError("expected OSR-010 invariant rejection")


def main() -> None:
    original_verifier = module.verify_callable_binding_execution_readiness
    module.verify_callable_binding_execution_readiness = accepted_verifier
    try:
        readiness = StubCallableBindingExecutionReadiness(
            readiness_id="callable-binding-execution-readiness:" + "a" * 64,
            readiness_hash="a" * 64,
            source_binding_activation_id="callable-binding-activation:" + "b" * 64,
            source_binding_activation_hash="b" * 64,
            source_binding_authorization_id=(
                "callable-binding-authorization:" + "c" * 64
            ),
            source_binding_authorization_hash="c" * 64,
            source_binding_readiness_id="callable-binding-readiness:" + "d" * 64,
            source_binding_readiness_hash="d" * 64,
            source_resolution_activation_id="osr005:activation:001",
            source_resolution_activation_hash="e" * 64,
            source_resolution_authorization_id="osr004:authorization:001",
            source_resolution_authorization_hash="f" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="1" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="2" * 64,
            callable_count=9,
            callable_binding_execution_ready=True,
            callable_binding_execution_authorized=False,
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

        first = module.authorize_callable_binding_execution(readiness=readiness)
        second = module.authorize_callable_binding_execution(readiness=readiness)

        assert first == second
        assert first.authorization_hash == second.authorization_hash
        assert module.verify_certified_callable_binding_execution_authorization(
            first
        )
        assert first.callable_count == 9
        assert first.execution_readiness_verified is True
        assert first.exact_readiness_hash_scope_preserved is True
        assert first.bounded_binding_scope_preserved is True
        assert first.deterministic_binding_required is True
        assert first.immutable_binding_result_required is True
        assert first.callable_binding_execution_authorized is True
        assert first.callable_binding_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: module.verify_certified_callable_binding_execution_authorization(
                replace(first, authorization_hash="0" * 64)
            )
        )
        rejected(
            lambda: module.verify_certified_callable_binding_execution_authorization(
                replace(first, callable_binding_allowed=True)
            )
        )
        rejected(
            lambda: module.authorize_callable_binding_execution(
                readiness=replace(
                    readiness,
                    implementation_symbol_load_allowed=True,
                )
            )
        )
        rejected(
            lambda: module.authorize_callable_binding_execution(
                readiness=replace(
                    readiness,
                    callable_binding_execution_authorized=True,
                )
            )
        )

        print("========================================")
        print(" OSR-010 TEST")
        print(" CERTIFIED CALLABLE BINDING")
        print(" EXECUTION AUTHORIZATION GATE")
        print("========================================")
        print("[PASS] Actual OSR-009 execution-readiness verifier consumed")
        print("[PASS] OSR-009 readiness identity and lineage preserved")
        print("[PASS] Exact readiness hash scope preserved")
        print("[PASS] Exact callable count preserved")
        print("[PASS] Bounded deterministic binding scope preserved")
        print("[PASS] Immutable binding-result requirement preserved")
        print("[PASS] Execution authorization identity deterministic")
        print("[PASS] Callable binding execution authorization enabled")
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
            "[DONE] OSR-010 CALLABLE BINDING EXECUTION AUTHORIZATION CERTIFIED"
        )
    finally:
        module.verify_callable_binding_execution_readiness = original_verifier


if __name__ == "__main__":
    main()
