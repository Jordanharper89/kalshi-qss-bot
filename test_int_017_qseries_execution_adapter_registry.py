from __future__ import annotations

from dataclasses import FrozenInstanceError

from qseries_v2.integration.qseries_execution_adapter_contract import (
    build_execution_adapter_request,
)
from qseries_v2.integration.qseries_execution_adapter_registry import (
    AdapterLifecycleStatus,
    AdapterValidationStatus,
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterRegistry,
    ExecutionAdapterRegistryError,
    build_execution_adapter_registration,
    validate_execution_adapter_request,
)


def expect_registry_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionAdapterRegistryError as exc:
        assert expected_text in str(exc), (
            f"expected error containing {expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected ExecutionAdapterRegistryError containing "
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
    }


def make_request(
    *,
    adapter_id: str = "adapter.kalshi.execution",
    market_id: str = "KXTEST-26JUL10",
    action: str = "buy",
    order_type: str = "limit",
    price_unit: str | None = "usd_probability",
    limit_price: str | None = "0.43",
):
    return build_execution_adapter_request(
        authorization_record=make_authorization_record(),
        adapter_id=adapter_id,
        account_reference="account-primary",
        market_id=market_id,
        action=action,
        order_type=order_type,
        quantity="12",
        limit_price=limit_price,
        price_unit=price_unit,
        time_in_force="gtc",
        client_order_id="client-order-001",
        created_at="2026-07-10T15:01:00-05:00",
        expires_at="2026-07-10T15:06:00-05:00",
        rationale="Authorized INT-015 adapter request.",
        metadata={"strategy_id": "strategy.test"},
    )


def make_registration(
    *,
    adapter_id: str = "adapter.kalshi.execution",
    lifecycle_status: str = "registered",
):
    return build_execution_adapter_registration(
        adapter_id=adapter_id,
        adapter_name="Kalshi Execution Adapter",
        adapter_version="1.0.0",
        venue_id="kalshi",
        supported_market_prefixes=[
            "kxtest",
            "kxbtc",
            "kxeth",
        ],
        supported_actions=["buy", "sell"],
        supported_order_types=["limit", "market"],
        supported_price_units=["usd_probability"],
        lifecycle_status=lifecycle_status,
        registered_at="2026-07-10T15:00:00-05:00",
        effective_at="2026-07-10T15:00:00-05:00",
        registration_reason=(
            "Register the canonical test execution adapter identity."
        ),
        metadata={
            "environment": "test",
            "live_execution_enabled": False,
        },
    )


def test_registration_contract() -> None:
    registration = make_registration()

    assert registration.schema_version == SCHEMA_VERSION
    assert registration.engine_id == ENGINE_ID
    assert registration.adapter_id == "adapter.kalshi.execution"
    assert registration.venue_id == "kalshi"
    assert registration.lifecycle_status is (
        AdapterLifecycleStatus.REGISTERED
    )
    assert registration.supported_market_prefixes == (
        "kxbtc",
        "kxeth",
        "kxtest",
    )
    assert registration.read_only is True
    assert registration.execution_allowed is False
    assert registration.requires_runtime_adapter is True
    assert len(registration.registration_hash) == 64
    assert (
        registration.metadata["live_execution_enabled"]
        is False
    )


def test_registration_immutability() -> None:
    registration = make_registration()

    try:
        registration.adapter_id = "mutated"
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError(
            "registration dataclass must be immutable"
        )

    try:
        registration.metadata["environment"] = "live"
    except TypeError:
        pass
    else:
        raise AssertionError(
            "registration metadata must be immutable"
        )


