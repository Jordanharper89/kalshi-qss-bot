from __future__ import annotations

from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
    AdapterAdmissionStatus,
    evaluate_execution_adapter_admission,
)
from qseries_v2.integration.qseries_execution_adapter_contract import (
    AdapterRequestStatus,
    build_execution_adapter_request,
    build_not_executed_result,
)
from qseries_v2.integration.qseries_execution_adapter_registry import (
    AdapterValidationStatus,
    ExecutionAdapterRegistry,
    build_execution_adapter_registration,
    validate_execution_adapter_request,
)
from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
    RuntimeDispatchStatus,
    build_runtime_adapter_dispatch,
)


SCHEMA_VERSION = "INT-SMOKE-004"
ENGINE_ID = "INT-SMOKE-004"


def make_int_015_authorization() -> dict:
    return {
        "schema_version": "INT-015",
        "engine_id": "INT-015",
        "authorization_id": "final-auth-smoke-004",
        "authorization_status": "authorized",
        "opportunity_id": "opportunity-smoke-004",
        "read_only": True,
        "execution_allowed": False,
        "adapter_execution_required": True,
        "authorized_at": "2026-07-10T16:00:00-05:00",
        "explanation": {
            "decision": "authorized for adapter-boundary smoke test",
            "live_execution": False,
        },
    }


