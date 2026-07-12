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
    ENGINE_ID,
    SCHEMA_VERSION,
    RuntimeAdapterDispatchError,
    RuntimeDispatchStatus,
    build_runtime_adapter_dispatch,
)


def expect_dispatch_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except RuntimeAdapterDispatchError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected RuntimeAdapterDispatchError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-0001",
        "authorization_status": "authorized",
        "opportunity_id": "opp-001",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T15:00:00-05:00"
        ),
    }


def make_request(
    *,
    market_id: str = "KXTEST-26JUL10",
):
    return build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        account_reference=(
            "account-primary"
        ),
        market_id=market_id,
        action="buy",
        order_type="limit",
        quantity="12",
        limit_price="0.43",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-001"
        ),
        created_at=(
            "2026-07-10T15:01:00-05:00"
        ),
        expires_at=(
            "2026-07-10T15:06:00-05:00"
        ),
        rationale=(
            "Authorized INT-015 adapter request."
        ),
        metadata={
            "strategy_id": "strategy.test",
        },
    )


def make_registry():
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
                "kxbtc",
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
                "2026-07-10T15:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T15:00:00-05:00"
            ),
            registration_reason=(
                "Canonical test adapter registration."
            ),
            metadata={
                "environment": "test",
                "live_execution_enabled": False,
            },
        )
    )

    return ExecutionAdapterRegistry(
        [registration]
    )


def make_chain(
    *,
    market_id: str = "KXTEST-26JUL10",
):
    request = make_request(
        market_id=market_id
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=make_registry(),
        validated_at=(
            "2026-07-10T15:01:01-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T15:01:02-05:00"
        ),
        evidence={
            "runtime_adapter_connected": False,
            "live_order_submitted": False,
        },
    )

    return request, validation, admission


def test_ready_dispatch_contract() -> None:
    request, validation, admission = make_chain()

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
        runtime_context={
            "environment": "test",
            "network_access_enabled": False,
            "adapter_invoked": False,
        },
    )

    assert dispatch.schema_version == SCHEMA_VERSION
    assert dispatch.engine_id == ENGINE_ID
    assert (
        dispatch.status
        is RuntimeDispatchStatus.READY_FOR_RUNTIME
    )
    assert dispatch.reason_codes == (
        "runtime_dispatch_ready",
    )
    assert (
        dispatch.request_id
        == request.request_id
    )
    assert (
        dispatch.validation_id
        == validation.validation_id
    )
    assert (
        dispatch.admission_id
        == admission.admission_id
    )
    assert (
        dispatch.request_contract_hash
        == request.contract_hash
    )
    assert (
        dispatch.validation_hash
        == validation.validation_hash
    )
    assert (
        dispatch.admission_hash
        == admission.admission_hash
    )
    assert dispatch.read_only is True
    assert dispatch.execution_allowed is False
    assert (
        dispatch.adapter_invocation_required
        is True
    )
    assert dispatch.live_order_submitted is False
    assert len(dispatch.dispatch_hash) == 64
    assert (
        dispatch.runtime_context[
            "adapter_invoked"
        ]
        is False
    )


def test_determinism() -> None:
    request, validation, admission = make_chain()

    first = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
        runtime_context={
            "network_access_enabled": False,
            "adapter_invoked": False,
        },
    )

    second = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
        runtime_context={
            "adapter_invoked": False,
            "network_access_enabled": False,
        },
    )

    assert first.dispatch_id == second.dispatch_id
    assert first.dispatch_hash == second.dispatch_hash
    assert first.to_dict() == second.to_dict()
    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    request, validation, admission = make_chain()

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
    )

    try:
        dispatch.status = (
            RuntimeDispatchStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "dispatch dataclass must be immutable"
        )

    try:
        dispatch.checks[
            "adapter_id_match"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "dispatch checks must be immutable"
        )


def test_blocked_admission_produces_blocked_dispatch() -> None:
    request, validation, admission = make_chain(
        market_id="UNSUPPORTED-001"
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
    )

    assert (
        dispatch.status
        is RuntimeDispatchStatus.BLOCKED
    )
    assert (
        "validation_not_approved"
        in dispatch.reason_codes
    )
    assert (
        "admission_not_approved"
        in dispatch.reason_codes
    )
    assert dispatch.execution_allowed is False


def test_mismatched_chain_blocked() -> None:
    first_request, first_validation, first_admission = (
        make_chain()
    )

    second_request, _, _ = make_chain(
        market_id="KXTEST-26JUL11"
    )

    dispatch = build_runtime_adapter_dispatch(
        request=second_request,
        validation=first_validation,
        admission=first_admission,
        dispatched_at=(
            "2026-07-10T15:02:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:06:00-05:00"
        ),
    )

    assert (
        dispatch.status
        is RuntimeDispatchStatus.BLOCKED
    )
    assert (
        "request_validation_mismatch"
        in dispatch.reason_codes
    )
    assert (
        "request_admission_mismatch"
        in dispatch.reason_codes
    )
    assert (
        "request_hash_mismatch"
        in dispatch.reason_codes
    )


def test_timestamp_validation() -> None:
    request, validation, admission = make_chain()

    expect_dispatch_error(
        lambda: build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T15:01:03"
            ),
            expires_at=(
                "2026-07-10T15:05:00-05:00"
            ),
        ),
        "must include a timezone offset",
    )

    expect_dispatch_error(
        lambda: build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T15:05:00-05:00"
            ),
            expires_at=(
                "2026-07-10T15:01:03-05:00"
            ),
        ),
        "expires_at must be later",
    )


def main() -> None:
    test_ready_dispatch_contract()
    test_determinism()
    test_immutability()
    test_blocked_admission_produces_blocked_dispatch()
    test_mismatched_chain_blocked()
    test_timestamp_validation()

    request, validation, admission = make_chain()

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T15:01:03-05:00"
        ),
        expires_at=(
            "2026-07-10T15:05:00-05:00"
        ),
        runtime_context={
            "environment": "test",
            "network_access_enabled": False,
            "adapter_invoked": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "dispatch_status": (
            dispatch.status.value
        ),
        "adapter_id": dispatch.adapter_id,
        "reason_codes": list(
            dispatch.reason_codes
        ),
        "read_only": dispatch.read_only,
        "execution_allowed": (
            dispatch.execution_allowed
        ),
        "adapter_invocation_required": (
            dispatch.adapter_invocation_required
        ),
        "live_order_submitted": (
            dispatch.live_order_submitted
        ),
    }

    print(
        "[PASS] INT-019 Q Series "
        "Runtime Adapter Dispatch Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
