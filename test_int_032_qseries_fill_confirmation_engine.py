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
    build_fill_confirmation_request,
)
from qseries_v2.integration.qseries_fill_confirmation_engine import (
    ENGINE_ID,
    SCHEMA_VERSION,
    ConfirmedFillType,
    FillConfirmationEngineError,
    FillConfirmationStatus,
    confirm_fill_evidence,
)
from qseries_v2.integration.qseries_fill_confirmation_evidence_contract import (
    build_fill_confirmation_evidence,
    build_not_observed_fill_confirmation_evidence,
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
    build_venue_reconciliation_evidence,
)
from qseries_v2.integration.qseries_venue_reconciliation_engine import (
    reconcile_venue_evidence,
)


def expect_engine_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except FillConfirmationEngineError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected FillConfirmationEngineError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-032",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-032",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T06:00:00-05:00"
        ),
    }


def make_confirmation_request(
    *,
    order_state: str = "filled",
    reported_quantity: str = "2",
    reported_price: str = "0.56",
):
    request = build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        account_reference="account-test",
        market_id="KXTEST-INT032",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.56",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id="client-order-int032",
        created_at=(
            "2026-07-11T06:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T06:10:00-05:00"
        ),
        rationale=(
            "Build INT-032 fill confirmation engine test chain."
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
                "2026-07-11T06:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T06:00:00-05:00"
            ),
            registration_reason=(
                "INT-032 test registration."
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
            "2026-07-11T06:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T06:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T06:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T06:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T06:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T06:08:00-05:00"
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
            "2026-07-11T06:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T06:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T06:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T06:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T06:00:09-05:00"
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
            "2026-07-11T06:00:10-05:00"
        ),
        adapter_reference="adapter-ref-032",
        venue_reference="venue-ref-032",
        reason_codes=(
            "venue_submission_accepted",
        ),
        explanation=(
            "Submission acceptance evidence."
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
                "2026-07-11T06:00:11-05:00"
            ),
        )
    )

    reconciliation_request = (
        build_execution_result_reconciliation_request(
            validation=result_validation,
            result=result,
            requested_at=(
                "2026-07-11T06:00:12-05:00"
            ),
        )
    )

    venue_evidence = build_venue_reconciliation_evidence(
        request=reconciliation_request,
        evidence_status="observed",
        order_state=order_state,
        observed_at=(
            "2026-07-11T06:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T06:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            f"Venue evidence reports {order_state}."
        ),
        venue_details={
            "reported_filled_quantity": (
                reported_quantity
            ),
            "reported_average_price": (
                reported_price
            ),
        },
    )

    reconciliation = reconcile_venue_evidence(
        request=reconciliation_request,
        evidence=venue_evidence,
        reconciled_at=(
            "2026-07-11T06:00:15-05:00"
        ),
    )

    return build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=venue_evidence,
        requested_at=(
            "2026-07-11T06:00:16-05:00"
        ),
    )


def test_full_fill_confirmed() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2.000",
        observed_average_price="0.5600",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Independent confirmation evidence matches "
            "the reported full fill."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
        confirmation_details={
            "environment": "test",
            "position_state_updated": False,
        },
    )

    assert decision.schema_version == SCHEMA_VERSION
    assert decision.engine_id == ENGINE_ID

    assert (
        decision.status
        is FillConfirmationStatus.CONFIRMED
    )

    assert (
        decision.confirmed_fill_type
        is ConfirmedFillType.FULL
    )

    assert (
        decision.confirmed_filled_quantity
        == "2"
    )

    assert (
        decision.confirmed_average_price
        == "0.56"
    )

    assert decision.reason_codes == (
        "full_fill_confirmed",
    )

    assert (
        decision.confirmation_request_id
        == request.confirmation_request_id
    )

    assert (
        decision.confirmation_request_hash
        == request.request_hash
    )

    assert (
        decision.confirmation_evidence_id
        == evidence.evidence_id
    )

    assert (
        decision.confirmation_evidence_hash
        == evidence.evidence_hash
    )

    assert decision.read_only is True
    assert decision.execution_allowed is False
    assert decision.fill_confirmed is True
    assert decision.funds_moved is False
    assert decision.portfolio_mutated is False

    assert (
        decision.position_state_update_required
        is True
    )

    assert len(decision.confirmation_hash) == 64


def test_partial_fill_confirmed() -> None:
    request = make_confirmation_request(
        order_state="partially_filled",
        reported_quantity="1",
        reported_price="0.55",
    )

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="partial",
        observed_filled_quantity="1",
        observed_average_price="0.55",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "partial_fill_evidence_observed",
        ),
        explanation=(
            "Independent confirmation evidence matches "
            "the reported partial fill."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.CONFIRMED
    )

    assert (
        decision.confirmed_fill_type
        is ConfirmedFillType.PARTIAL
    )

    assert decision.reason_codes == (
        "partial_fill_confirmed",
    )

    assert decision.fill_confirmed is True

    assert (
        decision.position_state_update_required
        is True
    )

    assert decision.portfolio_mutated is False