def test_registry_determinism() -> None:
    first_registration = make_registration()
    second_registration = build_execution_adapter_registration(
        adapter_id="adapter.secondary.execution",
        adapter_name="Secondary Test Adapter",
        adapter_version="1.0.0",
        venue_id="secondary",
        supported_market_prefixes=["sec"],
        supported_actions=["sell"],
        supported_order_types=["limit"],
        supported_price_units=["usd_probability"],
        lifecycle_status="registered",
        registered_at="2026-07-10T15:00:00-05:00",
        effective_at="2026-07-10T15:00:00-05:00",
        registration_reason="Secondary deterministic test adapter.",
    )

    registry_one = ExecutionAdapterRegistry(
        [first_registration, second_registration]
    )
    registry_two = ExecutionAdapterRegistry(
        [second_registration, first_registration]
    )

    assert registry_one.adapter_count == 2
    assert registry_one.registry_hash == registry_two.registry_hash
    assert registry_one.to_dict() == registry_two.to_dict()


def test_approved_validation() -> None:
    request = make_request()
    registry = ExecutionAdapterRegistry(
        [make_registration()]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    duplicate = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    assert validation.status is AdapterValidationStatus.APPROVED
    assert validation.reason_codes == (
        "adapter_capabilities_verified",
    )
    assert validation.checks["adapter_registered"] is True
    assert validation.checks["adapter_active"] is True
    assert validation.checks["market_supported"] is True
    assert validation.checks["action_supported"] is True
    assert validation.checks["order_type_supported"] is True
    assert validation.checks["price_unit_supported"] is True
    assert (
        validation.checks["request_non_executing_contract"]
        is True
    )
    assert validation.read_only is True
    assert validation.execution_allowed is False
    assert validation.runtime_processing_required is True
    assert validation.validation_id == duplicate.validation_id
    assert validation.validation_hash == duplicate.validation_hash
    assert validation.to_dict() == duplicate.to_dict()


def test_unknown_adapter_blocked() -> None:
    request = make_request(
        adapter_id="adapter.unknown.execution"
    )
    registry = ExecutionAdapterRegistry(
        [make_registration()]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    assert validation.status is AdapterValidationStatus.BLOCKED
    assert "adapter_not_registered" in validation.reason_codes
    assert validation.registration_hash is None
    assert validation.execution_allowed is False


def test_capability_mismatch_blocked() -> None:
    request = make_request(
        market_id="UNSUPPORTED-001"
    )
    registry = ExecutionAdapterRegistry(
        [make_registration()]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    assert validation.status is AdapterValidationStatus.BLOCKED
    assert "market_not_supported" in validation.reason_codes
    assert validation.checks["market_supported"] is False


def test_suspended_adapter_blocked() -> None:
    request = make_request()
    registry = ExecutionAdapterRegistry(
        [
            make_registration(
                lifecycle_status="suspended"
            )
        ]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    assert validation.status is AdapterValidationStatus.BLOCKED
    assert "adapter_not_active" in validation.reason_codes
    assert validation.checks["adapter_active"] is False


def test_duplicate_registration_rejected() -> None:
    registration = make_registration()

    expect_registry_error(
        lambda: ExecutionAdapterRegistry(
            [registration, registration]
        ),
        "duplicate adapter_id",
    )


def test_caller_supplied_timestamp_required() -> None:
    request = make_request()
    registry = ExecutionAdapterRegistry(
        [make_registration()]
    )

    expect_registry_error(
        lambda: validate_execution_adapter_request(
            request=request,
            registry=registry,
            validated_at="2026-07-10T15:01:01",
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_registration_contract()
    test_registration_immutability()
    test_registry_determinism()
    test_approved_validation()
    test_unknown_adapter_blocked()
    test_capability_mismatch_blocked()
    test_suspended_adapter_blocked()
    test_duplicate_registration_rejected()
    test_caller_supplied_timestamp_required()

    request = make_request()
    registration = make_registration()
    registry = ExecutionAdapterRegistry([registration])

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T15:01:01-05:00",
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "adapter_count": registry.adapter_count,
        "adapter_id": validation.adapter_id,
        "validation_status": validation.status.value,
        "reason_codes": list(validation.reason_codes),
        "read_only": validation.read_only,
        "execution_allowed": validation.execution_allowed,
        "runtime_processing_required": (
            validation.runtime_processing_required
        ),
    }

    print("[PASS] INT-017 Q Series Execution Adapter Registry")
    print(summary)


if __name__ == "__main__":
    main()