def make_registration():
    return build_execution_adapter_registration(
        adapter_id="adapter.kalshi.execution",
        adapter_name="Kalshi Execution Adapter",
        adapter_version="1.0.0",
        venue_id="kalshi",
        supported_market_prefixes=[
            "kxsmoke",
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
        registered_at="2026-07-10T16:00:01-05:00",
        effective_at="2026-07-10T16:00:01-05:00",
        registration_reason=(
            "Register deterministic smoke-test adapter identity."
        ),
        metadata={
            "environment": "smoke",
            "network_access_enabled": False,
            "live_execution_enabled": False,
        },
    )


def build_pipeline():
    authorization = make_int_015_authorization()

    request = build_execution_adapter_request(
        authorization_record=authorization,
        adapter_id="adapter.kalshi.execution",
        account_reference="account-smoke",
        market_id="KXSMOKE-26JUL10",
        action="buy",
        order_type="limit",
        quantity="5",
        limit_price="0.41",
        price_unit="usd_probability",
        time_in_force="gtc",
        client_order_id="smoke-client-order-004",
        created_at="2026-07-10T16:00:02-05:00",
        expires_at="2026-07-10T16:05:00-05:00",
        rationale=(
            "INT-015 authorization converted into an INT-016 "
            "adapter request for deterministic smoke validation."
        ),
        metadata={
            "smoke_gate": SCHEMA_VERSION,
            "network_access_enabled": False,
            "adapter_invoked": False,
        },
    )

    registry = ExecutionAdapterRegistry(
        [make_registration()]
    )

    validation = validate_execution_adapter_request(
        request=request,
        registry=registry,
        validated_at="2026-07-10T16:00:03-05:00",
    )

    admission = evaluate_execution_adapter_admission(
        request=request,
        validation=validation,
        admitted_at="2026-07-10T16:00:04-05:00",
        evidence={
            "authorization_schema": "INT-015",
            "request_schema": "INT-016",
            "validation_schema": "INT-017",
            "adapter_invoked": False,
            "exchange_called": False,
            "live_order_submitted": False,
        },
    )

    dispatch = build_runtime_adapter_dispatch(
        request=request,
        validation=validation,
        admission=admission,
        dispatched_at="2026-07-10T16:00:05-05:00",
        expires_at="2026-07-10T16:04:59-05:00",
        runtime_context={
            "environment": "smoke",
            "network_access_enabled": False,
            "adapter_invoked": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    result = build_not_executed_result(
        request=request,
        processed_at="2026-07-10T16:00:06-05:00",
        reason_code="smoke_gate_non_execution",
        explanation=(
            "The smoke integration gate validated the complete "
            "adapter pipeline without invoking a runtime adapter."
        ),
        details={
            "dispatch_id": dispatch.dispatch_id,
            "adapter_invoked": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        },
    )

    return {
        "authorization": authorization,
        "request": request,
        "registry": registry,
        "validation": validation,
        "admission": admission,
        "dispatch": dispatch,
        "result": result,
    }


def test_complete_pipeline_passes() -> None:
    pipeline = build_pipeline()

    request = pipeline["request"]
    validation = pipeline["validation"]
    admission = pipeline["admission"]
    dispatch = pipeline["dispatch"]
    result = pipeline["result"]

    assert request.request_status is (
        AdapterRequestStatus.READY_FOR_ADAPTER
    )

    assert validation.status is (
        AdapterValidationStatus.APPROVED
    )

    assert admission.status is (
        AdapterAdmissionStatus.ADMITTED
    )

    assert dispatch.status is (
        RuntimeDispatchStatus.READY_FOR_RUNTIME
    )

    assert result.status.value == "not_executed"


def test_canonical_evidence_chain() -> None:
    pipeline = build_pipeline()

    request = pipeline["request"]
    validation = pipeline["validation"]
    admission = pipeline["admission"]
    dispatch = pipeline["dispatch"]

    assert validation.request_id == request.request_id
    assert admission.request_id == request.request_id
    assert admission.validation_id == validation.validation_id

    assert (
        admission.request_contract_hash
        == request.contract_hash
    )

    assert (
        admission.validation_hash
        == validation.validation_hash
    )

    assert dispatch.request_id == request.request_id
    assert dispatch.validation_id == validation.validation_id
    assert dispatch.admission_id == admission.admission_id

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


def test_deterministic_replay() -> None:
    first = build_pipeline()
    second = build_pipeline()

    assert (
        first["request"].request_id
        == second["request"].request_id
    )

    assert (
        first["request"].contract_hash
        == second["request"].contract_hash
    )

    assert (
        first["registry"].registry_hash
        == second["registry"].registry_hash
    )

    assert (
        first["validation"].validation_id
        == second["validation"].validation_id
    )

    assert (
        first["validation"].validation_hash
        == second["validation"].validation_hash
    )

    assert (
        first["admission"].admission_id
        == second["admission"].admission_id
    )

    assert (
        first["admission"].admission_hash
        == second["admission"].admission_hash
    )

    assert (
        first["dispatch"].dispatch_id
        == second["dispatch"].dispatch_id
    )

    assert (
        first["dispatch"].dispatch_hash
        == second["dispatch"].dispatch_hash
    )

    assert (
        first["result"].result_id
        == second["result"].result_id
    )

    assert (
        first["result"].result_hash
        == second["result"].result_hash
    )


def test_execution_boundary_remains_closed() -> None:
    pipeline = build_pipeline()

    authorization = pipeline["authorization"]
    request = pipeline["request"]
    validation = pipeline["validation"]
    admission = pipeline["admission"]
    dispatch = pipeline["dispatch"]
    result = pipeline["result"]

    assert authorization["read_only"] is True
    assert authorization["execution_allowed"] is False
    assert authorization["adapter_execution_required"] is True

    assert request.read_only is True
    assert request.execution_allowed is False
    assert request.requires_concrete_adapter is True

    assert validation.read_only is True
    assert validation.execution_allowed is False
    assert validation.runtime_processing_required is True

    assert admission.read_only is True
    assert admission.execution_allowed is False
    assert admission.runtime_adapter_required is True

    assert dispatch.read_only is True
    assert dispatch.execution_allowed is False
    assert dispatch.adapter_invocation_required is True
    assert dispatch.live_order_submitted is False

    assert result.read_only is True
    assert result.status.value == "not_executed"
    assert result.executed_quantity == "0"

    assert (
        dispatch.runtime_context["network_access_enabled"]
        is False
    )
    assert (
        dispatch.runtime_context["adapter_invoked"]
        is False
    )
    assert (
        dispatch.runtime_context["exchange_called"]
        is False
    )
    assert (
        dispatch.runtime_context["live_order_submitted"]
        is False
    )
    assert (
        dispatch.runtime_context["funds_moved"]
        is False
    )
    assert (
        dispatch.runtime_context["portfolio_mutated"]
        is False
    )

    assert result.details["adapter_invoked"] is False
    assert result.details["exchange_called"] is False
    assert result.details["live_order_submitted"] is False
    assert result.details["funds_moved"] is False
    assert result.details["portfolio_mutated"] is False


def test_registry_and_dispatch_identity() -> None:
    pipeline = build_pipeline()

    registry = pipeline["registry"]
    request = pipeline["request"]
    validation = pipeline["validation"]
    admission = pipeline["admission"]
    dispatch = pipeline["dispatch"]

    registration = registry.get(
        "adapter.kalshi.execution"
    )

    assert registration is not None

    assert registration.adapter_id == request.adapter_id
    assert validation.adapter_id == request.adapter_id
    assert admission.adapter_id == request.adapter_id
    assert dispatch.adapter_id == request.adapter_id

    assert (
        validation.registration_hash
        == registration.registration_hash
    )


def main() -> None:
    test_complete_pipeline_passes()
    test_canonical_evidence_chain()
    test_deterministic_replay()
    test_execution_boundary_remains_closed()
    test_registry_and_dispatch_identity()

    pipeline = build_pipeline()

    request = pipeline["request"]
    validation = pipeline["validation"]
    admission = pipeline["admission"]
    dispatch = pipeline["dispatch"]
    result = pipeline["result"]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "request_status": request.request_status.value,
        "validation_status": validation.status.value,
        "admission_status": admission.status.value,
        "dispatch_status": dispatch.status.value,
        "result_status": result.status.value,
        "adapter_id": dispatch.adapter_id,
        "deterministic_replay": True,
        "read_only": True,
        "execution_allowed": False,
        "adapter_invoked": False,
        "exchange_called": False,
        "live_order_submitted": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-SMOKE-004 Q Series "
        "Execution Adapter Pipeline Smoke Gate"
    )
    print(summary)


if __name__ == "__main__":
    main()
