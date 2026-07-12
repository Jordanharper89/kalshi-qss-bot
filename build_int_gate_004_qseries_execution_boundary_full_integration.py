from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_int_gate_004_qseries_execution_boundary_full_integration.py"
)


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
        DryRunDecision,
        QSeriesDryRunRuntimeAdapter,
    )
    from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
        AdapterAdmissionStatus,
        evaluate_execution_adapter_admission,
    )
    from qseries_v2.integration.qseries_execution_adapter_contract import (
        AdapterRequestStatus,
        build_execution_adapter_request,
        build_not_executed_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_invocation_contract import (
        ExecutionInvocationStatus,
        build_execution_adapter_invocation,
    )
    from qseries_v2.integration.qseries_execution_adapter_registry import (
        AdapterValidationStatus,
        ExecutionAdapterRegistry,
        build_execution_adapter_registration,
        validate_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
        ExecutionAdapterSafetyStatus,
        evaluate_execution_adapter_safety,
    )
    from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
        RuntimeDispatchStatus,
        build_runtime_adapter_dispatch,
    )
    from qseries_v2.integration.qseries_runtime_adapter_interface import (
        RuntimeInvocationStatus,
        RuntimeResultStatus,
        build_runtime_adapter_invocation,
    )
    from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
        RuntimeInvocationGateStatus,
        evaluate_runtime_adapter_invocation_gate,
    )


    SCHEMA_VERSION = "INT-GATE-004"
    ENGINE_ID = "INT-GATE-004"


    def make_int_015_authorization() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": (
                "final-auth-int-gate-004"
            ),
            "authorization_status": "authorized",
            "opportunity_id": (
                "opportunity-int-gate-004"
            ),
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-10T22:00:00-05:00"
            ),
            "explanation": {
                "gate": (
                    "full execution boundary integration"
                ),
                "decision": (
                    "authorized for deterministic "
                    "non-live integration validation"
                ),
                "live_execution": False,
            },
        }


    def make_registration():
        return build_execution_adapter_registration(
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            adapter_name=(
                "Kalshi Execution Adapter"
            ),
            adapter_version="1.0.0",
            venue_id="kalshi",
            supported_market_prefixes=[
                "kxgate",
                "kxtest",
            ],
            supported_actions=[
                "buy",
                "sell",
            ],
            supported_order_types=[
                "limit",
                "market",
            ],
            supported_price_units=[
                "usd_probability",
            ],
            lifecycle_status="registered",
            registered_at=(
                "2026-07-10T22:00:01-05:00"
            ),
            effective_at=(
                "2026-07-10T22:00:01-05:00"
            ),
            registration_reason=(
                "Register deterministic full integration "
                "gate adapter identity."
            ),
            metadata={
                "environment": "integration",
                "network_access_enabled": False,
                "live_execution_enabled": False,
            },
        )


    def valid_safety_evidence() -> dict:
        return {
            "environment": "integration",
            "network_access_enabled": False,
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }


    def build_full_pipeline():
        authorization = make_int_015_authorization()

        request = build_execution_adapter_request(
            authorization_record=authorization,
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            account_reference=(
                "account-integration"
            ),
            market_id="KXGATE-INT004",
            action="buy",
            order_type="limit",
            quantity="7",
            limit_price="0.49",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int-gate-004"
            ),
            created_at=(
                "2026-07-10T22:00:02-05:00"
            ),
            expires_at=(
                "2026-07-10T22:15:00-05:00"
            ),
            rationale=(
                "Validate the complete Q Series "
                "execution-boundary integration chain."
            ),
            metadata={
                "integration_gate": SCHEMA_VERSION,
                "network_access_enabled": False,
                "live_execution_enabled": False,
            },
        )

        registration = make_registration()

        registry = ExecutionAdapterRegistry(
            [registration]
        )

        validation = validate_execution_adapter_request(
            request=request,
            registry=registry,
            validated_at=(
                "2026-07-10T22:00:03-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T22:00:04-05:00"
            ),
            evidence={
                "authorization_schema": "INT-015",
                "request_schema": "INT-016",
                "validation_schema": "INT-017",
                "adapter_invoked": False,
                "exchange_called": False,
                "live_order_submitted": False,
            },
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T22:00:05-05:00"
            ),
            expires_at=(
                "2026-07-10T22:14:00-05:00"
            ),
            runtime_context={
                "environment": "integration",
                "network_access_enabled": False,
                "adapter_invoked": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-10T22:00:06-05:00"
                ),
                expires_at=(
                    "2026-07-10T22:13:00-05:00"
                ),
                invocation_context={
                    "environment": "integration",
                    "network_access_enabled": False,
                    "adapter_called": False,
                },
            )
        )

        dry_run_adapter = QSeriesDryRunRuntimeAdapter(
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            adapter_version=(
                "1.0.0-integration-dry-run"
            ),
        )

        dry_run_response = dry_run_adapter.simulate(
            invocation=runtime_invocation,
            simulated_at=(
                "2026-07-10T22:00:07-05:00"
            ),
            simulation_context={
                "environment": "integration",
                "integration_gate": SCHEMA_VERSION,
                "network_access_enabled": False,
            },
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-10T22:00:08-05:00"
                ),
                evidence={
                    "environment": "integration",
                    "execution_adapter_connected": False,
                    "network_access_enabled": False,
                    "adapter_invoked": False,
                    "exchange_called": False,
                    "live_order_submitted": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-10T22:00:09-05:00"
                ),
                expires_at=(
                    "2026-07-10T22:12:00-05:00"
                ),
                execution_context={
                    "environment": "integration",
                    "network_access_enabled": False,
                    "execution_adapter_connected": False,
                    "execution_adapter_called": False,
                    "exchange_called": False,
                    "live_order_submitted": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )
        )

        safety_decision = (
            evaluate_execution_adapter_safety(
                invocation=execution_invocation,
                evaluated_at=(
                    "2026-07-10T22:00:10-05:00"
                ),
                safety_evidence=(
                    valid_safety_evidence()
                ),
            )
        )

        terminal_result = build_not_executed_result(
            request=request,
            processed_at=(
                "2026-07-10T22:00:11-05:00"
            ),
            reason_code=(
                "full_integration_gate_non_execution"
            ),
            explanation=(
                "INT-GATE-004 validated the full "
                "Q Series execution boundary through "
                "INT-024 without invoking an execution "
                "adapter or performing execution."
            ),
            details={
                "integration_gate": SCHEMA_VERSION,
                "safety_decision_id": (
                    safety_decision.safety_decision_id
                ),
                "safety_hash": (
                    safety_decision.safety_hash
                ),
                "execution_adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        return {
            "authorization": authorization,
            "request": request,
            "registration": registration,
            "registry": registry,
            "validation": validation,
            "admission": admission,
            "dispatch": dispatch,
            "runtime_invocation": runtime_invocation,
            "dry_run_response": dry_run_response,
            "invocation_gate": invocation_gate,
            "execution_invocation": execution_invocation,
            "safety_decision": safety_decision,
            "terminal_result": terminal_result,
        }


    def test_full_pipeline_status_chain() -> None:
        pipeline = build_full_pipeline()

        assert (
            pipeline["request"].request_status
            is AdapterRequestStatus.READY_FOR_ADAPTER
        )

        assert (
            pipeline["validation"].status
            is AdapterValidationStatus.APPROVED
        )

        assert (
            pipeline["admission"].status
            is AdapterAdmissionStatus.ADMITTED
        )

        assert (
            pipeline["dispatch"].status
            is RuntimeDispatchStatus.READY_FOR_RUNTIME
        )

        assert (
            pipeline["runtime_invocation"].status
            is RuntimeInvocationStatus.READY
        )

        assert (
            pipeline[
                "dry_run_response"
            ].receipt.decision
            is DryRunDecision.SIMULATED
        )

        assert (
            pipeline[
                "dry_run_response"
            ].result.status
            is RuntimeResultStatus.NOT_INVOKED
        )

        assert (
            pipeline["invocation_gate"].status
            is RuntimeInvocationGateStatus.ELIGIBLE
        )

        assert (
            pipeline["execution_invocation"].status
            is ExecutionInvocationStatus.READY_FOR_EXECUTION_ADAPTER
        )

        assert (
            pipeline["safety_decision"].status
            is ExecutionAdapterSafetyStatus.SAFETY_VERIFIED
        )

        assert (
            pipeline["terminal_result"].status.value
            == "not_executed"
        )


    def test_complete_hash_evidence_chain() -> None:
        pipeline = build_full_pipeline()

        request = pipeline["request"]
        validation = pipeline["validation"]
        admission = pipeline["admission"]
        dispatch = pipeline["dispatch"]
        runtime_invocation = pipeline[
            "runtime_invocation"
        ]
        dry_run_response = pipeline[
            "dry_run_response"
        ]
        invocation_gate = pipeline[
            "invocation_gate"
        ]
        execution_invocation = pipeline[
            "execution_invocation"
        ]
        safety_decision = pipeline[
            "safety_decision"
        ]

        assert (
            validation.request_id
            == request.request_id
        )

        assert (
            admission.request_id
            == request.request_id
        )

        assert (
            admission.request_contract_hash
            == request.contract_hash
        )

        assert (
            admission.validation_id
            == validation.validation_id
        )

        assert (
            admission.validation_hash
            == validation.validation_hash
        )

        assert (
            dispatch.request_id
            == request.request_id
        )

        assert (
            dispatch.request_contract_hash
            == request.contract_hash
        )

        assert (
            dispatch.validation_id
            == validation.validation_id
        )

        assert (
            dispatch.validation_hash
            == validation.validation_hash
        )

        assert (
            dispatch.admission_id
            == admission.admission_id
        )

        assert (
            dispatch.admission_hash
            == admission.admission_hash
        )

        assert (
            runtime_invocation.dispatch_id
            == dispatch.dispatch_id
        )

        assert (
            runtime_invocation.dispatch_hash
            == dispatch.dispatch_hash
        )

        assert (
            dry_run_response.receipt.invocation_id
            == runtime_invocation.invocation_id
        )

        assert (
            dry_run_response.receipt.invocation_hash
            == runtime_invocation.invocation_hash
        )

        assert (
            dry_run_response.result.invocation_id
            == runtime_invocation.invocation_id
        )

        assert (
            dry_run_response.result.invocation_hash
            == runtime_invocation.invocation_hash
        )

        assert (
            invocation_gate.invocation_id
            == runtime_invocation.invocation_id
        )

        assert (
            invocation_gate.invocation_hash
            == runtime_invocation.invocation_hash
        )

        assert (
            invocation_gate.dry_run_receipt_id
            == dry_run_response.receipt.receipt_id
        )

        assert (
            invocation_gate.dry_run_receipt_hash
            == dry_run_response.receipt.receipt_hash
        )

        assert (
            invocation_gate.dry_run_result_id
            == dry_run_response.result.result_id
        )

        assert (
            invocation_gate.dry_run_result_hash
            == dry_run_response.result.result_hash
        )

        assert (
            execution_invocation.runtime_invocation_id
            == runtime_invocation.invocation_id
        )

        assert (
            execution_invocation.runtime_invocation_hash
            == runtime_invocation.invocation_hash
        )

        assert (
            execution_invocation.gate_id
            == invocation_gate.gate_id
        )

        assert (
            execution_invocation.gate_hash
            == invocation_gate.gate_hash
        )

        assert (
            safety_decision.execution_invocation_id
            == execution_invocation.execution_invocation_id
        )

        assert (
            safety_decision.execution_invocation_hash
            == execution_invocation.invocation_hash
        )


    def test_adapter_identity_is_canonical() -> None:
        pipeline = build_full_pipeline()

        expected = "adapter.kalshi.execution"

        assert (
            pipeline["registration"].adapter_id
            == expected
        )

        assert (
            pipeline["request"].adapter_id
            == expected
        )

        assert (
            pipeline["validation"].adapter_id
            == expected
        )

        assert (
            pipeline["admission"].adapter_id
            == expected
        )

        assert (
            pipeline["dispatch"].adapter_id
            == expected
        )

        assert (
            pipeline["runtime_invocation"].adapter_id
            == expected
        )

        assert (
            pipeline[
                "dry_run_response"
            ].receipt.adapter_id
            == expected
        )

        assert (
            pipeline[
                "dry_run_response"
            ].result.adapter_id
            == expected
        )

        assert (
            pipeline["invocation_gate"].adapter_id
            == expected
        )

        assert (
            pipeline["execution_invocation"].adapter_id
            == expected
        )

        assert (
            pipeline["safety_decision"].adapter_id
            == expected
        )


    def test_deterministic_full_replay() -> None:
        first = build_full_pipeline()
        second = build_full_pipeline()

        deterministic_pairs = (
            (
                first["request"].request_id,
                second["request"].request_id,
            ),
            (
                first["request"].contract_hash,
                second["request"].contract_hash,
            ),
            (
                first["registry"].registry_hash,
                second["registry"].registry_hash,
            ),
            (
                first["validation"].validation_id,
                second["validation"].validation_id,
            ),
            (
                first["validation"].validation_hash,
                second["validation"].validation_hash,
            ),
            (
                first["admission"].admission_id,
                second["admission"].admission_id,
            ),
            (
                first["admission"].admission_hash,
                second["admission"].admission_hash,
            ),
            (
                first["dispatch"].dispatch_id,
                second["dispatch"].dispatch_id,
            ),
            (
                first["dispatch"].dispatch_hash,
                second["dispatch"].dispatch_hash,
            ),
            (
                first[
                    "runtime_invocation"
                ].invocation_id,
                second[
                    "runtime_invocation"
                ].invocation_id,
            ),
            (
                first[
                    "runtime_invocation"
                ].invocation_hash,
                second[
                    "runtime_invocation"
                ].invocation_hash,
            ),
            (
                first[
                    "dry_run_response"
                ].receipt.receipt_id,
                second[
                    "dry_run_response"
                ].receipt.receipt_id,
            ),
            (
                first[
                    "dry_run_response"
                ].receipt.receipt_hash,
                second[
                    "dry_run_response"
                ].receipt.receipt_hash,
            ),
            (
                first[
                    "dry_run_response"
                ].result.result_id,
                second[
                    "dry_run_response"
                ].result.result_id,
            ),
            (
                first[
                    "dry_run_response"
                ].result.result_hash,
                second[
                    "dry_run_response"
                ].result.result_hash,
            ),
            (
                first["invocation_gate"].gate_id,
                second["invocation_gate"].gate_id,
            ),
            (
                first["invocation_gate"].gate_hash,
                second["invocation_gate"].gate_hash,
            ),
            (
                first[
                    "execution_invocation"
                ].execution_invocation_id,
                second[
                    "execution_invocation"
                ].execution_invocation_id,
            ),
            (
                first[
                    "execution_invocation"
                ].invocation_hash,
                second[
                    "execution_invocation"
                ].invocation_hash,
            ),
            (
                first[
                    "safety_decision"
                ].safety_decision_id,
                second[
                    "safety_decision"
                ].safety_decision_id,
            ),
            (
                first[
                    "safety_decision"
                ].safety_hash,
                second[
                    "safety_decision"
                ].safety_hash,
            ),
            (
                first[
                    "terminal_result"
                ].result_id,
                second[
                    "terminal_result"
                ].result_id,
            ),
            (
                first[
                    "terminal_result"
                ].result_hash,
                second[
                    "terminal_result"
                ].result_hash,
            ),
        )

        for first_value, second_value in deterministic_pairs:
            assert first_value == second_value


    def test_execution_boundary_remains_closed() -> None:
        pipeline = build_full_pipeline()

        authorization = pipeline["authorization"]
        request = pipeline["request"]
        validation = pipeline["validation"]
        admission = pipeline["admission"]
        dispatch = pipeline["dispatch"]
        runtime_invocation = pipeline[
            "runtime_invocation"
        ]
        dry_run_receipt = pipeline[
            "dry_run_response"
        ].receipt
        dry_run_result = pipeline[
            "dry_run_response"
        ].result
        invocation_gate = pipeline[
            "invocation_gate"
        ]
        execution_invocation = pipeline[
            "execution_invocation"
        ]
        safety_decision = pipeline[
            "safety_decision"
        ]
        terminal_result = pipeline[
            "terminal_result"
        ]

        assert authorization["read_only"] is True
        assert authorization["execution_allowed"] is False
        assert (
            authorization["adapter_execution_required"]
            is True
        )

        assert request.read_only is True
        assert request.execution_allowed is False
        assert (
            request.requires_concrete_adapter
            is True
        )

        assert validation.read_only is True
        assert validation.execution_allowed is False
        assert (
            validation.runtime_processing_required
            is True
        )

        assert admission.read_only is True
        assert admission.execution_allowed is False
        assert (
            admission.runtime_adapter_required
            is True
        )

        assert dispatch.read_only is True
        assert dispatch.execution_allowed is False
        assert (
            dispatch.adapter_invocation_required
            is True
        )
        assert dispatch.live_order_submitted is False

        assert runtime_invocation.read_only is True
        assert (
            runtime_invocation.execution_allowed
            is False
        )
        assert (
            runtime_invocation.adapter_call_required
            is True
        )
        assert runtime_invocation.adapter_called is False

        assert dry_run_receipt.read_only is True
        assert (
            dry_run_receipt.network_access_enabled
            is False
        )
        assert dry_run_receipt.adapter_called is False
        assert dry_run_receipt.exchange_called is False
        assert (
            dry_run_receipt.live_order_submitted
            is False
        )
        assert dry_run_receipt.funds_moved is False
        assert (
            dry_run_receipt.portfolio_mutated
            is False
        )

        assert dry_run_result.read_only is True
        assert (
            dry_run_result.status
            is RuntimeResultStatus.NOT_INVOKED
        )
        assert (
            dry_run_result.live_order_submitted
            is False
        )
        assert dry_run_result.funds_moved is False
        assert (
            dry_run_result.portfolio_mutated
            is False
        )

        assert invocation_gate.read_only is True
        assert (
            invocation_gate.execution_allowed
            is False
        )
        assert (
            invocation_gate.execution_adapter_required
            is True
        )
        assert invocation_gate.adapter_invoked is False
        assert invocation_gate.exchange_called is False
        assert (
            invocation_gate.live_order_submitted
            is False
        )
        assert invocation_gate.funds_moved is False
        assert (
            invocation_gate.portfolio_mutated
            is False
        )

        assert execution_invocation.read_only is True
        assert (
            execution_invocation.execution_allowed
            is False
        )
        assert (
            execution_invocation.execution_adapter_call_required
            is True
        )
        assert (
            execution_invocation.execution_adapter_called
            is False
        )
        assert (
            execution_invocation.exchange_called
            is False
        )
        assert (
            execution_invocation.live_order_submitted
            is False
        )
        assert (
            execution_invocation.funds_moved
            is False
        )
        assert (
            execution_invocation.portfolio_mutated
            is False
        )

        assert safety_decision.read_only is True
        assert (
            safety_decision.execution_allowed
            is False
        )
        assert (
            safety_decision.concrete_adapter_required
            is True
        )
        assert (
            safety_decision.execution_adapter_called
            is False
        )
        assert safety_decision.exchange_called is False
        assert (
            safety_decision.live_order_submitted
            is False
        )
        assert safety_decision.funds_moved is False
        assert (
            safety_decision.portfolio_mutated
            is False
        )

        assert terminal_result.read_only is True
        assert (
            terminal_result.status.value
            == "not_executed"
        )
        assert (
            terminal_result.executed_quantity
            == "0"
        )

        assert (
            terminal_result.details[
                "execution_adapter_called"
            ]
            is False
        )
        assert (
            terminal_result.details[
                "exchange_called"
            ]
            is False
        )
        assert (
            terminal_result.details[
                "live_order_submitted"
            ]
            is False
        )
        assert (
            terminal_result.details[
                "funds_moved"
            ]
            is False
        )
        assert (
            terminal_result.details[
                "portfolio_mutated"
            ]
            is False
        )


    def test_safety_gate_requires_explicit_evidence() -> None:
        pipeline = build_full_pipeline()

        invocation = pipeline[
            "execution_invocation"
        ]

        incomplete = evaluate_execution_adapter_safety(
            invocation=invocation,
            evaluated_at=(
                "2026-07-10T22:00:10-05:00"
            ),
            safety_evidence={
                "environment": "integration",
            },
        )

        assert (
            incomplete.status
            is ExecutionAdapterSafetyStatus.BLOCKED
        )

        assert (
            "network_safety_evidence_invalid"
            in incomplete.reason_codes
        )

        assert (
            "adapter_call_safety_evidence_invalid"
            in incomplete.reason_codes
        )

        assert (
            "exchange_call_safety_evidence_invalid"
            in incomplete.reason_codes
        )

        assert (
            "order_submission_safety_evidence_invalid"
            in incomplete.reason_codes
        )

        assert (
            "fund_movement_safety_evidence_invalid"
            in incomplete.reason_codes
        )

        assert (
            "portfolio_mutation_safety_evidence_invalid"
            in incomplete.reason_codes
        )


    def main() -> None:
        test_full_pipeline_status_chain()
        test_complete_hash_evidence_chain()
        test_adapter_identity_is_canonical()
        test_deterministic_full_replay()
        test_execution_boundary_remains_closed()
        test_safety_gate_requires_explicit_evidence()

        pipeline = build_full_pipeline()

        request = pipeline["request"]
        validation = pipeline["validation"]
        admission = pipeline["admission"]
        dispatch = pipeline["dispatch"]
        runtime_invocation = pipeline[
            "runtime_invocation"
        ]
        dry_run_response = pipeline[
            "dry_run_response"
        ]
        invocation_gate = pipeline[
            "invocation_gate"
        ]
        execution_invocation = pipeline[
            "execution_invocation"
        ]
        safety_decision = pipeline[
            "safety_decision"
        ]
        terminal_result = pipeline[
            "terminal_result"
        ]

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "request_status": (
                request.request_status.value
            ),
            "validation_status": (
                validation.status.value
            ),
            "admission_status": (
                admission.status.value
            ),
            "dispatch_status": (
                dispatch.status.value
            ),
            "runtime_invocation_status": (
                runtime_invocation.status.value
            ),
            "dry_run_decision": (
                dry_run_response.receipt.decision.value
            ),
            "dry_run_result_status": (
                dry_run_response.result.status.value
            ),
            "invocation_gate_status": (
                invocation_gate.status.value
            ),
            "execution_invocation_status": (
                execution_invocation.status.value
            ),
            "safety_status": (
                safety_decision.status.value
            ),
            "terminal_result_status": (
                terminal_result.status.value
            ),
            "adapter_id": (
                safety_decision.adapter_id
            ),
            "deterministic_replay": True,
            "canonical_evidence_chain": True,
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        print(
            "[PASS] INT-GATE-004 Q Series "
            "Execution Boundary Full Integration Gate"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] Wrote {path}")


def main() -> None:
    print("========================================")
    print(" INT-GATE-004 INSTALLER")
    print(" Q Series Execution Boundary")
    print(" Full Integration Gate")
    print("========================================")

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print("[DONE] INT-GATE-004 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_gate_004_qseries_execution_boundary_full_integration.py"
    )


if __name__ == "__main__":
    main()