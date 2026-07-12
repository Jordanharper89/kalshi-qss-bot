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
    ENGINE_ID,
    SCHEMA_VERSION,
    VenueEvidenceStatus,
    VenueOrderState,
    VenueReconciliationEvidenceContractError,
    build_not_queried_venue_evidence,
    build_venue_reconciliation_evidence,
)


def expect_evidence_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except VenueReconciliationEvidenceContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected VenueReconciliationEvidenceContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-028",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-028",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-11T02:00:00-05:00"
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
        market_id="KXTEST-INT028",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.52",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int028"
        ),
        created_at=(
            "2026-07-11T02:00:01-05:00"
        ),
        expires_at=(
            "2026-07-11T02:10:00-05:00"
        ),
        rationale=(
            "Build INT-028 venue evidence contract test chain."
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
                "2026-07-11T02:00:00-05:00"
            ),
            effective_at=(
                "2026-07-11T02:00:00-05:00"
            ),
            registration_reason=(
                "INT-028 test registration."
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
            "2026-07-11T02:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-11T02:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-11T02:00:04-05:00"
        ),
        expires_at=(
            "2026-07-11T02:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-11T02:00:05-05:00"
            ),
            expires_at=(
                "2026-07-11T02:08:00-05:00"
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
            "2026-07-11T02:00:06-05:00"
        ),
    )

    invocation_gate = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-11T02:00:07-05:00"
            ),
        )
    )

    execution_invocation = (
        build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=invocation_gate,
            prepared_at=(
                "2026-07-11T02:00:08-05:00"
            ),
            expires_at=(
                "2026-07-11T02:07:00-05:00"
            ),
        )
    )

    safety_decision = evaluate_execution_adapter_safety(
        invocation=execution_invocation,
        evaluated_at=(
            "2026-07-11T02:00:09-05:00"
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
            "2026-07-11T02:00:10-05:00"
        ),
        adapter_reference="adapter-ref-028",
        venue_reference="venue-ref-028",
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
                "2026-07-11T02:00:11-05:00"
            ),
        )
    )

    return (
        build_execution_result_reconciliation_request(
            validation=result_validation,
            result=result,
            requested_at=(
                "2026-07-11T02:00:12-05:00"
            ),
            reconciliation_context={
                "environment": "test",
                "venue_query_performed": False,
                "fill_confirmed": False,
            },
        )
    )


def test_observed_evidence_contract() -> None:
    request = make_reconciliation_request()

    evidence = build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state="resting",
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T02:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            "Caller-supplied venue evidence reports "
            "a resting order state."
        ),
        venue_details={
            "remaining_quantity": "2",
            "filled_quantity": "0",
            "venue_query_performed": True,
        },
    )

    assert evidence.schema_version == SCHEMA_VERSION
    assert evidence.engine_id == ENGINE_ID

    assert (
        evidence.evidence_status
        is VenueEvidenceStatus.OBSERVED
    )

    assert (
        evidence.order_state
        is VenueOrderState.RESTING
    )

    assert (
        evidence.reconciliation_request_id
        == request.reconciliation_request_id
    )

    assert (
        evidence.reconciliation_request_hash
        == request.request_hash
    )

    assert evidence.result_id == request.result_id
    assert evidence.result_hash == request.result_hash

    assert evidence.adapter_id == request.adapter_id

    assert (
        evidence.adapter_reference
        == request.adapter_reference
    )

    assert (
        evidence.venue_reference
        == request.venue_reference
    )

    assert evidence.read_only is True
    assert evidence.venue_query_record is True
    assert evidence.fill_confirmed is False
    assert evidence.funds_moved is False
    assert evidence.portfolio_mutated is False

    assert (
        evidence.reconciliation_engine_required
        is True
    )

    assert len(evidence.evidence_hash) == 64


def test_filled_is_evidence_not_confirmation() -> None:
    request = make_reconciliation_request()

    evidence = build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state="filled",
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T02:00:13-05:00"
        ),
        reason_codes=(
            "venue_reports_filled",
        ),
        explanation=(
            "Venue evidence reports a filled state. "
            "INT-028 does not confirm the fill."
        ),
        venue_details={
            "reported_filled_quantity": "2",
            "reported_average_price": "0.52",
        },
    )

    assert (
        evidence.order_state
        is VenueOrderState.FILLED
    )

    assert evidence.fill_confirmed is False
    assert evidence.funds_moved is False
    assert evidence.portfolio_mutated is False

    assert (
        evidence.reconciliation_engine_required
        is True
    )


