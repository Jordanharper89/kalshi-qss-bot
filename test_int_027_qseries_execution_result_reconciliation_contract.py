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
    validate_execution_adapter_result,
)
from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
    evaluate_execution_adapter_safety,
)
from qseries_v2.integration.qseries_execution_result_reconciliation_contract import (
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionResultReconciliationContractError,
    ReconciliationRequestStatus,
    ReconciliationTarget,
    build_execution_result_reconciliation_request,
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


def expect_contract_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionResultReconciliationContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionResultReconciliationContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-027",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-027",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T01:00:00-05:00"
        ),
    }


def make_execution_chain():
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
        market_id="KXTEST-INT027",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.51",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int027"
        ),
        created_at=(
            "2026-07-11T01:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T01:10:00-05:00"
        ),
        rationale=(
            "Build INT-027 reconciliation contract test chain."
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
                "2026-07-11T01:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T01:00:00-05:00"
            ),
            registration_reason=(
                "INT-027 test registration."
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
            "2026-07-11T01:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T01:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T01:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T01:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T01:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T01:08:00-05:00"
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
            "2026-07-11T01:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T01:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T01:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T01:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T01:00:09-05:00"
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


def make_validated_result(
    *,
    result_status: str,
):
    invocation, safety_decision = (
        make_execution_chain()
    )

    if result_status == "not_called":
        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T01:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation=(
                "Adapter was not called."
            ),
            adapter_details={
                "execution_adapter_called": False,
                "exchange_called": False,
            },
        )

    elif result_status == "submission_accepted":
        result = build_execution_adapter_result(
            invocation=invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-11T01:00:10-05:00"
            ),
            adapter_reference="adapter-ref-027",
            venue_reference="venue-ref-027",
            reason_codes=(
                "venue_submission_accepted",
            ),
            explanation=(
                "Submission accepted evidence."
            ),
            adapter_details={
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

    elif result_status == "rejected":
        result = build_execution_adapter_result(
            invocation=invocation,
            status="rejected",
            completed_at=(
                "2026-07-11T01:00:10-05:00"
            ),
            adapter_reference="adapter-ref-rejected-027",
            venue_reference=None,
            reason_codes=(
                "adapter_rejected_submission",
            ),
            explanation=(
                "Adapter rejected submission."
            ),
            adapter_details={
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

    else:
        raise AssertionError(
            f"unsupported test result status: {result_status}"
        )

    validation = validate_execution_adapter_result(
        invocation=invocation,
        safety_decision=safety_decision,
        result=result,
        validated_at=(
            "2026-07-11T01:00:11-05:00"
        ),
    )

    return validation, result


def test_submission_reconciliation_request() -> None:
    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
            reconciliation_context={
                "environment": "test",
                "venue_query_performed": False,
                "fill_confirmed": False,
            },
        )
    )

    assert request.schema_version == SCHEMA_VERSION
    assert request.engine_id == ENGINE_ID

    assert (
        request.status
        is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
    )

    assert (
        request.target
        is ReconciliationTarget.VENUE_SUBMISSION
    )

    assert request.reason_codes == (
        "venue_submission_reconciliation_required",
    )

    assert (
        request.result_validation_id
        == validation.validation_id
    )

    assert (
        request.result_validation_hash
        == validation.validation_hash
    )

    assert request.result_id == result.result_id
    assert request.result_hash == result.result_hash

    assert (
        request.execution_invocation_id
        == result.execution_invocation_id
    )

    assert request.adapter_id == result.adapter_id

    assert (
        request.adapter_reference
        == result.adapter_reference
    )

    assert (
        request.venue_reference
        == result.venue_reference
    )

    assert request.read_only is True
    assert request.execution_allowed is False

    assert (
        request.reconciliation_required
        is True
    )

    assert request.fill_confirmed is False
    assert request.funds_moved is False
    assert request.portfolio_mutated is False

    assert len(request.request_hash) == 64


def test_not_called_requires_no_reconciliation() -> None:
    validation, result = make_validated_result(
        result_status="not_called"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
        )
    )

    assert (
        request.status
        is ReconciliationRequestStatus.NO_RECONCILIATION_REQUIRED
    )

    assert (
        request.target
        is ReconciliationTarget.NONE
    )

    assert request.reason_codes == (
        "adapter_not_called_no_reconciliation_required",
    )

    assert (
        request.reconciliation_required
        is False
    )

    assert request.fill_confirmed is False
    assert request.portfolio_mutated is False


def test_rejected_result_reconciliation_request() -> None:
    validation, result = make_validated_result(
        result_status="rejected"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
        )
    )

    assert (
        request.status
        is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
    )

    assert (
        request.target
        is ReconciliationTarget.ADAPTER_OUTCOME
    )

    assert request.reason_codes == (
        "adapter_outcome_reconciliation_required",
    )

    assert (
        request.reconciliation_required
        is True
    )

    assert request.fill_confirmed is False


def test_determinism() -> None:
    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    first = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
            reconciliation_context={
                "fill_confirmed": False,
                "environment": "test",
            },
        )
    )

    second = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
            reconciliation_context={
                "environment": "test",
                "fill_confirmed": False,
            },
        )
    )

    assert (
        first.reconciliation_request_id
        == second.reconciliation_request_id
    )

    assert (
        first.request_hash
        == second.request_hash
    )

    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
        )
    )

    try:
        request.status = (
            ReconciliationRequestStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "reconciliation request must be immutable"
        )

    try:
        request.checks[
            "validation_validated"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "reconciliation checks must be immutable"
        )


def test_request_precedes_validation_blocked() -> None:
    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:10-05:00"
            ),
        )
    )

    assert (
        request.status
        is ReconciliationRequestStatus.BLOCKED
    )

    assert (
        "reconciliation_request_precedes_validation"
        in request.reason_codes
    )

    assert request.execution_allowed is False
    assert request.fill_confirmed is False
    assert request.portfolio_mutated is False


def test_timestamp_required() -> None:
    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    expect_contract_error(
        lambda: (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12"
                ),
            )
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_submission_reconciliation_request()
    test_not_called_requires_no_reconciliation()
    test_rejected_result_reconciliation_request()
    test_determinism()
    test_immutability()
    test_request_precedes_validation_blocked()
    test_timestamp_required()

    validation, result = make_validated_result(
        result_status="submission_accepted"
    )

    request = (
        build_execution_result_reconciliation_request(
            validation=validation,
            result=result,
            requested_at=(
                "2026-07-11T01:00:12-05:00"
            ),
            reconciliation_context={
                "environment": "test",
                "venue_query_performed": False,
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "reconciliation_status": (
            request.status.value
        ),
        "target": request.target.value,
        "result_status": request.result_status,
        "adapter_id": request.adapter_id,
        "reason_codes": list(
            request.reason_codes
        ),
        "read_only": request.read_only,
        "execution_allowed": (
            request.execution_allowed
        ),
        "reconciliation_required": (
            request.reconciliation_required
        ),
        "fill_confirmed": (
            request.fill_confirmed
        ),
        "funds_moved": request.funds_moved,
        "portfolio_mutated": (
            request.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-027 Q Series "
        "Execution Result Reconciliation Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
