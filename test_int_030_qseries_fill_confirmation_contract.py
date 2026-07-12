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
)
from qseries_v2.integration.qseries_execution_adapter_result_validation_gate import (
    validate_execution_adapter_result,
)
from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
    evaluate_execution_adapter_safety,
)
from qseries_v2.integration.qseries_execution_result_reconciliation_contract import (
    build_execution_result_reconciliation_request,
)
from qseries_v2.integration.qseries_fill_confirmation_contract import (
    ENGINE_ID,
    SCHEMA_VERSION,
    FillConfirmationContractError,
    FillConfirmationRequestStatus,
    ReportedFillType,
    build_fill_confirmation_request,
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
from qseries_v2.integration.qseries_venue_reconciliation_evidence_contract import (
    VenueOrderState,
    build_venue_reconciliation_evidence,
)
from qseries_v2.integration.qseries_venue_reconciliation_engine import (
    VenueReconciliationOutcome,
    reconcile_venue_evidence,
)


def expect_contract_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except FillConfirmationContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected FillConfirmationContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-030",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-030",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T04:00:00-05:00"
        ),
    }


def make_reconciliation_request():
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
        market_id="KXTEST-INT030",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.54",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int030"
        ),
        created_at=(
            "2026-07-11T04:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T04:10:00-05:00"
        ),
        rationale=(
            "Build INT-030 fill confirmation contract test chain."
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
                "2026-07-11T04:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T04:00:00-05:00"
            ),
            registration_reason=(
                "INT-030 test registration."
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
            "2026-07-11T04:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T04:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T04:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T04:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T04:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T04:08:00-05:00"
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
            "2026-07-11T04:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T04:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T04:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T04:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T04:00:09-05:00"
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

    result = build_execution_adapter_result(
        invocation=execution_invocation,
        status="submission_accepted",
        completed_at=(
            "2026-07-11T04:00:10-05:00"
        ),
        adapter_reference="adapter-ref-030",
        venue_reference="venue-ref-030",
        reason_codes=(
            "venue_submission_accepted",
        ),
        explanation=(
            "Caller-supplied adapter evidence reports "
            "submission acceptance only."
        ),
        adapter_details={
            "fill_confirmed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    result_validation = (
        validate_execution_adapter_result(
            invocation=execution_invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T04:00:11-05:00"
            ),
        )
    )

    return (
        build_execution_result_reconciliation_request(
            validation=result_validation,
            result=result,
            requested_at=(
                "2026-07-11T04:00:12-05:00"
            ),
        )
    )


def make_reconciliation(
    *,
    order_state: str,
    venue_details: dict | None = None,
):
    request = make_reconciliation_request()

    evidence = build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state=order_state,
        observed_at=(
            "2026-07-11T04:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T04:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            f"Venue evidence reports {order_state}."
        ),
        venue_details=venue_details,
    )

    reconciliation = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T04:00:15-05:00"
        ),
    )

    return reconciliation, evidence


def test_full_fill_confirmation_request() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.54",
        },
    )

    assert (
        reconciliation.outcome
        is VenueReconciliationOutcome.FULL_FILL_REPORTED
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
        confirmation_context={
            "environment": "test",
            "fill_confirmation_performed": False,
        },
    )

    assert request.schema_version == SCHEMA_VERSION
    assert request.engine_id == ENGINE_ID

    assert (
        request.status
        is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
    )

    assert (
        request.reported_fill_type
        is ReportedFillType.FULL
    )

    assert (
        request.reported_order_state
        is VenueOrderState.FILLED
    )

    assert (
        request.reported_filled_quantity
        == "2"
    )

    assert (
        request.reported_average_price
        == "0.54"
    )

    assert request.reason_codes == (
        "full_fill_confirmation_required",
    )

    assert (
        request.reconciliation_id
        == reconciliation.reconciliation_id
    )

    assert (
        request.reconciliation_hash
        == reconciliation.reconciliation_hash
    )

    assert (
        request.venue_evidence_id
        == evidence.evidence_id
    )

    assert (
        request.venue_evidence_hash
        == evidence.evidence_hash
    )

    assert request.result_id == evidence.result_id
    assert request.result_hash == evidence.result_hash

    assert request.adapter_id == evidence.adapter_id

    assert (
        request.venue_reference
        == evidence.venue_reference
    )

    assert request.read_only is True
    assert request.execution_allowed is False

    assert (
        request.fill_confirmation_required
        is True
    )

    assert request.fill_confirmed is False
    assert request.funds_moved is False
    assert request.portfolio_mutated is False

    assert len(request.request_hash) == 64


