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
from qseries_v2.integration.qseries_fill_confirmation_evidence_contract import (
    ENGINE_ID,
    SCHEMA_VERSION,
    FillConfirmationEvidenceContractError,
    FillConfirmationEvidenceStatus,
    FillConfirmationEvidenceType,
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


def expect_evidence_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except FillConfirmationEvidenceContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected FillConfirmationEvidenceContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-031",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-031",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T05:00:00-05:00"
        ),
    }


def make_confirmation_request(
    *,
    order_state: str = "filled",
    reported_quantity: str = "2",
    reported_price: str = "0.55",
):
    request = build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        account_reference="account-test",
        market_id="KXTEST-INT031",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.55",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id="client-order-int031",
        created_at=(
            "2026-07-11T05:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T05:10:00-05:00"
        ),
        rationale=(
            "Build INT-031 fill confirmation evidence "
            "contract test chain."
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
                "2026-07-11T05:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T05:00:00-05:00"
            ),
            registration_reason=(
                "INT-031 test registration."
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
            "2026-07-11T05:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T05:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T05:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T05:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T05:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T05:08:00-05:00"
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
            "2026-07-11T05:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T05:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T05:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T05:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T05:00:09-05:00"
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
            "2026-07-11T05:00:10-05:00"
        ),
        adapter_reference="adapter-ref-031",
        venue_reference="venue-ref-031",
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
                "2026-07-11T05:00:11-05:00"
            ),
        )
    )

    reconciliation_request = (
        build_execution_result_reconciliation_request(
            validation=result_validation,
            result=result,
            requested_at=(
                "2026-07-11T05:00:12-05:00"
            ),
        )
    )

    venue_evidence = build_venue_reconciliation_evidence(
        request=reconciliation_request,
        evidence_status="observed",
        order_state=order_state,
        observed_at=(
            "2026-07-11T05:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T05:00:13-05:00"
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
            "2026-07-11T05:00:15-05:00"
        ),
    )

    return build_fill_confirmation_request(
        reconciliation=reconciliation,
        evidence=venue_evidence,
        requested_at=(
            "2026-07-11T05:00:16-05:00"
        ),
    )


def test_observed_full_fill_evidence() -> None:
    request = make_confirmation_request()

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2.000",
        observed_average_price="0.5500",
        observed_at=(
            "2026-07-11T05:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T05:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Caller-supplied confirmation evidence reports "
            "a complete fill observation."
        ),
        confirmation_details={
            "source": "test",
            "fill_confirmation_performed": False,
        },
    )

    assert evidence.schema_version == SCHEMA_VERSION
    assert evidence.engine_id == ENGINE_ID

    assert (
        evidence.evidence_status
        is FillConfirmationEvidenceStatus.OBSERVED
    )

    assert (
        evidence.evidence_type
        is FillConfirmationEvidenceType.FULL
    )

    assert (
        evidence.observed_filled_quantity
        == "2"
    )

    assert (
        evidence.observed_average_price
        == "0.55"
    )

    assert (
        evidence.confirmation_request_id
        == request.confirmation_request_id
    )

    assert (
        evidence.confirmation_request_hash
        == request.request_hash
    )

    assert (
        evidence.reconciliation_id
        == request.reconciliation_id
    )

    assert (
        evidence.reconciliation_hash
        == request.reconciliation_hash
    )

    assert evidence.read_only is True
    assert evidence.evidence_record is True
    assert evidence.fill_confirmed is False
    assert evidence.funds_moved is False
    assert evidence.portfolio_mutated is False

    assert (
        evidence.confirmation_engine_required
        is True
    )

    assert len(evidence.evidence_hash) == 64


def test_partial_fill_evidence() -> None:
    request = make_confirmation_request(
        order_state="partially_filled",
        reported_quantity="1",
        reported_price="0.54",
    )

    evidence = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="partial",
        observed_filled_quantity="1",
        observed_average_price="0.54",
        observed_at=(
            "2026-07-11T05:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T05:00:17-05:00"
        ),
        reason_codes=(
            "partial_fill_evidence_observed",
        ),
        explanation=(
            "Partial fill evidence observed."
        ),
    )

    assert (
        evidence.evidence_type
        is FillConfirmationEvidenceType.PARTIAL
    )

    assert (
        evidence.observed_filled_quantity
        == "1"
    )

    assert evidence.fill_confirmed is False
    assert evidence.portfolio_mutated is False


