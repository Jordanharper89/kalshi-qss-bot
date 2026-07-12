from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_runtime_adapter_interface.py"
)

TEST_PATH = (
    ROOT
    / "test_int_020_qseries_runtime_adapter_interface.py"
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
    INT-020 — Q Series Runtime Adapter Interface.

    This module defines the canonical runtime interface that future concrete
    execution adapters must implement.

    INT-020 does not implement a live adapter. It does not call an exchange,
    submit an order, move funds, mutate positions, or change portfolios.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and execution control.
    * Runtime adapters must consume canonical INT-019 dispatch records.
    * Invocation and result records are immutable.
    * All timestamps are caller supplied.
    * All records are deterministic, replayable, auditable, and explainable.
    * All hashing uses canonical JSON and never repr().
    """

    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import datetime
    from enum import Enum
    import hashlib
    import json
    from types import MappingProxyType
    from typing import Any, Mapping, Protocol, runtime_checkable

    from .qseries_runtime_adapter_dispatch_contract import (
        RuntimeAdapterDispatch,
        RuntimeDispatchStatus,
    )


    SCHEMA_VERSION = "INT-020"
    ENGINE_ID = "INT-020"
    SOURCE_DISPATCH_SCHEMA = "INT-019"


    class RuntimeAdapterInterfaceError(ValueError):
        """Raised when an INT-020 runtime-adapter contract is invalid."""


    class RuntimeInvocationStatus(str, Enum):
        READY = "ready"
        BLOCKED = "blocked"


    class RuntimeResultStatus(str, Enum):
        NOT_INVOKED = "not_invoked"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        FAILED = "failed"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RuntimeAdapterInterfaceError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise RuntimeAdapterInterfaceError(
                f"{field_name} must not be empty"
            )

        return normalized


    def _normalize_optional_string(
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        return _require_non_empty_string(
            value,
            field_name,
        )


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
            raise RuntimeAdapterInterfaceError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise RuntimeAdapterInterfaceError(
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
                raise RuntimeAdapterInterfaceError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise RuntimeAdapterInterfaceError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise RuntimeAdapterInterfaceError(
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
            raise RuntimeAdapterInterfaceError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise RuntimeAdapterInterfaceError(
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
            raise RuntimeAdapterInterfaceError(
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
            raise RuntimeAdapterInterfaceError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class RuntimeAdapterInvocation:
        """
        Immutable invocation envelope supplied to a runtime adapter.

        READY means the dispatch chain is valid for adapter invocation.
        INT-020 itself does not invoke an adapter.
        """

        invocation_id: str
        dispatch_id: str
        dispatch_hash: str
        request_id: str
        adapter_id: str
        status: RuntimeInvocationStatus
        prepared_at: str
        expires_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        invocation_context: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        adapter_call_required: bool = True
        adapter_called: bool = False
        invocation_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "invocation_id",
                _require_non_empty_string(
                    self.invocation_id,
                    "invocation_id",
                ),
            )
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
                "dispatch_hash",
                _require_non_empty_string(
                    self.dispatch_hash,
                    "dispatch_hash",
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
                "adapter_id",
                _require_non_empty_string(
                    self.adapter_id,
                    "adapter_id",
                ).lower(),
            )

            if not isinstance(
                self.status,
                RuntimeInvocationStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    RuntimeInvocationStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "prepared_at",
                _normalize_timestamp(
                    self.prepared_at,
                    "prepared_at",
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
                "invocation_context",
                _freeze_mapping(
                    self.invocation_context,
                    "invocation_context",
                ),
            )

            if (
                datetime.fromisoformat(self.expires_at)
                <= datetime.fromisoformat(self.prepared_at)
            ):
                raise RuntimeAdapterInterfaceError(
                    "expires_at must be later than prepared_at"
                )

            if self.schema_version != SCHEMA_VERSION:
                raise RuntimeAdapterInterfaceError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise RuntimeAdapterInterfaceError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise RuntimeAdapterInterfaceError(
                    "INT-020 invocation records must be read_only"
                )

            if self.execution_allowed is not False:
                raise RuntimeAdapterInterfaceError(
                    "INT-020 must not directly allow execution"
                )

            if self.adapter_call_required is not True:
                raise RuntimeAdapterInterfaceError(
                    "INT-020 must require a later adapter call"
                )

            if self.adapter_called is not False:
                raise RuntimeAdapterInterfaceError(
                    "INT-020 cannot report that an adapter was called"
                )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.invocation_hash:
                supplied_hash = _require_non_empty_string(
                    self.invocation_hash,
                    "invocation_hash",
                )

                if supplied_hash != calculated_hash:
                    raise RuntimeAdapterInterfaceError(
                        "invocation_hash does not match invocation contents"
                    )

            object.__setattr__(
                self,
                "invocation_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "invocation_id": self.invocation_id,
                "dispatch_id": self.dispatch_id,
                "dispatch_hash": self.dispatch_hash,
                "request_id": self.request_id,
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "prepared_at": self.prepared_at,
                "expires_at": self.expires_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "invocation_context": _mapping_to_dict(
                    self.invocation_context
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "adapter_call_required": (
                    self.adapter_call_required
                ),
                "adapter_called": self.adapter_called,
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["invocation_hash"] = (
                self.invocation_hash
            )
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    @dataclass(frozen=True, slots=True)
    class RuntimeAdapterResult:
        """
        Immutable result returned by a runtime-adapter implementation.

        INT-020 provides the result contract only. It does not provide a live
        implementation.
        """

        result_id: str
        invocation_id: str
        invocation_hash: str
        adapter_id: str
        status: RuntimeResultStatus
        completed_at: str
        adapter_reference: str | None
        reason_codes: tuple[str, ...]
        explanation: str
        details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        live_order_submitted: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        result_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "result_id",
                _require_non_empty_string(
                    self.result_id,
                    "result_id",
                ),
            )
            object.__setattr__(
                self,
                "invocation_id",
                _require_non_empty_string(
                    self.invocation_id,
                    "invocation_id",
                ),
            )
            object.__setattr__(
                self,
                "invocation_hash",
                _require_non_empty_string(
                    self.invocation_hash,
                    "invocation_hash",
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
                RuntimeResultStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    RuntimeResultStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "completed_at",
                _normalize_timestamp(
                    self.completed_at,
                    "completed_at",
                ),
            )
            object.__setattr__(
                self,
                "adapter_reference",
                _normalize_optional_string(
                    self.adapter_reference,
                    "adapter_reference",
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
                "details",
                _freeze_mapping(
                    self.details,
                    "details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise RuntimeAdapterInterfaceError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise RuntimeAdapterInterfaceError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise RuntimeAdapterInterfaceError(
                    "INT-020 result records must be read_only"
                )

            if self.status is RuntimeResultStatus.NOT_INVOKED:
                if self.adapter_reference is not None:
                    raise RuntimeAdapterInterfaceError(
                        "not_invoked results must not contain "
                        "adapter_reference"
                    )

                if self.live_order_submitted is not False:
                    raise RuntimeAdapterInterfaceError(
                        "not_invoked results cannot submit live orders"
                    )

                if self.funds_moved is not False:
                    raise RuntimeAdapterInterfaceError(
                        "not_invoked results cannot move funds"
                    )

                if self.portfolio_mutated is not False:
                    raise RuntimeAdapterInterfaceError(
                        "not_invoked results cannot mutate portfolios"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.result_hash:
                supplied_hash = _require_non_empty_string(
                    self.result_hash,
                    "result_hash",
                )

                if supplied_hash != calculated_hash:
                    raise RuntimeAdapterInterfaceError(
                        "result_hash does not match result contents"
                    )

            object.__setattr__(
                self,
                "result_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "result_id": self.result_id,
                "invocation_id": self.invocation_id,
                "invocation_hash": self.invocation_hash,
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "completed_at": self.completed_at,
                "adapter_reference": self.adapter_reference,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "details": _mapping_to_dict(
                    self.details
                ),
                "read_only": self.read_only,
                "live_order_submitted": (
                    self.live_order_submitted
                ),
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["result_hash"] = self.result_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    @runtime_checkable
    class RuntimeExecutionAdapterProtocol(Protocol):
        """
        Structural interface for future runtime execution adapters.

        Implementations must return a canonical RuntimeAdapterResult.
        """

        adapter_id: str

        def invoke(
            self,
            invocation: RuntimeAdapterInvocation,
        ) -> RuntimeAdapterResult:
            ...


    def build_runtime_adapter_invocation(
        *,
        dispatch: RuntimeAdapterDispatch,
        prepared_at: str,
        expires_at: str,
        invocation_context: Mapping[str, Any] | None = None,
    ) -> RuntimeAdapterInvocation:
        """
        Build the canonical INT-020 invocation envelope.

        No adapter is called by this function.
        """

        if not isinstance(
            dispatch,
            RuntimeAdapterDispatch,
        ):
            raise RuntimeAdapterInterfaceError(
                "dispatch must be a RuntimeAdapterDispatch"
            )

        if dispatch.schema_version != SOURCE_DISPATCH_SCHEMA:
            raise RuntimeAdapterInterfaceError(
                "dispatch.schema_version must be INT-019"
            )

        normalized_prepared_at = _normalize_timestamp(
            prepared_at,
            "prepared_at",
        )

        normalized_expires_at = _normalize_timestamp(
            expires_at,
            "expires_at",
        )

        checks = {
            "dispatch_ready": (
                dispatch.status
                is RuntimeDispatchStatus.READY_FOR_RUNTIME
            ),
            "dispatch_read_only": (
                dispatch.read_only is True
            ),
            "dispatch_execution_disabled": (
                dispatch.execution_allowed is False
            ),
            "adapter_invocation_required": (
                dispatch.adapter_invocation_required is True
            ),
            "live_order_not_submitted": (
                dispatch.live_order_submitted is False
            ),
            "dispatch_hash_present": bool(
                dispatch.dispatch_hash
            ),
        }

        reason_codes: list[str] = []

        if not checks["dispatch_ready"]:
            reason_codes.append(
                "dispatch_not_ready"
            )

        if not checks["dispatch_read_only"]:
            reason_codes.append(
                "dispatch_not_read_only"
            )

        if not checks["dispatch_execution_disabled"]:
            reason_codes.append(
                "dispatch_execution_boundary_invalid"
            )

        if not checks["adapter_invocation_required"]:
            reason_codes.append(
                "adapter_invocation_not_required"
            )

        if not checks["live_order_not_submitted"]:
            reason_codes.append(
                "live_order_already_submitted"
            )

        if not checks["dispatch_hash_present"]:
            reason_codes.append(
                "dispatch_hash_missing"
            )

        if all(checks.values()):
            status = RuntimeInvocationStatus.READY
            reason_codes = [
                "runtime_invocation_ready"
            ]
            explanation = (
                "The INT-019 dispatch record is valid and ready to be "
                "provided to a future runtime adapter. No adapter was called "
                "and no execution occurred."
            )
        else:
            status = RuntimeInvocationStatus.BLOCKED
            explanation = (
                "The INT-019 dispatch record failed one or more INT-020 "
                "runtime-interface checks. Adapter invocation is blocked."
            )

        frozen_context = _freeze_mapping(
            invocation_context,
            "invocation_context",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "dispatch_id": dispatch.dispatch_id,
            "dispatch_hash": dispatch.dispatch_hash,
            "request_id": dispatch.request_id,
            "adapter_id": dispatch.adapter_id,
            "status": status.value,
            "prepared_at": normalized_prepared_at,
            "expires_at": normalized_expires_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "invocation_context": _mapping_to_dict(
                frozen_context
            ),
        }

        invocation_id = (
            "int020-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return RuntimeAdapterInvocation(
            invocation_id=invocation_id,
            dispatch_id=dispatch.dispatch_id,
            dispatch_hash=dispatch.dispatch_hash,
            request_id=dispatch.request_id,
            adapter_id=dispatch.adapter_id,
            status=status,
            prepared_at=normalized_prepared_at,
            expires_at=normalized_expires_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            invocation_context=frozen_context,
        )


    def build_not_invoked_runtime_result(
        *,
        invocation: RuntimeAdapterInvocation,
        completed_at: str,
        reason_code: str,
        explanation: str,
        details: Mapping[str, Any] | None = None,
    ) -> RuntimeAdapterResult:
        """
        Build a deterministic result proving that no runtime adapter was called.
        """

        if not isinstance(
            invocation,
            RuntimeAdapterInvocation,
        ):
            raise RuntimeAdapterInterfaceError(
                "invocation must be a RuntimeAdapterInvocation"
            )

        normalized_completed_at = _normalize_timestamp(
            completed_at,
            "completed_at",
        )

        normalized_reason_code = (
            _require_non_empty_string(
                reason_code,
                "reason_code",
            ).lower()
        )

        normalized_explanation = (
            _require_non_empty_string(
                explanation,
                "explanation",
            )
        )

        frozen_details = _freeze_mapping(
            details,
            "details",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "invocation_id": invocation.invocation_id,
            "invocation_hash": invocation.invocation_hash,
            "adapter_id": invocation.adapter_id,
            "status": RuntimeResultStatus.NOT_INVOKED.value,
            "completed_at": normalized_completed_at,
            "reason_codes": [normalized_reason_code],
            "explanation": normalized_explanation,
            "details": _mapping_to_dict(
                frozen_details
            ),
        }

        result_id = (
            "int020-result-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return RuntimeAdapterResult(
            result_id=result_id,
            invocation_id=invocation.invocation_id,
            invocation_hash=invocation.invocation_hash,
            adapter_id=invocation.adapter_id,
            status=RuntimeResultStatus.NOT_INVOKED,
            completed_at=normalized_completed_at,
            adapter_reference=None,
            reason_codes=(
                normalized_reason_code,
            ),
            explanation=normalized_explanation,
            details=frozen_details,
            live_order_submitted=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_DISPATCH_SCHEMA",
        "RuntimeAdapterInterfaceError",
        "RuntimeInvocationStatus",
        "RuntimeResultStatus",
        "RuntimeAdapterInvocation",
        "RuntimeAdapterResult",
        "RuntimeExecutionAdapterProtocol",
        "canonical_json",
        "canonical_hash",
        "build_runtime_adapter_invocation",
        "build_not_invoked_runtime_result",
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
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    '''
    # INT-020 Q Series Runtime Adapter Interface
    from .qseries_runtime_adapter_interface import (
        RuntimeAdapterInterfaceError,
        RuntimeAdapterInvocation,
        RuntimeAdapterResult,
        RuntimeExecutionAdapterProtocol,
        RuntimeInvocationStatus,
        RuntimeResultStatus,
        build_not_invoked_runtime_result,
        build_runtime_adapter_invocation,
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
        "# INT-020 Q Series "
        "Runtime Adapter Interface"
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
    print(" INT-020 INSTALLER")
    print(" Q Series Runtime Adapter Interface")
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
    print("[DONE] INT-020 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_020_qseries_runtime_adapter_interface.py"
    )


if __name__ == "__main__":
    main()