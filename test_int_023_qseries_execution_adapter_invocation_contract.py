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
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterInvocationContractError,
    ExecutionInvocationStatus,
    build_execution_adapter_invocation,
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
    except ExecutionAdapterInvocationContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionAdapterInvocationContractError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-023",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-023",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T20:00:00-05:00"
        ),
    }


def make_runtime_invocation(
    *,
    market_id: str = "KXTEST-INT023",
    invocation_expires_at: str = (
        "2026-07-10T20:08:00-05:00"
    ),
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
        quantity="2",
        limit_price="0.47",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int023"
        ),
        created_at=(
            "2026-07-10T20:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T20:10:00-05:00"
        ),
        rationale=(
            "Build INT-023 invocation contract test chain."
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
                "2026-07-10T20:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T20:00:00-05:00"
            ),
            registration_reason=(
                "INT-023 test registration."
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
            "2026-07-10T20:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T20:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T20:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T20:09:00-05:00"
        ),
    )

    return build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T20:00:05-05:00"
        ),
        expires_at=invocation_expires_at,
        invocation_context={
            "environment": "test",
            "adapter_called": False,
            "network_access_enabled": False,
        },
    )


def make_gate_decision(runtime_invocation):
    adapter = QSeriesDryRunRuntimeAdapter(
        adapter_id=(
            "adapter.kalshi.execution"
        ),
        adapter_version="1.0.0-dry-run",
    )

    dry_run_response = adapter.simulate(
        invocation=runtime_invocation,
        simulated_at=(
            "2026-07-10T20:00:06-05:00"
        ),
        simulation_context={
            "environment": "test",
            "network_access_enabled": False,
        },
    )

    return evaluate_runtime_adapter_invocation_gate(
        invocation=runtime_invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T20:00:07-05:00"
        ),
        evidence={
            "environment": "test",
            "execution_adapter_connected": False,
        },
    )


def test_ready_execution_invocation() -> None:
    runtime_invocation = make_runtime_invocation()
    gate_decision = make_gate_decision(
        runtime_invocation
    )

    invocation = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
        execution_context={
            "environment": "test",
            "execution_adapter_connected": False,
            "network_access_enabled": False,
        },
    )

    assert invocation.schema_version == SCHEMA_VERSION
    assert invocation.engine_id == ENGINE_ID
    assert (
        invocation.status
        is ExecutionInvocationStatus.READY_FOR_EXECUTION_ADAPTER
    )
    assert invocation.reason_codes == (
        "execution_adapter_invocation_ready",
    )
    assert (
        invocation.runtime_invocation_id
        == runtime_invocation.invocation_id
    )
    assert (
        invocation.runtime_invocation_hash
        == runtime_invocation.invocation_hash
    )
    assert (
        invocation.gate_id
        == gate_decision.gate_id
    )
    assert (
        invocation.gate_hash
        == gate_decision.gate_hash
    )
    assert (
        invocation.adapter_id
        == runtime_invocation.adapter_id
    )
    assert invocation.read_only is True
    assert invocation.execution_allowed is False
    assert (
        invocation.execution_adapter_call_required
        is True
    )
    assert (
        invocation.execution_adapter_called
        is False
    )
    assert invocation.exchange_called is False
    assert invocation.live_order_submitted is False
    assert invocation.funds_moved is False
    assert invocation.portfolio_mutated is False
    assert len(invocation.invocation_hash) == 64


def test_determinism() -> None:
    runtime_invocation = make_runtime_invocation()
    gate_decision = make_gate_decision(
        runtime_invocation
    )

    first = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
        execution_context={
            "network_access_enabled": False,
            "environment": "test",
        },
    )

    second = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
        execution_context={
            "environment": "test",
            "network_access_enabled": False,
        },
    )

    assert (
        first.execution_invocation_id
        == second.execution_invocation_id
    )
    assert (
        first.invocation_hash
        == second.invocation_hash
    )
    assert (
        first.to_dict()
        == second.to_dict()
    )
    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    runtime_invocation = make_runtime_invocation()
    gate_decision = make_gate_decision(
        runtime_invocation
    )

    invocation = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
    )

    try:
        invocation.status = (
            ExecutionInvocationStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "execution invocation must be immutable"
        )

    try:
        invocation.checks[
            "gate_eligible"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "execution invocation checks must be immutable"
        )


def test_expired_runtime_invocation_blocked() -> None:
    runtime_invocation = make_runtime_invocation(
        invocation_expires_at=(
            "2026-07-10T20:00:08-05:00"
        )
    )

    gate_decision = make_gate_decision(
        runtime_invocation
    )

    invocation = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:09-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
    )

    assert (
        invocation.status
        is ExecutionInvocationStatus.BLOCKED
    )
    assert (
        "runtime_invocation_expired"
        in invocation.reason_codes
    )
    assert invocation.execution_allowed is False
    assert (
        invocation.execution_adapter_called
        is False
    )
    assert invocation.live_order_submitted is False


def test_timestamp_validation() -> None:
    runtime_invocation = make_runtime_invocation()
    gate_decision = make_gate_decision(
        runtime_invocation
    )

    expect_contract_error(
        lambda: build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=gate_decision,
            prepared_at=(
                "2026-07-10T20:00:08"
            ),
            expires_at=(
                "2026-07-10T20:07:00-05:00"
            ),
        ),
        "must include a timezone offset",
    )

    expect_contract_error(
        lambda: build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=gate_decision,
            prepared_at=(
                "2026-07-10T20:07:00-05:00"
            ),
            expires_at=(
                "2026-07-10T20:00:08-05:00"
            ),
        ),
        "expires_at must be later",
    )


def main() -> None:
    test_ready_execution_invocation()
    test_determinism()
    test_immutability()
    test_expired_runtime_invocation_blocked()
    test_timestamp_validation()

    runtime_invocation = make_runtime_invocation()

    gate_decision = make_gate_decision(
        runtime_invocation
    )

    invocation = build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T20:00:08-05:00"
        ),
        expires_at=(
            "2026-07-10T20:07:00-05:00"
        ),
        execution_context={
            "environment": "test",
            "execution_adapter_connected": False,
            "network_access_enabled": False,
            "execution_adapter_called": False,
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
        "adapter_id": invocation.adapter_id,
        "reason_codes": list(
            invocation.reason_codes
        ),
        "read_only": invocation.read_only,
        "execution_allowed": (
            invocation.execution_allowed
        ),
        "execution_adapter_call_required": (
            invocation.execution_adapter_call_required
        ),
        "execution_adapter_called": (
            invocation.execution_adapter_called
        ),
        "exchange_called": (
            invocation.exchange_called
        ),
        "live_order_submitted": (
            invocation.live_order_submitted
        ),
        "funds_moved": (
            invocation.funds_moved
        ),
        "portfolio_mutated": (
            invocation.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-023 Q Series "
        "Execution Adapter Invocation Contract"
    )
    print(summary)


if __name__ == "__main__":
    main()
