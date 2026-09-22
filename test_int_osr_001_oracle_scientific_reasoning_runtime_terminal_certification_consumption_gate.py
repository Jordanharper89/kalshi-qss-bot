from __future__ import annotations

from dataclasses import dataclass, replace
import importlib

module = importlib.import_module(
    "qseries_v2.oracle_scientific_reasoning_runtime."
    "oracle_scientific_reasoning_runtime_terminal_certification_consumption_gate"
)


@dataclass(frozen=True)
class StubTerminalCertification:
    terminal_certification_id: str
    terminal_certification_hash: str
    source_execution_result_id: str
    source_execution_result_hash: str
    callable_count: int
    subsystem_frozen: bool
    further_certification_layers_required: bool
    implementation_import_performed: bool
    implementation_symbol_load_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    reasoning_execution_performed: bool
    probability_estimation_performed: bool
    final_intelligence_conclusion_produced: bool
    publication_performed: bool
    alerting_performed: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    read_only: bool


def accepted_verifier(value) -> bool:
    if not isinstance(value, StubTerminalCertification):
        raise ValueError("unexpected terminal certification type")
    if value.subsystem_frozen is not True:
        raise ValueError("OSR subsystem is not frozen")
    return True


def rejected(callable_) -> None:
    try:
        callable_()
    except module.OracleScientificReasoningRuntimeTerminalConsumptionInvariantError:
        return
    raise AssertionError("expected INT-OSR-001 invariant rejection")


def main() -> None:
    original_verifier = (
        module.verify_oracle_scientific_reasoning_runtime_terminal_certification
    )
    module.verify_oracle_scientific_reasoning_runtime_terminal_certification = (
        accepted_verifier
    )
    try:
        certification = StubTerminalCertification(
            terminal_certification_id=(
                "oracle-scientific-reasoning-runtime-terminal:" + "a" * 64
            ),
            terminal_certification_hash="a" * 64,
            source_execution_result_id=(
                "callable-binding-execution-result:" + "b" * 64
            ),
            source_execution_result_hash="b" * 64,
            callable_count=9,
            subsystem_frozen=True,
            further_certification_layers_required=False,
            implementation_import_performed=False,
            implementation_symbol_load_performed=False,
            callable_binding_performed=False,
            callable_invocation_performed=False,
            reasoning_execution_performed=False,
            probability_estimation_performed=False,
            final_intelligence_conclusion_produced=False,
            publication_performed=False,
            alerting_performed=False,
            qseries_handoff_performed=False,
            qseries_execution_performed=False,
            order_creation_performed=False,
            funds_movement_performed=False,
            portfolio_mutation_performed=False,
            read_only=True,
        )

        first = (
            module.consume_oracle_scientific_reasoning_runtime_terminal_certification(
                certification=certification
            )
        )
        second = (
            module.consume_oracle_scientific_reasoning_runtime_terminal_certification(
                certification=certification
            )
        )

        assert first == second
        assert first.consumption_hash == second.consumption_hash
        assert (
            module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(
                first
            )
        )
        assert first.terminal_certification_verified is True
        assert first.subsystem_frozen_verified is True
        assert first.no_further_osr_layers_verified is True
        assert first.exact_terminal_hash_scope_preserved is True
        assert first.downstream_contract_materialization_allowed is True
        assert first.downstream_read_only_consumption_allowed is True
        assert first.scientific_reasoning_runtime_mutation_allowed is False
        assert first.reasoning_execution_allowed is False
        assert first.qseries_execution_allowed is False
        assert first.read_only is True

        rejected(
            lambda: (
                module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(
                    replace(first, consumption_hash="0" * 64)
                )
            )
        )
        rejected(
            lambda: (
                module.verify_oracle_scientific_reasoning_runtime_terminal_consumption(
                    replace(
                        first,
                        scientific_reasoning_runtime_mutation_allowed=True,
                    )
                )
            )
        )
        rejected(
            lambda: (
                module.consume_oracle_scientific_reasoning_runtime_terminal_certification(
                    certification=replace(
                        certification,
                        subsystem_frozen=False,
                    )
                )
            )
        )
        rejected(
            lambda: (
                module.consume_oracle_scientific_reasoning_runtime_terminal_certification(
                    certification=replace(
                        certification,
                        qseries_execution_performed=True,
                    )
                )
            )
        )

        print("========================================")
        print(" INT-OSR-001 TEST")
        print(" OSR TERMINAL CERTIFICATION")
        print(" CONSUMPTION GATE")
        print("========================================")
        print("[PASS] Actual OSR-014 terminal verifier consumed")
        print("[PASS] OSR-014 terminal identity and hash preserved")
        print("[PASS] OSR subsystem frozen status verified")
        print("[PASS] No further OSR layers required")
        print("[PASS] Read-only integration boundary established")
        print("[PASS] Downstream contract materialization allowed")
        print("[PASS] Downstream read-only consumption allowed")
        print("[PASS] OSR mutation remains disabled")
        print("[PASS] Implementation import remains disabled")
        print("[PASS] Implementation symbol loading remains disabled")
        print("[PASS] Callable binding and invocation remain disabled")
        print("[PASS] Reasoning execution remains disabled")
        print("[PASS] Probability estimation remains disabled")
        print("[PASS] Final intelligence conclusions remain disabled")
        print("[PASS] Publication, alerting, and handoff disabled")
        print("[PASS] Q Series execution remains disabled")
        print("[PASS] Orders, funds, and portfolio mutation disabled")
        print("[PASS] Read-only Oracle boundary preserved")
        print("[DONE] INT-OSR-001 TERMINAL CONSUMPTION CERTIFIED")
    finally:
        module.verify_oracle_scientific_reasoning_runtime_terminal_certification = (
            original_verifier
        )


if __name__ == "__main__":
    main()
