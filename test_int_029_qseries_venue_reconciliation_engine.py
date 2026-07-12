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
    build_not_queried_venue_evidence,
    build_venue_reconciliation_evidence,
)
from qseries_v2.integration.qseries_venue_reconciliation_engine import (
    ENGINE_ID,
    SCHEMA_VERSION,
    VenueReconciliationEngineError,
    VenueReconciliationOutcome,
    VenueReconciliationStatus,
    reconcile_venue_evidence,
)


def expect_engine_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except VenueReconciliationEngineError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected VenueReconciliationEngineError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-029",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-029",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T03:00:00-05:00"
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
        market_id="KXTEST-INT029",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.53",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int029"
        ),
        created_at=(
            "2026-07-11T03:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T03:10:00-05:00"
        ),
        rationale=(
            "Build INT-029 venue reconciliation engine test chain."
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
                "2026-07-11T03:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T03:00:00-05:00"
            ),
            registration_reason=(
                "INT-029 test registration."
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
            "2026-07-11T03:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T03:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T03:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T03:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T03:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T03:08:00-05:00"
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
            "2026-07-11T03:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T03:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T03:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T03:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T03:00:09-05:00"
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
            "2026-07-11T03:00:10-05:00"
        ),
        adapter_reference="adapter-ref-029",
        venue_reference="venue-ref-029",
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
                "2026-07-11T03:00:11-05:00"
            ),
        )
    )

    return (
        build_execution_result_reconciliation_request(
            validation=result_validation,
            result=result,
            requested_at=(
                "2026-07-11T03:00:12-05:00"
            ),
            reconciliation_context={
                "environment": "test",
                "venue_query_performed": False,
                "fill_confirmed": False,
            },
        )
    )


def make_observed_evidence(
    request,
    *,
    order_state: str,
    venue_details: dict | None = None,
):
    return build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state=order_state,
        observed_at=(
            "2026-07-11T03:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T03:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            f"Caller-supplied venue evidence reports "
            f"{order_state}."
        ),
        venue_details=venue_details,
    )


def test_resting_order_pending() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="resting",
        venue_details={
            "remaining_quantity": "2",
            "filled_quantity": "0",
        },
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
        reconciliation_details={
            "environment": "test",
            "fill_confirmation_performed": False,
        },
    )

    assert decision.schema_version == SCHEMA_VERSION
    assert decision.engine_id == ENGINE_ID

    assert (
        decision.status
        is VenueReconciliationStatus.PENDING
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.ORDER_RESTING
    )

    assert (
        decision.observed_order_state
        is VenueOrderState.RESTING
    )

    assert decision.reason_codes == (
        "venue_order_resting",
    )

    assert (
        decision.reconciliation_request_id
        == request.reconciliation_request_id
    )

    assert (
        decision.reconciliation_request_hash
        == request.request_hash
    )

    assert (
        decision.venue_evidence_id
        == evidence.evidence_id
    )

    assert (
        decision.venue_evidence_hash
        == evidence.evidence_hash
    )

    assert decision.read_only is True
    assert decision.execution_allowed is False
    assert decision.venue_state_classified is True
    assert decision.fill_confirmed is False
    assert decision.funds_moved is False
    assert decision.portfolio_mutated is False

    assert (
        decision.fill_confirmation_required
        is False
    )

    assert len(decision.reconciliation_hash) == 64


def test_full_fill_requires_confirmation() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.53",
        },
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
    )

    assert (
        decision.status
        is VenueReconciliationStatus.RECONCILED
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.FULL_FILL_REPORTED
    )

    assert (
        decision.observed_order_state
        is VenueOrderState.FILLED
    )

    assert decision.reason_codes == (
        "venue_full_fill_reported",
    )

    assert decision.fill_confirmed is False

    assert (
        decision.fill_confirmation_required
        is True
    )

    assert decision.funds_moved is False
    assert decision.portfolio_mutated is False


