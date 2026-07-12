from __future__ import annotations

from dataclasses import FrozenInstanceError

from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
    ENGINE_ID,
    SCHEMA_VERSION,
    DryRunDecision,
    DryRunRuntimeAdapterError,
    QSeriesDryRunRuntimeAdapter,
)
from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
    evaluate_execution_adapter_admission,
)
from qseries_v2.integration.qseries_execution_adapter_contract import (
    build_execution_adapter_request,
)
from qseries_v2.integration.qseries_execution_adapter_registry import (
    ExecutionAdapterRegistry,
    build_execution_adapter_registration,
    validate_execution_adapter_request,
)
from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
    build_runtime_adapter_dispatch,
)
from qseries_v2.integration.qseries_runtime_adapter_interface import (
    RuntimeResultStatus,
    build_runtime_adapter_invocation,
)


def expect_dry_run_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except DryRunRuntimeAdapterError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected DryRunRuntimeAdapterError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-021",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-021",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T18:00:00-05:00"
        ),
    }


def make_invocation(
    *,
    adapter_id: str = "adapter.kalshi.execution",
    market_id: str = "KXTEST-INT021",
    invocation_expires_at: str = (
        "2026-07-10T18:08:00-05:00"
    ),
):
    request = build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=adapter_id,
        account_reference="account-test",
        market_id=market_id,
        action="buy",
        order_type="limit",
        quantity="3",
        limit_price="0.45",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id="client-order-int021",
        created_at=(
            "2026-07-10T18:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T18:10:00-05:00"
        ),
        rationale=(
            "Build INT-021 dry-run adapter test chain."
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
                "2026-07-10T18:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T18:00:00-05:00"
            ),
            registration_reason=(
                "INT-021 test registration."
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
            "2026-07-10T18:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T18:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T18:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T18:09:00-05:00"
        ),
    )

    return build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T18:00:05-05:00"
        ),
        expires_at=invocation_expires_at,
        invocation_context={
            "environment": "test",
            "adapter_called": False,
            "network_access_enabled": False,
        },
    )


def make_adapter(
    *,
    adapter_id: str = "adapter.kalshi.execution",
) -> QSeriesDryRunRuntimeAdapter:
    return QSeriesDryRunRuntimeAdapter(
        adapter_id=adapter_id,
        adapter_version="1.0.0-dry-run",
    )


def test_successful_dry_run() -> None:
    invocation = make_invocation()
    adapter = make_adapter()

    response = adapter.simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
        simulation_context={
            "scenario": "unit-test",
            "network_access_enabled": False,
        },
    )

    receipt = response.receipt
    result = response.result

    assert receipt.schema_version == SCHEMA_VERSION
    assert receipt.engine_id == ENGINE_ID
    assert receipt.decision is DryRunDecision.SIMULATED
    assert (
        receipt.invocation_id
        == invocation.invocation_id
    )
    assert (
        receipt.invocation_hash
        == invocation.invocation_hash
    )
    assert receipt.adapter_id == invocation.adapter_id
    assert receipt.read_only is True
    assert receipt.network_access_enabled is False
    assert receipt.adapter_called is False
    assert receipt.exchange_called is False
    assert receipt.live_order_submitted is False
    assert receipt.funds_moved is False
    assert receipt.portfolio_mutated is False
    assert len(receipt.receipt_hash) == 64

    assert (
        result.status
        is RuntimeResultStatus.NOT_INVOKED
    )
    assert (
        result.invocation_id
        == invocation.invocation_id
    )
    assert result.adapter_reference is None
    assert result.read_only is True
    assert result.live_order_submitted is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False
    assert (
        result.details["dry_run_receipt_id"]
        == receipt.receipt_id
    )
    assert (
        result.details["dry_run_receipt_hash"]
        == receipt.receipt_hash
    )


