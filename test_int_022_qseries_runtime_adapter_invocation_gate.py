from __future__ import annotations

from dataclasses import FrozenInstanceError

from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
    DryRunDecision,
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
from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    RuntimeAdapterInvocationGateError,
    RuntimeInvocationGateStatus,
    evaluate_runtime_adapter_invocation_gate,
)


def expect_gate_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except RuntimeAdapterInvocationGateError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected RuntimeAdapterInvocationGateError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-022",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-022",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T19:00:00-05:00"
        ),
    }


def make_invocation(
    *,
    market_id: str = "KXTEST-INT022",
    invocation_expires_at: str = (
        "2026-07-10T19:08:00-05:00"
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
        limit_price="0.46",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int022"
        ),
        created_at=(
            "2026-07-10T19:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T19:10:00-05:00"
        ),
        rationale=(
            "Build INT-022 invocation gate test chain."
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
                "2026-07-10T19:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T19:00:00-05:00"
            ),
            registration_reason=(
                "INT-022 test registration."
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
            "2026-07-10T19:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T19:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T19:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T19:09:00-05:00"
        ),
    )

    return build_runtime_adapter_invocation(
        dispatch=dispatch,
        prepared_at=(
            "2026-07-10T19:00:05-05:00"
        ),
        expires_at=invocation_expires_at,
        invocation_context={
            "environment": "test",
            "adapter_called": False,
            "network_access_enabled": False,
        },
    )


def make_dry_run_response(
    invocation,
    *,
    adapter_id: str = "adapter.kalshi.execution",
    simulated_at: str = (
        "2026-07-10T19:00:06-05:00"
    ),
):
    adapter = QSeriesDryRunRuntimeAdapter(
        adapter_id=adapter_id,
        adapter_version="1.0.0-dry-run",
    )

    return adapter.simulate(
        invocation=invocation,
        simulated_at=simulated_at,
        simulation_context={
            "environment": "test",
            "network_access_enabled": False,
        },
    )


def test_eligible_gate_decision() -> None:
    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation
    )

    decision = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
        evidence={
            "environment": "test",
            "execution_adapter_connected": False,
            "network_access_enabled": False,
        },
    )

    assert decision.schema_version == SCHEMA_VERSION
    assert decision.engine_id == ENGINE_ID
    assert (
        decision.status
        is RuntimeInvocationGateStatus.ELIGIBLE
    )
    assert decision.reason_codes == (
        "runtime_invocation_eligible",
    )
    assert (
        decision.invocation_id
        == invocation.invocation_id
    )
    assert (
        decision.invocation_hash
        == invocation.invocation_hash
    )
    assert (
        decision.dry_run_receipt_id
        == dry_run_response.receipt.receipt_id
    )
    assert (
        decision.dry_run_receipt_hash
        == dry_run_response.receipt.receipt_hash
    )
    assert (
        decision.dry_run_result_id
        == dry_run_response.result.result_id
    )
    assert (
        decision.dry_run_result_hash
        == dry_run_response.result.result_hash
    )
    assert (
        decision.adapter_id
        == invocation.adapter_id
    )
    assert decision.read_only is True
    assert decision.execution_allowed is False
    assert (
        decision.execution_adapter_required
        is True
    )
    assert decision.adapter_invoked is False
    assert decision.exchange_called is False
    assert decision.live_order_submitted is False
    assert decision.funds_moved is False
    assert decision.portfolio_mutated is False
    assert len(decision.gate_hash) == 64


def test_determinism() -> None:
    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation
    )

    first = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
        evidence={
            "network_access_enabled": False,
            "environment": "test",
        },
    )

    second = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
        evidence={
            "environment": "test",
            "network_access_enabled": False,
        },
    )

    assert first.gate_id == second.gate_id
    assert first.gate_hash == second.gate_hash
    assert first.to_dict() == second.to_dict()
    assert (
        first.to_canonical_json()
        == second.to_canonical_json()
    )


def test_immutability() -> None:
    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation
    )

    decision = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
    )

    try:
        decision.status = (
            RuntimeInvocationGateStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "gate decision must be immutable"
        )

    try:
        decision.checks[
            "invocation_ready"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "gate checks must be immutable"
        )


def test_blocked_dry_run_evidence() -> None:
    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation,
        adapter_id="adapter.other.execution",
    )

    assert (
        dry_run_response.receipt.decision
        is DryRunDecision.BLOCKED
    )
    assert (
        dry_run_response.result.status
        is RuntimeResultStatus.REJECTED
    )

    decision = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
    )

    assert (
        decision.status
        is RuntimeInvocationGateStatus.BLOCKED
    )
    assert (
        "dry_run_not_simulated"
        in decision.reason_codes
    )
    assert (
        "dry_run_result_invalid"
        in decision.reason_codes
    )
    assert (
        "adapter_identity_mismatch"
        in decision.reason_codes
    )
    assert decision.execution_allowed is False


def test_expired_invocation_blocked() -> None:
    invocation = make_invocation(
        invocation_expires_at=(
            "2026-07-10T19:00:07-05:00"
        )
    )

    dry_run_response = make_dry_run_response(
        invocation,
        simulated_at=(
            "2026-07-10T19:00:06-05:00"
        ),
    )

    decision = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:08-05:00"
        ),
    )

    assert (
        decision.status
        is RuntimeInvocationGateStatus.BLOCKED
    )
    assert (
        "invocation_expired"
        in decision.reason_codes
    )
    assert decision.adapter_invoked is False
    assert decision.live_order_submitted is False


def test_timestamp_required() -> None:
    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation
    )

    expect_gate_error(
        lambda: evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07"
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_eligible_gate_decision()
    test_determinism()
    test_immutability()
    test_blocked_dry_run_evidence()
    test_expired_invocation_blocked()
    test_timestamp_required()

    invocation = make_invocation()

    dry_run_response = make_dry_run_response(
        invocation
    )

    decision = evaluate_runtime_adapter_invocation_gate(
        invocation=invocation,
        dry_run_response=dry_run_response,
        evaluated_at=(
            "2026-07-10T19:00:07-05:00"
        ),
        evidence={
            "environment": "test",
            "execution_adapter_connected": False,
            "network_access_enabled": False,
            "adapter_invoked": False,
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
        "gate_status": decision.status.value,
        "adapter_id": decision.adapter_id,
        "reason_codes": list(
            decision.reason_codes
        ),
        "read_only": decision.read_only,
        "execution_allowed": (
            decision.execution_allowed
        ),
        "execution_adapter_required": (
            decision.execution_adapter_required
        ),
        "adapter_invoked": (
            decision.adapter_invoked
        ),
        "exchange_called": (
            decision.exchange_called
        ),
        "live_order_submitted": (
            decision.live_order_submitted
        ),
        "funds_moved": (
            decision.funds_moved
        ),
        "portfolio_mutated": (
            decision.portfolio_mutated
        ),
    }

    print(
        "[PASS] INT-022 Q Series "
        "Runtime Adapter Invocation Gate"
    )
    print(summary)


if __name__ == "__main__":
    main()