def test_partial_fill_requires_confirmation() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="partially_filled",
        venue_details={
            "reported_filled_quantity": "1",
            "reported_remaining_quantity": "1",
        },
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.PARTIAL_FILL_REPORTED
    )

    assert decision.fill_confirmed is False

    assert (
        decision.fill_confirmation_required
        is True
    )


def test_not_queried_unresolved() -> None:
    request = make_reconciliation_request()

    evidence = build_not_queried_venue_evidence(
        request=request,
        observed_at=(
            "2026-07-11T03:00:14-05:00"
        ),
        reason_code="venue_not_queried",
        explanation=(
            "Venue was not queried."
        ),
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
    )

    assert (
        decision.status
        is VenueReconciliationStatus.UNRESOLVED
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.NO_OBSERVATION
    )

    assert decision.fill_confirmed is False

    assert (
        decision.fill_confirmation_required
        is False
    )


def test_canceled_order_reconciled() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="canceled",
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
    )

    assert (
        decision.status
        is VenueReconciliationStatus.RECONCILED
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.ORDER_CANCELED
    )

    assert decision.fill_confirmed is False

    assert (
        decision.fill_confirmation_required
        is False
    )


def test_determinism() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="filled",
        venue_details={
            "reported_average_price": "0.53",
            "reported_filled_quantity": "2",
        },
    )

    first = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
        reconciliation_details={
            "fill_confirmation_performed": False,
            "environment": "test",
        },
    )

    second = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
        reconciliation_details={
            "environment": "test",
            "fill_confirmation_performed": False,
        },
    )

    assert (
        first.reconciliation_id
        == second.reconciliation_id
    )

    assert (
        first.reconciliation_hash
        == second.reconciliation_hash
    )

    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="resting",
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
    )

    try:
        decision.status = (
            VenueReconciliationStatus.RECONCILED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "venue reconciliation decision must be immutable"
        )

    try:
        decision.checks[
            "request_id_match"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "venue reconciliation checks must be immutable"
        )


def test_reconciliation_precedes_evidence_blocked() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="resting",
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:13-05:00"
        ),
    )

    assert (
        decision.status
        is VenueReconciliationStatus.BLOCKED
    )

    assert (
        decision.outcome
        is VenueReconciliationOutcome.INVALID_EVIDENCE_CHAIN
    )

    assert (
        "reconciliation_precedes_evidence"
        in decision.reason_codes
    )

    assert decision.fill_confirmed is False
    assert decision.portfolio_mutated is False


def test_timestamp_required() -> None:
    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="resting",
    )

    expect_engine_error(
        lambda: reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_resting_order_pending()
    test_full_fill_requires_confirmation()
    test_partial_fill_requires_confirmation()
    test_not_queried_unresolved()
    test_canceled_order_reconciled()
    test_determinism()
    test_immutability()
    test_reconciliation_precedes_evidence_blocked()
    test_timestamp_required()

    request = make_reconciliation_request()

    evidence = make_observed_evidence(
        request,
        order_state="filled",
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.53",
        },
    )

    decision = reconcile_venue_evidence(
        request=request,
        evidence=evidence,
        reconciled_at=(
            "2026-07-11T03:00:15-05:00"
        ),
        reconciliation_details={
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
        "reconciliation_status": (
            decision.status.value
        ),
        "outcome": decision.outcome.value,
        "observed_order_state": (
            decision.observed_order_state.value
        ),
        "adapter_id": decision.adapter_id,
        "reason_codes": list(
            decision.reason_codes
        ),
        "read_only": decision.read_only,
        "execution_allowed": (
            decision.execution_allowed
        ),
        "venue_state_classified": (
            decision.venue_state_classified
        ),
        "fill_confirmed": (
            decision.fill_confirmed
        ),
        "fill_confirmation_required": (
            decision.fill_confirmation_required
        ),
        "funds_moved": decision.funds_moved,
        "portfolio_mutated": (
            decision.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-029 Q Series "
        "Venue Reconciliation Engine"
    )
    print(summary)


if __name__ == "__main__":
    main()