def test_determinism() -> None:
    invocation = make_invocation()
    adapter = make_adapter()

    first = adapter.simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
        simulation_context={
            "network_access_enabled": False,
            "scenario": "deterministic",
        },
    )

    second = adapter.simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
        simulation_context={
            "scenario": "deterministic",
            "network_access_enabled": False,
        },
    )

    assert (
        first.receipt.receipt_id
        == second.receipt.receipt_id
    )
    assert (
        first.receipt.receipt_hash
        == second.receipt.receipt_hash
    )
    assert (
        first.receipt.to_dict()
        == second.receipt.to_dict()
    )
    assert (
        first.result.result_id
        == second.result.result_id
    )
    assert (
        first.result.result_hash
        == second.result.result_hash
    )
    assert (
        first.result.to_dict()
        == second.result.to_dict()
    )


def test_immutability() -> None:
    invocation = make_invocation()

    response = make_adapter().simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
    )

    try:
        response.receipt.decision = (
            DryRunDecision.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "dry-run receipt must be immutable"
        )

    try:
        response.receipt.checks[
            "invocation_ready"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "dry-run receipt checks must be immutable"
        )


def test_adapter_identity_mismatch_blocked() -> None:
    invocation = make_invocation()

    adapter = make_adapter(
        adapter_id="adapter.other.execution"
    )

    response = adapter.simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
    )

    assert (
        response.receipt.decision
        is DryRunDecision.BLOCKED
    )
    assert (
        response.receipt.checks[
            "adapter_id_matches"
        ]
        is False
    )
    assert (
        response.result.status
        is RuntimeResultStatus.REJECTED
    )
    assert (
        "adapter_id_matches"
        in response.result.reason_codes
    )
    assert (
        response.result.live_order_submitted
        is False
    )


def test_expired_invocation_blocked() -> None:
    invocation = make_invocation(
        invocation_expires_at=(
            "2026-07-10T18:00:06-05:00"
        )
    )

    response = make_adapter().simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:07-05:00"
        ),
    )

    assert (
        response.receipt.decision
        is DryRunDecision.BLOCKED
    )
    assert (
        response.receipt.checks[
            "invocation_not_expired"
        ]
        is False
    )
    assert (
        response.result.status
        is RuntimeResultStatus.REJECTED
    )
    assert (
        "invocation_not_expired"
        in response.result.reason_codes
    )
    assert (
        response.result.live_order_submitted
        is False
    )
    assert response.result.funds_moved is False
    assert response.result.portfolio_mutated is False


def test_protocol_invoke_disabled() -> None:
    invocation = make_invocation()
    adapter = make_adapter()

    expect_dry_run_error(
        lambda: adapter.invoke(invocation),
        "caller-supplied simulated_at",
    )


def test_timestamp_required() -> None:
    invocation = make_invocation()
    adapter = make_adapter()

    expect_dry_run_error(
        lambda: adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_successful_dry_run()
    test_determinism()
    test_immutability()
    test_adapter_identity_mismatch_blocked()
    test_expired_invocation_blocked()
    test_protocol_invoke_disabled()
    test_timestamp_required()

    invocation = make_invocation()
    adapter = make_adapter()

    response = adapter.simulate(
        invocation=invocation,
        simulated_at=(
            "2026-07-10T18:00:06-05:00"
        ),
        simulation_context={
            "environment": "test",
            "scenario": "summary",
            "network_access_enabled": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "decision": (
            response.receipt.decision.value
        ),
        "result_status": (
            response.result.status.value
        ),
        "adapter_id": (
            response.receipt.adapter_id
        ),
        "read_only": (
            response.receipt.read_only
        ),
        "network_access_enabled": (
            response.receipt.network_access_enabled
        ),
        "adapter_called": (
            response.receipt.adapter_called
        ),
        "exchange_called": (
            response.receipt.exchange_called
        ),
        "live_order_submitted": (
            response.receipt.live_order_submitted
        ),
        "funds_moved": (
            response.receipt.funds_moved
        ),
        "portfolio_mutated": (
            response.receipt.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-021 Q Series "
        "Dry-Run Runtime Adapter"
    )
    print(summary)


if __name__ == "__main__":
    main()