def test_not_observed_unresolved() -> None:
    request = make_confirmation_request()

    evidence = (
        build_not_observed_fill_confirmation_evidence(
            request=request,
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            reason_code=(
                "confirmation_evidence_not_observed"
            ),
            explanation=(
                "No independent confirmation evidence was observed."
            ),
        )
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.UNRESOLVED
    )

    assert (
        decision.confirmed_fill_type
        is ConfirmedFillType.NONE
    )

    assert decision.reason_codes == (
        "fill_confirmation_evidence_unresolved",
    )

    assert decision.fill_confirmed is False

    assert (
        decision.position_state_update_required
        is False
    )


def test_fill_type_mismatch_blocked() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="partial",
        observed_filled_quantity="2",
        observed_average_price="0.56",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Mismatched evidence type."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.BLOCKED
    )

    assert (
        "fill_evidence_type_mismatch"
        in decision.reason_codes
    )

    assert decision.fill_confirmed is False
    assert decision.portfolio_mutated is False


def test_quantity_mismatch_blocked() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="1",
        observed_average_price="0.56",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Quantity mismatch evidence."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.BLOCKED
    )

    assert (
        "filled_quantity_mismatch"
        in decision.reason_codes
    )

    assert decision.fill_confirmed is False


def test_price_mismatch_blocked() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2",
        observed_average_price="0.57",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Price mismatch evidence."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.BLOCKED
    )

    assert (
        "average_price_mismatch"
        in decision.reason_codes
    )

    assert decision.fill_confirmed is False


def test_determinism() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2",
        observed_average_price="0.56",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Deterministic fill confirmation evidence."
        ),
    )

    first = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
        confirmation_details={
            "position_state_updated": False,
            "environment": "test",
        },
    )

    second = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
        confirmation_details={
            "environment": "test",
            "position_state_updated": False,
        },
    )

    assert (
        first.confirmation_id
        == second.confirmation_id
    )

    assert (
        first.confirmation_hash
        == second.confirmation_hash
    )

    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    request = make_confirmation_request()

    evidence = (
        build_not_observed_fill_confirmation_evidence(
            request=request,
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            reason_code="not_observed",
            explanation="Immutability evidence.",
        )
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
        confirmation_details={
            "position_state_updated": False,
        },
    )

    try:
        decision.fill_confirmed = True
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "fill confirmation decision must be immutable"
        )

    try:
        decision.confirmation_details[
            "position_state_updated"
        ] = True
    except TypeError:
        pass
    else:
        raise AssertionError(
            "confirmation details must be immutable"
        )


def test_confirmation_precedes_evidence_blocked() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2",
        observed_average_price="0.56",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Temporal validation evidence."
        ),
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:17-05:00"
        ),
    )

    assert (
        decision.status
        is FillConfirmationStatus.BLOCKED
    )

    assert (
        "confirmation_precedes_evidence"
        in decision.reason_codes
    )

    assert decision.fill_confirmed is False


def test_timestamp_required() -> None:
    request = make_confirmation_request()

    evidence = (
        build_not_observed_fill_confirmation_evidence(
            request=request,
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            reason_code="not_observed",
            explanation="Timestamp evidence.",
        )
    )

    expect_engine_error(
        lambda: confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_full_fill_confirmed()
    test_partial_fill_confirmed()
    test_not_observed_unresolved()
    test_fill_type_mismatch_blocked()
    test_quantity_mismatch_blocked()
    test_price_mismatch_blocked()
    test_determinism()
    test_immutability()
    test_confirmation_precedes_evidence_blocked()
    test_timestamp_required()

    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2",
        observed_average_price="0.56",
        observed_at=(
            "2026-07-11T06:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T06:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Canonical full-fill confirmation evidence."
        ),
        confirmation_details={
            "environment": "test",
            "portfolio_mutated": False,
        },
    )

    decision = confirm_fill_evidence(
        request=request,
        evidence=evidence,
        confirmed_at=(
            "2026-07-11T06:00:19-05:00"
        ),
        confirmation_details={
            "environment": "test",
            "position_state_updated": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "confirmation_status": (
            decision.status.value
        ),
        "confirmed_fill_type": (
            decision.confirmed_fill_type.value
        ),
        "confirmed_filled_quantity": (
            decision.confirmed_filled_quantity
        ),
        "confirmed_average_price": (
            decision.confirmed_average_price
        ),
        "adapter_id": decision.adapter_id,
        "reason_codes": list(
            decision.reason_codes
        ),
        "read_only": decision.read_only,
        "execution_allowed": (
            decision.execution_allowed
        ),
        "fill_confirmed": (
            decision.fill_confirmed
        ),
        "funds_moved": decision.funds_moved,
        "portfolio_mutated": (
            decision.portfolio_mutated
        ),
        "position_state_update_required": (
            decision.position_state_update_required
        ),
    }

    print(
        "[PASS] INT-032 Q Series "
        "Fill Confirmation Engine"
    )
    print(summary)


if __name__ == "__main__":
    main()
