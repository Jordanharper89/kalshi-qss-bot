from __future__ import annotations

from dataclasses import FrozenInstanceError
import json

from qseries_v2.integration.qseries_execution_adapter_contract import (
    AdapterAction,
    AdapterOrderType,
    AdapterRequestStatus,
    AdapterResultStatus,
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterContractError,
    build_execution_adapter_request,
    build_not_executed_result,
    canonical_hash,
    canonical_json,
)


def expect_contract_error(callable_object, expected_text: str) -> None:
    try:
        callable_object()
    except ExecutionAdapterContractError as exc:
        assert expected_text in str(exc), (
            f"expected error containing {expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            f"expected ExecutionAdapterContractError containing "
            f"{expected_text!r}"
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
        "authorized_at": "2026-07-10T15:00:00-05:00",
        "explanation": {
            "gate": "final execution authorization",
            "decision": "all required checks passed",
        },
    }


def build_request():
    return build_execution_adapter_request(
        authorization_record=make_authorization_record(),
        adapter_id="adapter.kalshi.execution",
        account_reference="account-primary",
        market_id="KXTEST-26JUL10",
        action=AdapterAction.BUY,
        order_type=AdapterOrderType.LIMIT,
        quantity="12.000",
        limit_price="0.43",
        price_unit="usd_probability",
        time_in_force="GTC",
        client_order_id="qseries-client-order-001",
        created_at="2026-07-10T15:01:00-05:00",
        expires_at="2026-07-10T15:06:00-05:00",
        rationale=(
            "INT-015 granted final authorization and requires processing "
            "through an approved execution adapter."
        ),
        metadata={
            "strategy_id": "strategy.test",
            "replay_sequence": 16,
            "tags": ["integration", "dry-run"],
        },
    )


def test_canonical_hashing() -> None:
    first = {
        "b": 2,
        "a": {
            "z": "last",
            "y": [3, 2, 1],
        },
    }

    second = {
        "a": {
            "y": [3, 2, 1],
            "z": "last",
        },
        "b": 2,
    }

    assert canonical_json(first) == canonical_json(second)
    assert canonical_hash(first) == canonical_hash(second)


def test_request_contract() -> None:
    request = build_request()

    assert request.schema_version == SCHEMA_VERSION
    assert request.engine_id == ENGINE_ID
    assert request.request_id.startswith("int016-")
    assert request.authorization_id == "final-auth-0001"
    assert len(request.authorization_record_hash) == 64
    assert request.adapter_id == "adapter.kalshi.execution"
    assert request.account_reference == "account-primary"
    assert request.market_id == "KXTEST-26JUL10"
    assert request.action is AdapterAction.BUY
    assert request.order_type is AdapterOrderType.LIMIT
    assert request.quantity == "12"
    assert request.limit_price == "0.43"
    assert request.price_unit == "usd_probability"
    assert request.time_in_force == "gtc"
    assert request.request_status is AdapterRequestStatus.READY_FOR_ADAPTER
    assert request.read_only is True
    assert request.execution_allowed is False
    assert request.requires_concrete_adapter is True
    assert len(request.contract_hash) == 64

    payload = request.to_dict()

    assert payload["schema_version"] == "INT-016"
    assert payload["execution_allowed"] is False
    assert payload["requires_concrete_adapter"] is True
    assert payload["contract_hash"] == request.contract_hash

    decoded = json.loads(request.to_canonical_json())
    assert decoded == payload


def test_determinism() -> None:
    first = build_request()
    second = build_request()

    assert first.request_id == second.request_id
    assert first.contract_hash == second.contract_hash
    assert first.to_dict() == second.to_dict()
    assert first.to_canonical_json() == second.to_canonical_json()


def test_immutability() -> None:
    request = build_request()

    try:
        request.market_id = "MUTATED"
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("request dataclass must be immutable")

    try:
        request.metadata["strategy_id"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("request metadata must be immutable")


def test_not_executed_result() -> None:
    request = build_request()

    result = build_not_executed_result(
        request=request,
        processed_at="2026-07-10T15:01:01-05:00",
        reason_code="contract_only",
        explanation=(
            "INT-016 defines the adapter boundary but contains no live "
            "execution implementation."
        ),
        details={
            "live_order_submitted": False,
            "portfolio_mutated": False,
            "funds_moved": False,
        },
    )

    duplicate = build_not_executed_result(
        request=request,
        processed_at="2026-07-10T15:01:01-05:00",
        reason_code="contract_only",
        explanation=(
            "INT-016 defines the adapter boundary but contains no live "
            "execution implementation."
        ),
        details={
            "live_order_submitted": False,
            "portfolio_mutated": False,
            "funds_moved": False,
        },
    )

    assert result.status is AdapterResultStatus.NOT_EXECUTED
    assert result.executed_quantity == "0"
    assert result.adapter_reference is None
    assert result.average_price is None
    assert result.read_only is True
    assert result.result_id == duplicate.result_id
    assert result.result_hash == duplicate.result_hash
    assert result.to_dict() == duplicate.to_dict()
    assert result.details["live_order_submitted"] is False
    assert result.details["portfolio_mutated"] is False
    assert result.details["funds_moved"] is False


def test_authorization_boundary_rejections() -> None:
    blocked = make_authorization_record()
    blocked["authorization_status"] = "blocked"

    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=blocked,
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="limit",
            quantity="1",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="gtc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "not authorized",
    )

    wrong_schema = make_authorization_record()
    wrong_schema["schema_version"] = "INT-014"

    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=wrong_schema,
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="limit",
            quantity="1",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="gtc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "must be INT-015",
    )

    direct_execution = make_authorization_record()
    direct_execution["execution_allowed"] = True

    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=direct_execution,
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="limit",
            quantity="1",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="gtc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "must not directly allow execution",
    )


def test_timestamp_and_order_validation() -> None:
    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=make_authorization_record(),
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="limit",
            quantity="1",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="gtc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "must include a timezone offset",
    )

    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=make_authorization_record(),
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="market",
            quantity="1",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="ioc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "market orders must not contain limit_price",
    )

    expect_contract_error(
        lambda: build_execution_adapter_request(
            authorization_record=make_authorization_record(),
            adapter_id="adapter.test",
            account_reference="account.test",
            market_id="market.test",
            action="buy",
            order_type="limit",
            quantity="0",
            limit_price="0.50",
            price_unit="probability",
            time_in_force="gtc",
            client_order_id="client-1",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:02:00-05:00",
            rationale="test",
        ),
        "quantity must be greater than zero",
    )


def main() -> None:
    test_canonical_hashing()
    test_request_contract()
    test_determinism()
    test_immutability()
    test_not_executed_result()
    test_authorization_boundary_rejections()
    test_timestamp_and_order_validation()

    request = build_request()

    result = build_not_executed_result(
        request=request,
        processed_at="2026-07-10T15:01:01-05:00",
        reason_code="contract_only",
        explanation=(
            "Execution adapter contract validated without performing "
            "execution."
        ),
        details={
            "live_order_submitted": False,
            "exchange_called": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "request_id": request.request_id,
        "request_status": request.request_status.value,
        "adapter_id": request.adapter_id,
        "result_status": result.status.value,
        "read_only": request.read_only,
        "execution_allowed": request.execution_allowed,
        "requires_concrete_adapter": (
            request.requires_concrete_adapter
        ),
    }

    print("[PASS] INT-016 Q Series Execution Adapter Contract")
    print(summary)


if __name__ == "__main__":
    main()
