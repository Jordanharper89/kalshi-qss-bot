from __future__ import annotations

from dataclasses import FrozenInstanceError

from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
    QSeriesDryRunRuntimeAdapter,
)
from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
    evaluate_execution_adapter_admission,
)
from qseries_v2.integration.qseries_execution_adapter_contract import (
    build_execution_adapter_request,
)
from qseries_v2.integration.qseries_execution_adapter_invocation_contract import (
    build_execution_adapter_invocation,
)
from qseries_v2.integration.qseries_execution_adapter_registry import (
    ExecutionAdapterRegistry,
    build_execution_adapter_registration,
    validate_execution_adapter_request,
)
from qseries_v2.integration.qseries_execution_adapter_result_contract import (
    build_execution_adapter_result,
    build_not_called_execution_result,
)
from qseries_v2.integration.qseries_execution_adapter_result_validation_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterResultValidationError,
    ExecutionAdapterResultValidationStatus,
    validate_execution_adapter_result,
)
from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
    evaluate_execution_adapter_safety,
)
from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
    build_runtime_adapter_dispatch,
)
from qseries_v2.integration.qseries_runtime_adapter_interface import (
    build_runtime_adapter_invocation,
)
from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
    evaluate_runtime_adapter_invocation_gate,
)


def expect_validation_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionAdapterResultValidationError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionAdapterResultValidationError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-026",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-026",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T00:00:00-05:00"
        ),
    }


def make_chain():
    request = build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        account_reference=(
            "account-test"
        ),
        market_id="KXTEST-INT026",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.50",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int026"
        ),
        created_at=(
            "2026-07-11T00:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T00:10:00-05:00"
        ),
        rationale=(
            "Build INT-026 result validation test chain."
        ),
    )

    registration = (
        build_execution_adapter_registration(
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            adapter_name=(
                "Kalshi Execution Adapter"
            ),
            adapter_version="1.0.0",
            venue_id="kalshi",
            supported_market_prefixes=[
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
                "2026-07-11T00:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T00:00:00-05:00"
            ),
            registration_reason=(
                "INT-026 test registration."
            ),
        )
    )

    registry = ExecutionAdapterRegistry(
        [registration]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at=(
            "2026-07-11T00:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T00:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T00:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T00:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T00:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T00:08:00-05:00"
            ),
        )
    )

    dry_run_adapter = QSeriesDryRunRuntimeAdapter(
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        adapter_version="1.0.0-dry-run",
    )

    dry_run_response = dry_run_adapter.simulate(
        invocation=runtime_invocation,
        simulated_at=(
            "2026-07-11T00:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T00:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T00:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T00:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T00:00:09-05:00"
        ),
        safety_evidence={
            "environment": "test",
            "network_access_enabled": False,
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    return execution_invocation, safety_decision


def test_not_called_result_validated() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code="adapter_not_called",
        explanation=(
            "INT-026 validates a canonical not-called result."
        ),
        adapter_details={
            "execution_adapter_called": False,
            "exchange_called": False,
        },
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
        evidence={
            "environment": "test",
            "result_received": True,
            "fill_reconciliation_performed": False,
        },
    )

    assert validation.schema_version == SCHEMA_VERSION
    assert validation.engine_id == ENGINE_ID

    assert (
        validation.status
        is ExecutionAdapterResultValidationStatus.VALIDATED
    )

    assert validation.reason_codes == (
        "execution_adapter_result_validated",
    )

    assert (
        validation.execution_invocation_id
        == invocation.execution_invocation_id
    )

    assert (
        validation.execution_invocation_hash
        == invocation.invocation_hash
    )

    assert (
        validation.safety_decision_id
        == safety_decision.safety_decision_id
    )

    assert (
        validation.safety_hash
        == safety_decision.safety_hash
    )

    assert validation.result_id == result.result_id
    assert validation.result_hash == result.result_hash

    assert validation.adapter_id == result.adapter_id

    assert (
        validation.result_status
        == result.status.value
    )

    assert validation.read_only is True
    assert validation.execution_allowed is False
    assert validation.fill_confirmed is False
    assert validation.funds_moved is False
    assert validation.portfolio_mutated is False

    assert (
        validation.reconciliation_required
        is True
    )

    assert len(validation.validation_hash) == 64


def test_submission_accepted_result_validated() -> None:
    invocation, safety_decision = make_chain()

    result = build_execution_adapter_result(
        invocation=invocation,
        status="submission_accepted",
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        adapter_reference="adapter-ref-026",
        venue_reference="venue-ref-026",
        reason_codes=(
            "venue_submission_accepted",
        ),
        explanation=(
            "Caller-supplied evidence reports submission "
            "acceptance only."
        ),
        adapter_details={
            "fill_confirmed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
    )

    assert (
        validation.status
        is ExecutionAdapterResultValidationStatus.VALIDATED
    )

    assert (
        validation.result_status
        == "submission_accepted"
    )

    assert validation.fill_confirmed is False

    assert (
        validation.reconciliation_required
        is True
    )


def test_determinism() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code="adapter_not_called",
        explanation=(
            "Deterministic validation result."
        ),
    )

    first = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
        evidence={
            "result_received": True,
            "environment": "test",
        },
    )

    second = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
        evidence={
            "environment": "test",
            "result_received": True,
        },
    )

    assert (
        first.validation_id
        == second.validation_id
    )

    assert (
        first.validation_hash
        == second.validation_hash
    )

    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code="adapter_not_called",
        explanation="Immutability result.",
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
    )

    try:
        validation.status = (
            ExecutionAdapterResultValidationStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "result validation must be immutable"
        )

    try:
        validation.checks[
            "adapter_identity_match"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "result validation checks must be immutable"
        )