def test_not_queried_evidence() -> None:
    request = make_reconciliation_request()

    evidence = build_not_queried_venue_evidence(
        request=request,
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        reason_code="venue_not_queried",
        explanation=(
            "INT-028 contract validation occurred "
            "without querying a venue."
        ),
        venue_details={
            "venue_query_performed": False,
        },
    )

    assert (
        evidence.evidence_status
        is VenueEvidenceStatus.NOT_QUERIED
    )

    assert (
        evidence.order_state
        is VenueOrderState.UNKNOWN
    )

    assert evidence.venue_updated_at is None
    assert evidence.fill_confirmed is False
    assert evidence.portfolio_mutated is False


def test_determinism() -> None:
    request = make_reconciliation_request()

    first = build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state="pending",
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T02:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            "Deterministic venue evidence."
        ),
        venue_details={
            "filled_quantity": "0",
            "remaining_quantity": "2",
        },
    )

    second = build_venue_reconciliation_evidence(
        request=request,
        evidence_status="observed",
        order_state="pending",
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        venue_updated_at=(
            "2026-07-11T02:00:13-05:00"
        ),
        reason_codes=(
            "venue_order_observed",
        ),
        explanation=(
            "Deterministic venue evidence."
        ),
        venue_details={
            "remaining_quantity": "2",
            "filled_quantity": "0",
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
    request = make_reconciliation_request()

    evidence = build_not_queried_venue_evidence(
        request=request,
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        reason_code="venue_not_queried",
        explanation="Immutability evidence.",
        venue_details={
            "venue_query_performed": False,
        },
    )

    try:
        evidence.order_state = (
            VenueOrderState.FILLED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "venue evidence must be immutable"
        )

    try:
        evidence.venue_details[
            "venue_query_performed"
        ] = True
    except TypeError:
        pass
    else:
        raise AssertionError(
            "venue details must be immutable"
        )


def test_observed_requires_known_state() -> None:
    request = make_reconciliation_request()

    expect_evidence_error(
        lambda: build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="unknown",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                "Invalid observed evidence."
            ),
        ),
        "must identify a non-unknown order state",
    )


def test_non_observed_requires_unknown_state() -> None:
    request = make_reconciliation_request()

    expect_evidence_error(
        lambda: build_venue_reconciliation_evidence(
            request=request,
            evidence_status="failed",
            order_state="resting",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=None,
            reason_codes=(
                "venue_query_failed",
            ),
            explanation=(
                "Invalid failed evidence."
            ),
        ),
        "non-observed evidence must use unknown order state",
    )


def test_venue_update_cannot_follow_observation() -> None:
    request = make_reconciliation_request()

    expect_evidence_error(
        lambda: build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="resting",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:15-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                "Invalid temporal evidence."
            ),
        ),
        "must not be later than observed_at",
    )


def test_timestamp_required() -> None:
    request = make_reconciliation_request()

    expect_evidence_error(
        lambda: build_not_queried_venue_evidence(
            request=request,
            observed_at=(
                "2026-07-11T02:00:14"
            ),
            reason_code="venue_not_queried",
            explanation=(
                "Timestamp validation evidence."
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_observed_evidence_contract()
    test_filled_is_evidence_not_confirmation()
    test_not_queried_evidence()
    test_determinism()
    test_immutability()
    test_observed_requires_known_state()
    test_non_observed_requires_unknown_state()
    test_venue_update_cannot_follow_observation()
    test_timestamp_required()

    request = make_reconciliation_request()

    evidence = build_not_queried_venue_evidence(
        request=request,
        observed_at=(
            "2026-07-11T02:00:14-05:00"
        ),
        reason_code=(
            "venue_evidence_contract_only"
        ),
        explanation=(
            "Venue reconciliation evidence contract validated "
            "without querying a venue."
        ),
        venue_details={
            "environment": "test",
            "venue_query_performed": False,
            "fill_confirmed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "evidence_status": (
            evidence.evidence_status.value
        ),
        "order_state": (
            evidence.order_state.value
        ),
        "adapter_id": evidence.adapter_id,
        "reason_codes": list(
            evidence.reason_codes
        ),
        "read_only": evidence.read_only,
        "venue_query_record": (
            evidence.venue_query_record
        ),
        "fill_confirmed": (
            evidence.fill_confirmed
        ),
        "funds_moved": evidence.funds_moved,
        "portfolio_mutated": (
            evidence.portfolio_mutated
        ),
        "reconciliation_engine_required": (
            evidence.reconciliation_engine_required
        ),
    }

    print(
        "[PASS] INT-028 Q Series "
        "Venue Reconciliation Evidence Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
