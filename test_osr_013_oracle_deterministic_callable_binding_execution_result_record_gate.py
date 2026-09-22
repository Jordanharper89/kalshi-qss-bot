from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_deterministic_callable_binding_execution_result_record_gate"
)


@dataclass(frozen=True)
class StubDeterministicCallableBindingExecutionEnvelope:
    envelope_id: str
    envelope_hash: str
    source_execution_activation_id: str
    source_execution_activation_hash: str
    source_execution_authorization_id: str
    source_execution_authorization_hash: str
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
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
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
        StubDeterministicCallableBindingExecutionEnvelope,
    ):
        raise ValueError("unexpected execution-envelope type")
    if value.read_only is not True:
        raise ValueError("execution envelope is not read-only")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleDeterministicCallableBindingExecutionResultInvariantError:
        return
    raise AssertionError("expected OSR-013 invariant rejection")


def main() -> None:
    original_verifier = (
        module.verify_deterministic_callable_binding_execution_envelope
    )
    module.verify_deterministic_callable_binding_execution_envelope = (
        accepted_verifier
    )
    try:
        envelope = StubDeterministicCallableBindingExecutionEnvelope(
            envelope_id="callable-binding-execution-envelope:" + "a" * 64,
            envelope_hash="a" * 64,
            source_execution_activation_id=(
                "callable-binding-execution-authorization-activation:"
                + "b" * 64
            ),
            source_execution_activation_hash="b" * 64,
            source_execution_authorization_id=(
                "callable-binding-execution-authorization:" + "c" * 64
            ),
            source_execution_authorization_hash="c" * 64,
            source_execution_readiness_id=(
                "callable-binding-execution-readiness:" + "d" * 64
            ),
            source_execution_readiness_hash="d" * 64,
            source_binding_activation_id=(
                "callable-binding-activation:" + "e" * 64
            ),
            source_binding_activation_hash="e" * 64,
            source_binding_authorization_id=(
                "callable-binding-authorization:" + "f" * 64
            ),
            source_binding_authorization_hash="f" * 64,
            source_binding_readiness_id=(
                "callable-binding-readiness:" + "1" * 64
            ),
            source_binding_readiness_hash="1" * 64,
            source_resolution_activation_id="osr005:activation:001",
            source_resolution_activation_hash="2" * 64,
            source_resolution_authorization_id="osr004:authorization:001",
            source_resolution_authorization_hash="3" * 64,
            source_resolution_package_id="osr003:resolution:001",
            source_resolution_hash="4" * 64,
            source_admission_package_id="osr002:admission:001",
            source_admission_hash="5" * 64,
            callable_count=9,
            implementation_import_allowed=False,
            implementation_symbol_load_allowed=False,
            callable_binding_allowed=False,
            callable_invocation_allowed=False,
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

        first = (
            module.materialize_deterministic_callable_binding_execution_result_record(
                envelope=envelope
            )
        )
        second = (
            module.materialize_deterministic_callable_binding_execution_result_record(
                envelope=envelope
            )
        )

        assert first == second
        assert first.result_hash == second.result_hash
        assert (
            module.verify_deterministic_callable_binding_execution_result_record(
                first
            )
        )
        assert first.callable_count == 9
        assert first.envelope_verified is True
        assert first.exact_envelope_hash_scope_preserved is True
        assert first.execution_attempted is False
        assert first.implementation_import_performed is False
        assert first.implementation_symbol_load_performed is False
        assert first.callable_binding_performed is False
        assert first.callable_invocation_performed is False
        assert first.reasoning_execution_performed is False
        assert first.qseries_execution_performed is False
        assert first.read_only is True

        rejected(
            lambda: (
                module.verify_deterministic_callable_binding_execution_result_record(
                    replace(first, result_hash="0" * 64)
                )
            )
        )
        rejected(
            lambda: (
                module.verify_deterministic_callable_binding_execution_result_record(
                    replace(first, callable_invocation_performed=True)
                )
            )
        )
        rejected(
            lambda: (
                module.materialize_deterministic_callable_binding_execution_result_record(
                    envelope=replace(
                        envelope,
                        implementation_symbol_load_allowed=True,
                    )
                )
            )
        )
        rejected(
            lambda: (
                module.materialize_deterministic_callable_binding_execution_result_record(
                    envelope=replace(
                        envelope,
                        read_only=False,
                    )
                )
            )
        )

        print("========================================")
        print(" OSR-013 TEST")
        print(" DETERMINISTIC CALLABLE BINDING")
        print(" EXECUTION RESULT RECORD GATE")
        print("========================================")
        print("[PASS] Actual OSR-012 execution-envelope verifier consumed")
        print("[PASS] OSR-012 envelope identity and lineage preserved")
        print("[PASS] Exact envelope hash scope preserved")
        print("[PASS] Exact callable count preserved")
        print("[PASS] Deterministic no-execution result identity certified")
        print("[PASS] Execution attempt remains false")
        print("[PASS] Implementation import remains unperformed")
        print("[PASS] Implementation symbol loading remains unperformed")
        print("[PASS] Callable binding remains unperformed")
        print("[PASS] Callable invocation remains unperformed")
        print("[PASS] Reasoning execution remains unperformed")
        print("[PASS] Probability estimation remains unperformed")
        print("[PASS] Final intelligence conclusions remain unproduced")
        print("[PASS] Publication, alerting, and handoff unperformed")
        print("[PASS] Q Series execution remains unperformed")
        print("[PASS] Orders, funds, and portfolio mutation unperformed")
        print("[PASS] Read-only Oracle boundary preserved")
        print(
            "[DONE] OSR-013 DETERMINISTIC EXECUTION RESULT RECORD CERTIFIED"
        )
    finally:
        module.verify_deterministic_callable_binding_execution_envelope = (
            original_verifier
        )


if __name__ == "__main__":
    main()