def test_not_observed_evidence() -> None:
    request = make_confirmation_request()

    evidence = (
        build_not_observed_fill_confirmation_evidence(
            request=request,
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            reason_code=(
                "confirmation_evidence_not_observed"
            ),
            explanation=(
                "No independent confirmation evidence was observed."
            ),
            confirmation_details={
                "source_queried": False,
            },
        )
    )

    assert (
        evidence.evidence_status
        is FillConfirmationEvidenceStatus.NOT_OBSERVED
    )

    assert (
        evidence.evidence_type
        is FillConfirmationEvidenceType.NONE
    )

    assert evidence.observed_filled_quantity is None
    assert evidence.observed_average_price is None
    assert evidence.source_updated_at is None
    assert evidence.fill_confirmed is False


def test_determinism() -> None:
    request = make_confirmation_request()

    first = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2",
        observed_average_price="0.55",
        observed_at=(
            "2026-07-11T05:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T05:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Deterministic confirmation evidence."
        ),
        confirmation_details={
            "verified": False,
            "source": "test",
        },
    )

    second = build_fill_confirmation_evidence(
        request=request,
        evidence_status="observed",
        evidence_type="full",
        observed_filled_quantity="2.0",
        observed_average_price="0.550",
        observed_at=(
            "2026-07-11T05:00:18-05:00"
        ),
        source_updated_at=(
            "2026-07-11T05:00:17-05:00"
        ),
        reason_codes=(
            "fill_evidence_observed",
        ),
        explanation=(
            "Deterministic confirmation evidence."
        ),
        confirmation_details={
            "source": "test",
            "verified": False,
        },
    )

    assert first.evidence_id == second.evidence_id

    assert (
        first.evidence_hash
        == second.evidence_hash
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
                "2026-07-11T05:00:18-05:00"
            ),
            reason_code="not_observed",
            explanation="Immutability evidence.",
            confirmation_details={
                "source_queried": False,
            },
        )
    )

    try:
        evidence.fill_confirmed = True
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "fill confirmation evidence must be immutable"
        )

    try:
        evidence.confirmation_details[
            "source_queried"
        ] = True
    except TypeError:
        pass
    else:
        raise AssertionError(
            "confirmation details must be immutable"
        )


def test_observed_requires_quantity() -> None:
    request = make_confirmation_request()

    expect_evidence_error(
        lambda: build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity=None,
            observed_average_price="0.55",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Invalid observed evidence."
            ),
        ),
        "requires observed_filled_quantity",
    )


def test_observed_requires_price() -> None:
    request = make_confirmation_request()

    expect_evidence_error(
        lambda: build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price=None,
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Invalid observed evidence."
            ),
        ),
        "requires observed_average_price",
    )


def test_non_observed_rejects_fill_values() -> None:
    request = make_confirmation_request()

    expect_evidence_error(
        lambda: build_fill_confirmation_evidence(
            request=request,
            evidence_status="failed",
            evidence_type="none",
            observed_filled_quantity="2",
            observed_average_price=None,
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=None,
            reason_codes=(
                "confirmation_source_failed",
            ),
            explanation=(
                "Invalid failed evidence."
            ),
        ),
        "must not contain observed_filled_quantity",
    )


def test_source_update_cannot_follow_observation() -> None:
    request = make_confirmation_request()

    expect_evidence_error(
        lambda: build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.55",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:19-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Invalid temporal evidence."
            ),
        ),
        "must not be later than observed_at",
    )


def test_timestamp_required() -> None:
    request = make_confirmation_request()

    expect_evidence_error(
        lambda: (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T05:00:18"
                ),
                reason_code="not_observed",
                explanation=(
                    "Timestamp validation evidence."
                ),
            )
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_observed_full_fill_evidence()
    test_partial_fill_evidence()
    test_not_observed_evidence()
    test_determinism()
    test_immutability()
    test_observed_requires_quantity()
    test_observed_requires_price()
    test_non_observed_rejects_fill_values()
    test_source_update_cannot_follow_observation()
    test_timestamp_required()

    request = make_confirmation_request()

    evidence = (
        build_not_observed_fill_confirmation_evidence(
            request=request,
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            reason_code=(
                "confirmation_evidence_contract_only"
            ),
            explanation=(
                "Fill confirmation evidence contract validated "
                "without confirming a fill."
            ),
            confirmation_details={
                "environment": "test",
                "source_queried": False,
                "fill_confirmation_performed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "evidence_status": (
            evidence.evidence_status.value
        ),
        "evidence_type": (
            evidence.evidence_type.value
        ),
        "adapter_id": evidence.adapter_id,
        "reason_codes": list(
            evidence.reason_codes
        ),
        "read_only": evidence.read_only,
        "evidence_record": (
            evidence.evidence_record
        ),
        "fill_confirmed": (
            evidence.fill_confirmed
        ),
        "funds_moved": evidence.funds_moved,
        "portfolio_mutated": (
            evidence.portfolio_mutated
        ),
        "confirmation_engine_required": (
            evidence.confirmation_engine_required
        ),
    }

    print(
        "[PASS] INT-031 Q Series "
        "Fill Confirmation Evidence Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
