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
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterResultContractError,
    ExecutionAdapterResultStatus,
    build_execution_adapter_result,
    build_not_called_execution_result,
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


def expect_result_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionAdapterResultContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionAdapterResultContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-025",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-025",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T23:00:00-05:00"
        ),
    }


def make_execution_invocation():
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
        market_id="KXTEST-INT025",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.49",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int025"
        ),
        created_at=(
            "2026-07-10T23:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T23:10:00-05:00"
        ),
        rationale=(
            "Build INT-025 result contract test chain."
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
                "2026-07-10T23:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T23:00:00-05:00"
            ),
            registration_reason=(
                "INT-025 test registration."
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
            "2026-07-10T23:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T23:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T23:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T23:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T23:00:05-05:00"
            ),
            expires_at=(
                "2026-07-10T23:08:00-05:00"
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
            "2026-07-10T23:00:06-05:00"
        ),
    )

    gate_decision = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T23:00:07-05:00"
            ),
        )
    )

    return build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T23:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T23:07:00-05:00"
        ),
    )


def test_not_called_result() -> None:
    invocation = make_execution_invocation()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        reason_code=(
            "result_contract_only"
        ),
        explanation=(
            "INT-025 validated the adapter result contract "
            "without calling an execution adapter."
        ),
        adapter_details={
            "environment": "test",
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
        },
    )

    assert result.schema_version == SCHEMA_VERSION
    assert result.engine_id == ENGINE_ID

    assert (
        result.status
        is ExecutionAdapterResultStatus.NOT_CALLED
    )

    assert result.reason_codes == (
        "result_contract_only",
    )

    assert (
        result.execution_invocation_id
        == invocation.execution_invocation_id
    )

    assert (
        result.execution_invocation_hash
        == invocation.invocation_hash
    )

    assert (
        result.adapter_id
        == invocation.adapter_id
    )

    assert result.adapter_reference is None
    assert result.venue_reference is None
    assert result.read_only is True

    assert (
        result.execution_result_record
        is True
    )

    assert result.fill_confirmed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False

    assert len(result.result_hash) == 64


def test_submission_accepted_contract() -> None:
    invocation = make_execution_invocation()

    result = build_execution_adapter_result(
        invocation=invocation,
        status="submission_accepted",
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        adapter_reference=(
            "adapter-ref-025"
        ),
        venue_reference=(
            "venue-ref-025"
        ),
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

    assert (
        result.status
        is ExecutionAdapterResultStatus.SUBMISSION_ACCEPTED
    )

    assert (
        result.adapter_reference
        == "adapter-ref-025"
    )

    assert (
        result.venue_reference
        == "venue-ref-025"
    )

    assert result.fill_confirmed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False


def test_determinism() -> None:
    invocation = make_execution_invocation()

    first = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        reason_code=(
            "result_contract_only"
        ),
        explanation=(
            "Deterministic INT-025 result."
        ),
        adapter_details={
            "exchange_called": False,
            "execution_adapter_called": False,
        },
    )

    second = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        reason_code=(
            "result_contract_only"
        ),
        explanation=(
            "Deterministic INT-025 result."
        ),
        adapter_details={
            "execution_adapter_called": False,
            "exchange_called": False,
        },
    )

    assert first.result_id == second.result_id
    assert first.result_hash == second.result_hash
    assert first.to_dict() == second.to_dict()

    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    invocation = make_execution_invocation()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        reason_code="not_called",
        explanation=(
            "Immutability test result."
        ),
        adapter_details={
            "exchange_called": False,
        },
    )

    try:
        result.status = (
            ExecutionAdapterResultStatus.FAILED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "execution adapter result must be immutable"
        )

    try:
        result.adapter_details[
            "exchange_called"
        ] = True
    except TypeError:
        pass
    else:
        raise AssertionError(
            "adapter details must be immutable"
        )


def test_accepted_requires_references() -> None:
    invocation = make_execution_invocation()

    expect_result_error(
        lambda: build_execution_adapter_result(
            invocation=invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            adapter_reference=None,
            venue_reference=None,
            reason_codes=(
                "accepted",
            ),
            explanation=(
                "Invalid accepted result."
            ),
        ),
        "require adapter_reference",
    )


def test_not_called_rejects_references() -> None:
    invocation = make_execution_invocation()

    expect_result_error(
        lambda: build_execution_adapter_result(
            invocation=invocation,
            status="not_called",
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            adapter_reference=(
                "adapter-ref-invalid"
            ),
            venue_reference=None,
            reason_codes=(
                "not_called",
            ),
            explanation=(
                "Invalid not-called result."
            ),
        ),
        "must not contain adapter_reference",
    )


def test_timestamp_required() -> None:
    invocation = make_execution_invocation()

    expect_result_error(
        lambda: build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09"
            ),
            reason_code="not_called",
            explanation=(
                "Timestamp validation test."
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_not_called_result()
    test_submission_accepted_contract()
    test_determinism()
    test_immutability()
    test_accepted_requires_references()
    test_not_called_rejects_references()
    test_timestamp_required()

    invocation = make_execution_invocation()

    result = build_not_called_execution_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T23:00:09-05:00"
        ),
        reason_code=(
            "result_contract_only"
        ),
        explanation=(
            "Execution adapter result contract validated "
            "without adapter invocation."
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

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "result_status": result.status.value,
        "adapter_id": result.adapter_id,
        "reason_codes": list(
            result.reason_codes
        ),
        "read_only": result.read_only,
        "execution_result_record": (
            result.execution_result_record
        ),
        "fill_confirmed": (
            result.fill_confirmed
        ),
        "funds_moved": result.funds_moved,
        "portfolio_mutated": (
            result.portfolio_mutated
        ),
        "execution_adapter_called": False,
        "exchange_called": False,
        "live_order_submitted": False,
    }

    print(
        "[PASS] INT-025 Q Series "
        "Execution Adapter Result Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
