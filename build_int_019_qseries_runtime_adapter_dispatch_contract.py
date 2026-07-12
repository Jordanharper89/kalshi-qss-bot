from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_runtime_adapter_dispatch_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_019_qseries_runtime_adapter_dispatch_contract.py"
)

PACKAGE_INIT_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "__init__.py"
)


MODULE_CONTENT = dedent(
    r'''
    """
    INT-019 — Q Series Runtime Adapter Dispatch Contract.

    This module creates the canonical dispatch envelope delivered to a future
    runtime execution adapter after an INT-018 admission decision.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and dispatch admission.
    * No live order is placed.
    * No exchange, broker, account, or portfolio API is called.
    * No funds, positions, or portfolios are mutated.
    * All records are immutable.
    * All timestamps are caller supplied.
    * All outputs are deterministic, replayable, auditable, and explainable.
    * All hashing uses canonical JSON and never repr().
    """

    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import datetime
    from enum import Enum
    import hashlib
    import json
    from types import MappingProxyType
    from typing import Any, Mapping

    from .qseries_execution_adapter_admission_gate import (
        AdapterAdmissionStatus,
        ExecutionAdapterAdmission,
    )
    from .qseries_execution_adapter_contract import (
        ExecutionAdapterRequest,
    )
    from .qseries_execution_adapter_registry import (
        AdapterValidationStatus,
        ExecutionAdapterValidation,
    )


    SCHEMA_VERSION = "INT-019"
    ENGINE_ID = "INT-019"
    SOURCE_REQUEST_SCHEMA = "INT-016"
    SOURCE_VALIDATION_SCHEMA = "INT-017"
    SOURCE_ADMISSION_SCHEMA = "INT-018"


    class RuntimeAdapterDispatchError(ValueError):
        """Raised when an INT-019 dispatch contract is invalid."""


    class RuntimeDispatchStatus(str, Enum):
        READY_FOR_RUNTIME = "ready_for_runtime"
        BLOCKED = "blocked"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RuntimeAdapterDispatchError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise RuntimeAdapterDispatchError(
                f"{field_name} must not be empty"
            )

        return normalized


    def _normalize_timestamp(
        value: Any,
        field_name: str,
    ) -> str:
        text = _require_non_empty_string(
            value,
            field_name,
        )

        parse_value = text

        if parse_value.endswith("Z"):
            parse_value = parse_value[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(parse_value)
        except ValueError as exc:
            raise RuntimeAdapterDispatchError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise RuntimeAdapterDispatchError(
                f"{field_name} must include a timezone offset"
            )

        return parsed.isoformat()


    def _canonicalize(value: Any) -> Any:
        if value is None or isinstance(
            value,
            (str, int, bool),
        ):
            return value

        if isinstance(value, float):
            if value != value or value in (
                float("inf"),
                float("-inf"),
            ):
                raise RuntimeAdapterDispatchError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise RuntimeAdapterDispatchError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise RuntimeAdapterDispatchError(
            "unsupported canonical value type: "
            f"{type(value).__name__}"
        )


    def canonical_json(value: Any) -> str:
        return json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


    def canonical_hash(value: Any) -> str:
        return hashlib.sha256(
            canonical_json(value).encode("utf-8")
        ).hexdigest()


    def _freeze_mapping(
        value: Mapping[str, Any] | None,
        field_name: str,
    ) -> Mapping[str, Any]:
        if value is None:
            return MappingProxyType({})

        if not isinstance(value, Mapping):
            raise RuntimeAdapterDispatchError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise RuntimeAdapterDispatchError(
                f"{field_name} must resolve to a mapping"
            )

        return MappingProxyType(
            json.loads(
                canonical_json(canonical_value)
            )
        )


    def _mapping_to_dict(
        value: Mapping[str, Any],
    ) -> dict[str, Any]:
        return json.loads(
            canonical_json(value)
        )


    def _normalize_reason_codes(
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if isinstance(values, (str, bytes)):
            raise RuntimeAdapterDispatchError(
                "reason_codes must be an iterable of strings"
            )

        normalized = tuple(
            sorted(
                {
                    _require_non_empty_string(
                        value,
                        "reason_codes",
                    ).lower()
                    for value in values
                }
            )
        )

        if not normalized:
            raise RuntimeAdapterDispatchError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class RuntimeAdapterDispatch:
        """
        Immutable runtime-adapter dispatch envelope.

        READY_FOR_RUNTIME means the request has passed the Q Series contract,
        registry, and admission boundaries. It does not mean an adapter has
        been invoked and does not mean an order has been submitted.
        """

        dispatch_id: str
        request_id: str
        request_contract_hash: str
        validation_id: str
        validation_hash: str
        admission_id: str
        admission_hash: str
        adapter_id: str
        status: RuntimeDispatchStatus
        dispatched_at: str
        expires_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        runtime_context: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        adapter_invocation_required: bool = True
        live_order_submitted: bool = False
        dispatch_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "dispatch_id",
                _require_non_empty_string(
                    self.dispatch_id,
                    "dispatch_id",
                ),
            )
            object.__setattr__(
                self,
                "request_id",
                _require_non_empty_string(
                    self.request_id,
                    "request_id",
                ),
            )
            object.__setattr__(
                self,
                "request_contract_hash",
                _require_non_empty_string(
                    self.request_contract_hash,
                    "request_contract_hash",
                ),
            )
            object.__setattr__(
                self,
                "validation_id",
                _require_non_empty_string(
                    self.validation_id,
                    "validation_id",
                ),
            )
            object.__setattr__(
                self,
                "validation_hash",
                _require_non_empty_string(
                    self.validation_hash,
                    "validation_hash",
                ),
            )
            object.__setattr__(
                self,
                "admission_id",
                _require_non_empty_string(
                    self.admission_id,
                    "admission_id",
                ),
            )
            object.__setattr__(
                self,
                "admission_hash",
                _require_non_empty_string(
                    self.admission_hash,
                    "admission_hash",
                ),
            )
            object.__setattr__(
                self,
                "adapter_id",
                _require_non_empty_string(
                    self.adapter_id,
                    "adapter_id",
                ).lower(),
            )

            if not isinstance(
                self.status,
                RuntimeDispatchStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    RuntimeDispatchStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "dispatched_at",
                _normalize_timestamp(
                    self.dispatched_at,
                    "dispatched_at",
                ),
            )
            object.__setattr__(
                self,
                "expires_at",
                _normalize_timestamp(
                    self.expires_at,
                    "expires_at",
                ),
            )
            object.__setattr__(
                self,
                "reason_codes",
                _normalize_reason_codes(
                    self.reason_codes
                ),
            )
            object.__setattr__(
                self,
                "explanation",
                _require_non_empty_string(
                    self.explanation,
                    "explanation",
                ),
            )
            object.__setattr__(
                self,
                "checks",
                _freeze_mapping(
                    self.checks,
                    "checks",
                ),
            )
            object.__setattr__(
                self,
                "runtime_context",
                _freeze_mapping(
                    self.runtime_context,
                    "runtime_context",
                ),
            )

            if (
                datetime.fromisoformat(self.expires_at)
                <= datetime.fromisoformat(self.dispatched_at)
            ):
                raise RuntimeAdapterDispatchError(
                    "expires_at must be later than dispatched_at"
                )

            if self.schema_version != SCHEMA_VERSION:
                raise RuntimeAdapterDispatchError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise RuntimeAdapterDispatchError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise RuntimeAdapterDispatchError(
                    "INT-019 dispatch records must be read_only"
                )

            if self.execution_allowed is not False:
                raise RuntimeAdapterDispatchError(
                    "INT-019 must not directly allow execution"
                )

            if self.adapter_invocation_required is not True:
                raise RuntimeAdapterDispatchError(
                    "INT-019 must require adapter invocation"
                )

            if self.live_order_submitted is not False:
                raise RuntimeAdapterDispatchError(
                    "INT-019 cannot report a submitted live order"
                )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.dispatch_hash:
                supplied_hash = _require_non_empty_string(
                    self.dispatch_hash,
                    "dispatch_hash",
                )

                if supplied_hash != calculated_hash:
                    raise RuntimeAdapterDispatchError(
                        "dispatch_hash does not match dispatch contents"
                    )

            object.__setattr__(
                self,
                "dispatch_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "dispatch_id": self.dispatch_id,
                "request_id": self.request_id,
                "request_contract_hash": (
                    self.request_contract_hash
                ),
                "validation_id": self.validation_id,
                "validation_hash": self.validation_hash,
                "admission_id": self.admission_id,
                "admission_hash": self.admission_hash,
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "dispatched_at": self.dispatched_at,
                "expires_at": self.expires_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "runtime_context": _mapping_to_dict(
                    self.runtime_context
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "adapter_invocation_required": (
                    self.adapter_invocation_required
                ),
                "live_order_submitted": (
                    self.live_order_submitted
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["dispatch_hash"] = (
                self.dispatch_hash
            )
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def build_runtime_adapter_dispatch(
        *,
        request: ExecutionAdapterRequest,
        validation: ExecutionAdapterValidation,
        admission: ExecutionAdapterAdmission,
        dispatched_at: str,
        expires_at: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> RuntimeAdapterDispatch:
        """
        Build a deterministic dispatch envelope for later runtime-adapter use.

        The function validates the complete INT-016 through INT-018 evidence
        chain. It does not invoke the adapter and does not submit an order.
        """

        if not isinstance(
            request,
            ExecutionAdapterRequest,
        ):
            raise RuntimeAdapterDispatchError(
                "request must be an ExecutionAdapterRequest"
            )

        if not isinstance(
            validation,
            ExecutionAdapterValidation,
        ):
            raise RuntimeAdapterDispatchError(
                "validation must be an ExecutionAdapterValidation"
            )

        if not isinstance(
            admission,
            ExecutionAdapterAdmission,
        ):
            raise RuntimeAdapterDispatchError(
                "admission must be an ExecutionAdapterAdmission"
            )

        if request.schema_version != SOURCE_REQUEST_SCHEMA:
            raise RuntimeAdapterDispatchError(
                "request.schema_version must be INT-016"
            )

        if validation.schema_version != SOURCE_VALIDATION_SCHEMA:
            raise RuntimeAdapterDispatchError(
                "validation.schema_version must be INT-017"
            )

        if admission.schema_version != SOURCE_ADMISSION_SCHEMA:
            raise RuntimeAdapterDispatchError(
                "admission.schema_version must be INT-018"
            )

        normalized_dispatched_at = _normalize_timestamp(
            dispatched_at,
            "dispatched_at",
        )
        normalized_expires_at = _normalize_timestamp(
            expires_at,
            "expires_at",
        )

        checks = {
            "request_validation_id_match": (
                request.request_id
                == validation.request_id
            ),
            "request_admission_id_match": (
                request.request_id
                == admission.request_id
            ),
            "validation_admission_id_match": (
                validation.validation_id
                == admission.validation_id
            ),
            "request_hash_match": (
                request.contract_hash
                == admission.request_contract_hash
            ),
            "validation_hash_match": (
                validation.validation_hash
                == admission.validation_hash
            ),
            "adapter_id_match": (
                request.adapter_id.lower()
                == validation.adapter_id
                == admission.adapter_id
            ),
            "validation_approved": (
                validation.status
                is AdapterValidationStatus.APPROVED
            ),
            "admission_approved": (
                admission.status
                is AdapterAdmissionStatus.ADMITTED
            ),
            "request_read_only": (
                request.read_only is True
            ),
            "validation_read_only": (
                validation.read_only is True
            ),
            "admission_read_only": (
                admission.read_only is True
            ),
            "request_execution_disabled": (
                request.execution_allowed is False
            ),
            "validation_execution_disabled": (
                validation.execution_allowed is False
            ),
            "admission_execution_disabled": (
                admission.execution_allowed is False
            ),
            "runtime_adapter_required": (
                admission.runtime_adapter_required is True
            ),
        }

        reason_codes: list[str] = []

        if not checks["request_validation_id_match"]:
            reason_codes.append(
                "request_validation_mismatch"
            )

        if not checks["request_admission_id_match"]:
            reason_codes.append(
                "request_admission_mismatch"
            )

        if not checks["validation_admission_id_match"]:
            reason_codes.append(
                "validation_admission_mismatch"
            )

        if not checks["request_hash_match"]:
            reason_codes.append(
                "request_hash_mismatch"
            )

        if not checks["validation_hash_match"]:
            reason_codes.append(
                "validation_hash_mismatch"
            )

        if not checks["adapter_id_match"]:
            reason_codes.append(
                "adapter_id_mismatch"
            )

        if not checks["validation_approved"]:
            reason_codes.append(
                "validation_not_approved"
            )

        if not checks["admission_approved"]:
            reason_codes.append(
                "admission_not_approved"
            )

        if not checks["request_read_only"]:
            reason_codes.append(
                "request_not_read_only"
            )

        if not checks["validation_read_only"]:
            reason_codes.append(
                "validation_not_read_only"
            )

        if not checks["admission_read_only"]:
            reason_codes.append(
                "admission_not_read_only"
            )

        if not checks["request_execution_disabled"]:
            reason_codes.append(
                "request_execution_boundary_invalid"
            )

        if not checks["validation_execution_disabled"]:
            reason_codes.append(
                "validation_execution_boundary_invalid"
            )

        if not checks["admission_execution_disabled"]:
            reason_codes.append(
                "admission_execution_boundary_invalid"
            )

        if not checks["runtime_adapter_required"]:
            reason_codes.append(
                "runtime_adapter_requirement_missing"
            )

        if all(checks.values()):
            status = RuntimeDispatchStatus.READY_FOR_RUNTIME
            reason_codes = [
                "runtime_dispatch_ready"
            ]
            explanation = (
                "The INT-016 request, INT-017 validation, and INT-018 "
                "admission records form a valid evidence chain. The dispatch "
                "envelope is ready for later runtime-adapter invocation. "
                "No adapter was invoked and no execution occurred."
            )
        else:
            status = RuntimeDispatchStatus.BLOCKED
            explanation = (
                "The execution evidence chain failed one or more INT-019 "
                "dispatch checks. Runtime-adapter invocation is blocked and "
                "no execution occurred."
            )

        frozen_runtime_context = _freeze_mapping(
            runtime_context,
            "runtime_context",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "request_id": request.request_id,
            "request_contract_hash": (
                request.contract_hash
            ),
            "validation_id": (
                validation.validation_id
            ),
            "validation_hash": (
                validation.validation_hash
            ),
            "admission_id": (
                admission.admission_id
            ),
            "admission_hash": (
                admission.admission_hash
            ),
            "adapter_id": request.adapter_id.lower(),
            "status": status.value,
            "dispatched_at": normalized_dispatched_at,
            "expires_at": normalized_expires_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "runtime_context": _mapping_to_dict(
                frozen_runtime_context
            ),
        }

        dispatch_id = (
            "int019-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return RuntimeAdapterDispatch(
            dispatch_id=dispatch_id,
            request_id=request.request_id,
            request_contract_hash=(
                request.contract_hash
            ),
            validation_id=(
                validation.validation_id
            ),
            validation_hash=(
                validation.validation_hash
            ),
            admission_id=(
                admission.admission_id
            ),
            admission_hash=(
                admission.admission_hash
            ),
            adapter_id=request.adapter_id,
            status=status,
            dispatched_at=normalized_dispatched_at,
            expires_at=normalized_expires_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            runtime_context=frozen_runtime_context,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_REQUEST_SCHEMA",
        "SOURCE_VALIDATION_SCHEMA",
        "SOURCE_ADMISSION_SCHEMA",
        "RuntimeAdapterDispatchError",
        "RuntimeDispatchStatus",
        "RuntimeAdapterDispatch",
        "canonical_json",
        "canonical_hash",
        "build_runtime_adapter_dispatch",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
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
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    '''
    # INT-019 Q Series Runtime Adapter Dispatch Contract
    from .qseries_runtime_adapter_dispatch_contract import (
        RuntimeAdapterDispatch,
        RuntimeAdapterDispatchError,
        RuntimeDispatchStatus,
        build_runtime_adapter_dispatch,
    )
    '''
).strip()


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports(
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = (
        path.read_text(
            encoding="utf-8"
        )
        if path.exists()
        else ""
    )

    marker = (
        "# INT-019 Q Series "
        "Runtime Adapter Dispatch Contract"
    )

    if marker in existing:
        print(
            f"[OK] Export already present in {path}"
        )
        return

    updated = existing.rstrip()

    if updated:
        updated += "\n\n"

    updated += EXPORT_BLOCK + "\n"

    path.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] Updated {path}")


def main() -> None:
    print("========================================")
    print(" INT-019 INSTALLER")
    print(" Q Series Runtime Adapter Dispatch Contract")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )
    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )
    update_package_exports(
        PACKAGE_INIT_PATH
    )

    print()
    print("[DONE] INT-019 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_019_qseries_runtime_adapter_dispatch_contract.py"
    )


if __name__ == "__main__":
    main()