from __future__ import annotations

from dataclasses import FrozenInstanceError

from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
    AdapterAdmissionStatus,
    ENGINE_ID,
    SCHEMA_VERSION,
    ExecutionAdapterAdmissionError,
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


def expect_admission_error(
    callable_object,
    expected_text: str,
) -> None:
    try:
        callable_object()
    except ExecutionAdapterAdmissionError as exc:
        assert expected_text in str(exc), (
            f"expected error containing "
            f"{expected_text!r}, got {exc!r}"
        )
    else:
        raise AssertionError(
            "expected "
            "ExecutionAdapterAdmissionError "
            f"containing {expected_text!r}"
        )


def make_authorization_record() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": (
            "final-auth-0001"
        ),
        "authorization_status": (
            "authorized"
        ),
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
    adapter_id: str = (
        "adapter.kalshi.execution"
    ),
    market_id: str = (
        "KXTEST-26JUL10"
    ),
):
    return build_execution_adapter_request(
        authorization_record=(
            make_authorization_record()
        ),
        adapter_id=adapter_id,
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
            "strategy_id": (
                "strategy.test"
            ),
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
            lifecycle_status=(
                "registered"
            ),
            registered_at=(
                "2026-07-10T15:00:00-05:00"
            ),
            effective_at=(
                "2026-07-10T15:00:00-05:00"
            ),
            registration_reason=(
                "Canonical test adapter "
                "registration."
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


def make_validation(request):
    return validate_execution_adapter_request(
        request=request,
        registry=make_registry(),
        validated_at=(
            "2026-07-10T15:01:01-05:00"
        ),
    )


def test_admitted_contract() -> None:
    request = make_request()
    validation = make_validation(request)

    admission = (
        evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
            evidence={
                "runtime_adapter_connected": False,
                "live_order_submitted": False,
                "portfolio_mutated": False,
            },
        )
    )

    assert (
        admission.schema_version
        == SCHEMA_VERSION
    )
    assert admission.engine_id == ENGINE_ID
    assert (
        admission.status
        is AdapterAdmissionStatus.ADMITTED
    )
    assert admission.reason_codes == (
        "adapter_request_admitted",
    )
    assert (
        admission.request_id
        == request.request_id
    )
    assert (
        admission.validation_id
        == validation.validation_id
    )
    assert (
        admission.adapter_id
        == request.adapter_id
    )
    assert admission.read_only is True
    assert admission.execution_allowed is False
    assert (
        admission.runtime_adapter_required
        is True
    )
    assert len(admission.admission_hash) == 64
    assert (
        admission.checks[
            "request_id_matches"
        ]
        is True
    )
    assert (
        admission.checks[
            "adapter_id_matches"
        ]
        is True
    )
    assert (
        admission.checks[
            "validation_approved"
        ]
        is True
    )
    assert (
        admission.evidence[
            "live_order_submitted"
        ]
        is False
    )


def test_determinism() -> None:
    request = make_request()
    validation = make_validation(request)

    first = evaluate_execution_adapter_admission(
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

    second = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at=(
            "2026-07-10T15:01:02-05:00"
        ),
        evidence={
            "live_order_submitted": False,
            "runtime_adapter_connected": False,
        },
    )

    assert (
        first.admission_id
        == second.admission_id
    )
    assert (
        first.admission_hash
        == second.admission_hash
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
    request = make_request()
    validation = make_validation(request)

    admission = (
        evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
        )
    )

    try:
        admission.status = (
            AdapterAdmissionStatus.BLOCKED
        )
    except (
        FrozenInstanceError,
        AttributeError,
    ):
        pass
    else:
        raise AssertionError(
            "admission dataclass must be immutable"
        )

    try:
        admission.checks[
            "request_id_matches"
        ] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "admission checks must be immutable"
        )


def test_blocked_validation() -> None:
    request = make_request(
        market_id="UNSUPPORTED-001"
    )

    validation = (
        validate_execution_adapter_request(
            request=request,
            registry=make_registry(),
            validated_at=(
                "2026-07-10T15:01:01-05:00"
            ),
        )
    )

    admission = (
        evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
        )
    )

    assert (
        admission.status
        is AdapterAdmissionStatus.BLOCKED
    )
    assert (
        "registry_validation_not_approved"
        in admission.reason_codes
    )
    assert admission.execution_allowed is False


def test_request_mismatch_blocked() -> None:
    first_request = make_request()

    second_request = (
        build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            account_reference=(
                "account-primary"
            ),
            market_id=(
                "KXTEST-26JUL11"
            ),
            action="buy",
            order_type="limit",
            quantity="10",
            limit_price="0.42",
            price_unit=(
                "usd_probability"
            ),
            time_in_force="gtc",
            client_order_id=(
                "client-order-002"
            ),
            created_at=(
                "2026-07-10T15:02:00-05:00"
            ),
            expires_at=(
                "2026-07-10T15:07:00-05:00"
            ),
            rationale=(
                "Second authorized request."
            ),
        )
    )

    validation = make_validation(
        first_request
    )

    admission = (
        evaluate_execution_adapter_admission(
            request=second_request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:02:01-05:00"
            ),
        )
    )

    assert (
        admission.status
        is AdapterAdmissionStatus.BLOCKED
    )
    assert (
        "request_id_mismatch"
        in admission.reason_codes
    )


def test_caller_supplied_timestamp_required() -> None:
    request = make_request()
    validation = make_validation(request)

    expect_admission_error(
        lambda: (
            evaluate_execution_adapter_admission(
                request=request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:01:02"
                ),
            )
        ),
        "must include a timezone offset",
    )


def main() -> None:
    test_admitted_contract()
    test_determinism()
    test_immutability()
    test_blocked_validation()
    test_request_mismatch_blocked()
    test_caller_supplied_timestamp_required()

    request = make_request()
    validation = make_validation(request)

    admission = (
        evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
            evidence={
                "runtime_adapter_connected": False,
                "live_order_submitted": False,
                "exchange_called": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "admission_status": (
            admission.status.value
        ),
        "adapter_id": admission.adapter_id,
        "reason_codes": list(
            admission.reason_codes
        ),
        "read_only": admission.read_only,
        "execution_allowed": (
            admission.execution_allowed
        ),
        "runtime_adapter_required": (
            admission.runtime_adapter_required
        ),
    }

    print(
        "[PASS] INT-018 Q Series "
        "Execution Adapter Admission Gate"
    )
    print(summary)


if __name__ == "__main__":
    main()
