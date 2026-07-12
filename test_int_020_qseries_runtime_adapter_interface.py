from __future__ import annotations

from dataclasses import FrozenInstanceError

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
    ENGINE_ID,
    SCHEMA_VERSION,
    RuntimeAdapterInterfaceError,
    RuntimeInvocationStatus,
    RuntimeResultStatus,
    build_not_invoked_runtime_result,
    build_runtime_adapter_invocation,
)


def expect_interface_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except RuntimeAdapterInterfaceError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected RuntimeAdapterInterfaceError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-020",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-020",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T17:00:00-05:00"
        ),
    }


def make_chain(
    *,
    market_id: str = "KXTEST-INT020",
):
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
        market_id=market_id,
        action="buy",
        order_type="limit",
        quantity="4",
        limit_price="0.44",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int020"
        ),
        created_at=(
            "2026-07-10T17:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T17:10:00-05:00"
        ),
        rationale=(
            "Build INT-020 runtime interface test chain."
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
                "2026-07-10T17:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T17:00:00-05:00"
            ),
            registration_reason=(
                "INT-020 test registration."
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
            "2026-07-10T17:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T17:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T17:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T17:09:00-05:00"
        ),
        runtime_context={
            "environment": "test",
            "adapter_invoked": False,
            "network_access_enabled": False,
        },
    )

    return dispatch


def test_ready_invocation() -> None:
    dispatch = make_chain()

    invocation = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
        invocation_context={
            "environment": "test",
            "network_access_enabled": False,
            "adapter_called": False,
        },
    )

    assert invocation.schema_version == SCHEMA_VERSION
    assert invocation.engine_id == ENGINE_ID
    assert (
        invocation.status
        is RuntimeInvocationStatus.READY
    )
    assert invocation.reason_codes == (
        "runtime_invocation_ready",
    )
    assert (
        invocation.dispatch_id
        == dispatch.dispatch_id
    )
    assert (
        invocation.dispatch_hash
        == dispatch.dispatch_hash
    )
    assert (
        invocation.request_id
        == dispatch.request_id
    )
    assert (
        invocation.adapter_id
        == dispatch.adapter_id
    )
    assert invocation.read_only is True
    assert invocation.execution_allowed is False
    assert invocation.adapter_call_required is True
    assert invocation.adapter_called is False
    assert len(invocation.invocation_hash) == 64


def test_not_invoked_result() -> None:
    dispatch = make_chain()

    invocation = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
    )

    result = build_not_invoked_runtime_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T17:00:06-05:00"
        ),
        reason_code=(
            "interface_contract_only"
        ),
        explanation=(
            "INT-020 validated the runtime adapter interface "
            "without invoking an adapter."
        ),
        details={
            "adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    assert (
        result.status
        is RuntimeResultStatus.NOT_INVOKED
    )
    assert (
        result.invocation_id
        == invocation.invocation_id
    )
    assert (
        result.invocation_hash
        == invocation.invocation_hash
    )
    assert result.adapter_reference is None
    assert result.read_only is True
    assert result.live_order_submitted is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False
    assert len(result.result_hash) == 64


def test_determinism() -> None:
    dispatch = make_chain()

    first = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
        invocation_context={
            "adapter_called": False,
            "network_access_enabled": False,
        },
    )

    second = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
        invocation_context={
            "network_access_enabled": False,
            "adapter_called": False,
        },
    )

    assert first.invocation_id == second.invocation_id
    assert (
        first.invocation_hash
        == second.invocation_hash
    )
    assert first.to_dict() == second.to_dict()
    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    dispatch = make_chain()

    invocation = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
    )

    try:
        invocation.status = (
            RuntimeInvocationStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "invocation must be immutable"
        )

    try:
        invocation.checks[
            "dispatch_ready"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "invocation checks must be immutable"
        )


def test_blocked_dispatch() -> None:
    dispatch = make_chain(
        market_id="UNSUPPORTED-INT020"
    )

    invocation = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
    )

    assert (
        invocation.status
        is RuntimeInvocationStatus.BLOCKED
    )
    assert (
        "dispatch_not_ready"
        in invocation.reason_codes
    )
    assert invocation.execution_allowed is False
    assert invocation.adapter_called is False


def test_timestamp_validation() -> None:
    dispatch = make_chain()

    expect_interface_error(
        lambda: build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T17:00:05"
            ),
            expires_at=(
                "2026-07-10T17:08:00-05:00"
            ),
        ),
        "must include a timezone offset",
    )

    expect_interface_error(
        lambda: build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T17:08:00-05:00"
            ),
            expires_at=(
                "2026-07-10T17:00:05-05:00"
            ),
        ),
        "expires_at must be later",
    )


def main() -> None:
    test_ready_invocation()
    test_not_invoked_result()
    test_determinism()
    test_immutability()
    test_blocked_dispatch()
    test_timestamp_validation()

    dispatch = make_chain()

    invocation = build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T17:00:05-05:00"
        ),
        expires_at=(
            "2026-07-10T17:08:00-05:00"
        ),
        invocation_context={
            "environment": "test",
            "network_access_enabled": False,
            "adapter_called": False,
        },
    )

    result = build_not_invoked_runtime_result(
        invocation=invocation,
        completed_at=(
            "2026-07-10T17:00:06-05:00"
        ),
        reason_code=(
            "interface_contract_only"
        ),
        explanation=(
            "Runtime adapter interface validated "
            "without invocation."
        ),
        details={
            "adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "invocation_status": (
            invocation.status.value
        ),
        "result_status": (
            result.status.value
        ),
        "adapter_id": invocation.adapter_id,
        "read_only": invocation.read_only,
        "execution_allowed": (
            invocation.execution_allowed
        ),
        "adapter_call_required": (
            invocation.adapter_call_required
        ),
        "adapter_called": (
            invocation.adapter_called
        ),
        "live_order_submitted": (
            result.live_order_submitted
        ),
        "funds_moved": result.funds_moved,
        "portfolio_mutated": (
            result.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-020 Q Series "
        "Runtime Adapter Interface"
    )
    print(summary)


if __name__ == "__main__":
    main()
