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
from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterSafetyGateError,
    ExecutionAdapterSafetyStatus,
    evaluate_execution_adapter_safety,
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


def expect_safety_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionAdapterSafetyGateError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionAdapterSafetyGateError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-024",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-024",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": (
            "2026-07-10T21:00:00-05:00"
        ),
    }


def make_execution_invocation(
    *,
    execution_expires_at: str = (
        "2026-07-10T21:07:30-05:00"
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
        market_id="KXTEST-INT024",
        action="buy",
        order_type="limit",
        quantity="2",
        limit_price="0.48",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id=(
            "client-order-int024"
        ),
        created_at=(
            "2026-07-10T21:00:01-05:00"
        ),
        expires_at=(
            "2026-07-10T21:10:00-05:00"
        ),
        rationale=(
            "Build INT-024 safety gate test chain."
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
                "2026-07-10T21:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T21:00:00-05:00"
            ),
            registration_reason=(
                "INT-024 test registration."
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
            "2026-07-10T21:00:02-05:00"
        ),
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T21:00:03-05:00"
        ),
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at=(
            "2026-07-10T21:00:04-05:00"
        ),
        expires_at=(
            "2026-07-10T21:09:00-05:00"
        ),
    )

    runtime_invocation = (
        build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T21:00:05-05:00"
            ),
            expires_at=(
                "2026-07-10T21:08:00-05:00"
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
            "2026-07-10T21:00:06-05:00"
        ),
    )

    gate_decision = (
        evaluate_runtime_adapter_invocation_gate(
            invocation=runtime_invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T21:00:07-05:00"
            ),
        )
    )

    return build_execution_adapter_invocation(
        runtime_invocation=runtime_invocation,
        gate_decision=gate_decision,
        prepared_at=(
            "2026-07-10T21:00:08-05:00"
        ),
        expires_at=execution_expires_at,
        execution_context={
            "environment": "test",
            "network_access_enabled": False,
            "execution_adapter_called": False,
        },
    )


def valid_safety_evidence() -> dict:
    return {
        "environment": "test",
        "network_access_enabled": False,
        "execution_adapter_called": False,
        "exchange_called": False,
        "live_order_submitted": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }


def test_safety_verified() -> None:
    invocation = make_execution_invocation()

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence=valid_safety_evidence(),
    )

    assert decision.schema_version == SCHEMA_VERSION
    assert decision.engine_id == ENGINE_ID

    assert (
        decision.status
        is ExecutionAdapterSafetyStatus.SAFETY_VERIFIED
    )

    assert decision.reason_codes == (
        "execution_adapter_safety_verified",
    )

    assert (
        decision.execution_invocation_id
        == invocation.execution_invocation_id
    )

    assert (
        decision.execution_invocation_hash
        == invocation.invocation_hash
    )

    assert (
        decision.adapter_id
        == invocation.adapter_id
    )

    assert decision.read_only is True
    assert decision.execution_allowed is False

    assert (
        decision.concrete_adapter_required
        is True
    )

    assert (
        decision.execution_adapter_called
        is False
    )

    assert decision.exchange_called is False

    assert (
        decision.live_order_submitted
        is False
    )

    assert decision.funds_moved is False

    assert (
        decision.portfolio_mutated
        is False
    )

    assert len(decision.safety_hash) == 64


def test_determinism() -> None:
    invocation = make_execution_invocation()

    first = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence={
            "portfolio_mutated": False,
            "funds_moved": False,
            "live_order_submitted": False,
            "exchange_called": False,
            "execution_adapter_called": False,
            "network_access_enabled": False,
            "environment": "test",
        },
    )

    second = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence=valid_safety_evidence(),
    )

    assert (
        first.safety_decision_id
        == second.safety_decision_id
    )

    assert (
        first.safety_hash
        == second.safety_hash
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
    invocation = make_execution_invocation()

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence=valid_safety_evidence(),
    )

    try:
        decision.status = (
            ExecutionAdapterSafetyStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "safety decision must be immutable"
        )

    try:
        decision.checks[
            "invocation_ready"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "safety checks must be immutable"
        )

    try:
        decision.safety_evidence[
            "network_access_enabled"
        ] = True
    except TypeError:
        pass
    else:
        raise AssertionError(
            "safety evidence must be immutable"
        )


def test_invalid_safety_evidence_blocked() -> None:
    invocation = make_execution_invocation()

    unsafe_evidence = valid_safety_evidence()
    unsafe_evidence[
        "network_access_enabled"
    ] = True
    unsafe_evidence[
        "exchange_called"
    ] = True

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence=unsafe_evidence,
    )

    assert (
        decision.status
        is ExecutionAdapterSafetyStatus.BLOCKED
    )

    assert (
        "network_safety_evidence_invalid"
        in decision.reason_codes
    )

    assert (
        "exchange_call_safety_evidence_invalid"
        in decision.reason_codes
    )

    assert decision.execution_allowed is False

    assert (
        decision.execution_adapter_called
        is False
    )

    assert (
        decision.live_order_submitted
        is False
    )


def test_missing_safety_evidence_blocked() -> None:
    invocation = make_execution_invocation()

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence={
            "environment": "test",
        },
    )

    assert (
        decision.status
        is ExecutionAdapterSafetyStatus.BLOCKED
    )

    assert (
        "network_safety_evidence_invalid"
        in decision.reason_codes
    )

    assert (
        "adapter_call_safety_evidence_invalid"
        in decision.reason_codes
    )

    assert (
        "order_submission_safety_evidence_invalid"
        in decision.reason_codes
    )


def test_expired_invocation_blocked() -> None:
    invocation = make_execution_invocation(
        execution_expires_at=(
            "2026-07-10T21:00:09-05:00"
        )
    )

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:10-05:00"
        ),
        safety_evidence=valid_safety_evidence(),
    )

    assert (
        decision.status
        is ExecutionAdapterSafetyStatus.BLOCKED
    )

    assert (
        "execution_invocation_expired"
        in decision.reason_codes
    )

    assert decision.execution_allowed is False


def test_timestamp_required() -> None:
    invocation = make_execution_invocation()

    expect_safety_error(
        lambda: evaluate_execution_adapter_safety(
            invocation=invocation,
            evaluated_at=(
                "2026-07-10T21:00:09"
            ),
            safety_evidence=(
                valid_safety_evidence()
            ),
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_safety_verified()
    test_determinism()
    test_immutability()
    test_invalid_safety_evidence_blocked()
    test_missing_safety_evidence_blocked()
    test_expired_invocation_blocked()
    test_timestamp_required()

    invocation = make_execution_invocation()

    decision = evaluate_execution_adapter_safety(
        invocation=invocation,
        evaluated_at=(
            "2026-07-10T21:00:09-05:00"
        ),
        safety_evidence=valid_safety_evidence(),
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "safety_status": (
            decision.status.value
        ),
        "adapter_id": decision.adapter_id,
        "reason_codes": list(
            decision.reason_codes
        ),
        "read_only": decision.read_only,
        "execution_allowed": (
            decision.execution_allowed
        ),
        "concrete_adapter_required": (
            decision.concrete_adapter_required
        ),
        "execution_adapter_called": (
            decision.execution_adapter_called
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
        "[PASS] INT-024 Q Series "
        "Execution Adapter Safety Gate"
    )
    print(summary)


if __name__ == "__main__":
    main()