def test_partial_fill_confirmation_request() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="partially_filled",
        venue_details={
            "reported_filled_quantity": "1",
            "reported_average_price": "0.53",
            "reported_remaining_quantity": "1",
        },
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
    )

    assert (
        request.status
        is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
    )

    assert (
        request.reported_fill_type
        is ReportedFillType.PARTIAL
    )

    assert (
        request.reported_order_state
        is VenueOrderState.PARTIALLY_FILLED
    )

    assert (
        request.reported_filled_quantity
        == "1"
    )

    assert (
        request.reported_average_price
        == "0.53"
    )

    assert request.reason_codes == (
        "partial_fill_confirmation_required",
    )

    assert request.fill_confirmed is False


def test_resting_order_not_required() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="resting",
        venue_details={
            "reported_filled_quantity": "0",
        },
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
    )

    assert (
        request.status
        is FillConfirmationRequestStatus.NOT_REQUIRED
    )

    assert (
        request.reported_fill_type
        is ReportedFillType.NONE
    )

    assert request.reason_codes == (
        "fill_confirmation_not_required",
    )

    assert (
        request.fill_confirmation_required
        is False
    )

    assert request.fill_confirmed is False
    assert request.portfolio_mutated is False


def test_determinism() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_average_price": "0.54",
            "reported_filled_quantity": "2",
        },
    )

    first = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
        confirmation_context={
            "fill_confirmation_performed": False,
            "environment": "test",
        },
    )

    second = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
        confirmation_context={
            "environment": "test",
            "fill_confirmation_performed": False,
        },
    )

    assert (
        first.confirmation_request_id
        == second.confirmation_request_id
    )

    assert first.request_hash == second.request_hash

    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.54",
        },
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
    )

    try:
        request.status = (
            FillConfirmationRequestStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "fill confirmation request must be immutable"
        )

    try:
        request.checks[
            "result_id_match"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "fill confirmation checks must be immutable"
        )


def test_request_precedes_reconciliation_blocked() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.54",
        },
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:14-05:00"
        ),
    )

    assert (
        request.status
        is FillConfirmationRequestStatus.BLOCKED
    )

    assert (
        "confirmation_request_precedes_reconciliation"
        in request.reason_codes
    )

    assert request.fill_confirmed is False
    assert request.funds_moved is False
    assert request.portfolio_mutated is False


def test_timestamp_required() -> None:
    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.54",
        },
    )

    expect_contract_error(
        lambda: build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_full_fill_confirmation_request()
    test_partial_fill_confirmation_request()
    test_resting_order_not_required()
    test_determinism()
    test_immutability()
    test_request_precedes_reconciliation_blocked()
    test_timestamp_required()

    reconciliation, evidence = make_reconciliation(
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.54",
        },
    )

    request = build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=evidence,
        requested_at=(
            "2026-07-11T04:00:16-05:00"
        ),
        confirmation_context={
            "environment": "test",
            "fill_confirmation_performed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "confirmation_status": (
            request.status.value
        ),
        "reported_fill_type": (
            request.reported_fill_type.value
        ),
        "reported_order_state": (
            request.reported_order_state.value
        ),
        "reported_filled_quantity": (
            request.reported_filled_quantity
        ),
        "reported_average_price": (
            request.reported_average_price
        ),
        "adapter_id": request.adapter_id,
        "reason_codes": list(
            request.reason_codes
        ),
        "read_only": request.read_only,
        "execution_allowed": (
            request.execution_allowed
        ),
        "fill_confirmation_required": (
            request.fill_confirmation_required
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
        "[PASS] INT-030 Q Series "
        "Fill Confirmation Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