def test_result_precedes_invocation_blocked() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:07-05:00"
        ),
        reason_code="adapter_not_called",
        explanation=(
            "Deliberately early result."
        ),
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
    )

    assert (
        validation.status
        is ExecutionAdapterResultValidationStatus.BLOCKED
    )

    assert (
        "result_precedes_invocation"
        in validation.reason_codes
    )

    assert validation.execution_allowed is False
    assert validation.fill_confirmed is False
    assert validation.portfolio_mutated is False


def test_validation_precedes_result_blocked() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code="adapter_not_called",
        explanation=(
            "Canonical result."
        ),
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:09-05:00"
        ),
    )

    assert (
        validation.status
        is ExecutionAdapterResultValidationStatus.BLOCKED
    )

    assert (
        "validation_precedes_result"
        in validation.reason_codes
    )


def test_timestamp_required() -> None:
    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code="adapter_not_called",
        explanation="Timestamp test result.",
    )

    expect_validation_error(
        lambda: validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_not_called_result_validated()
    test_submission_accepted_result_validated()
    test_determinism()
    test_immutability()
    test_result_precedes_invocation_blocked()
    test_validation_precedes_result_blocked()
    test_timestamp_required()

    invocation, safety_decision = make_chain()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-11T00:00:10-05:00"
        ),
        reason_code=(
            "adapter_not_called"
        ),
        explanation=(
            "Execution adapter result validation "
            "completed without adapter invocation."
        ),
        adapter_details={
            "environment": "test",
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "fill_confirmed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T00:00:11-05:00"
        ),
        evidence={
            "environment": "test",
            "result_received": True,
            "fill_reconciliation_performed": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "validation_status": (
            validation.status.value
        ),
        "result_status": (
            validation.result_status
        ),
        "adapter_id": (
            validation.adapter_id
        ),
        "reason_codes": list(
            validation.reason_codes
        ),
        "read_only": validation.read_only,
        "execution_allowed": (
            validation.execution_allowed
        ),
        "fill_confirmed": (
            validation.fill_confirmed
        ),
        "funds_moved": (
            validation.funds_moved
        ),
        "portfolio_mutated": (
            validation.portfolio_mutated
        ),
        "reconciliation_required": (
            validation.reconciliation_required
        ),
    }

    print(
        "[PASS] INT-026 Q Series "
        "Execution Adapter Result Validation Gate"
    )
    print(summary)


if __name__ == "__main__":
    main()
