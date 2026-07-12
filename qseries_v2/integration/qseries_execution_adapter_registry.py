"""
INT-017 — Q Series Execution Adapter Registry.

This module defines the canonical registry used to recognize execution
adapters and validate their declared capabilities against INT-016 requests.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns authorization and execution admission.
* No live order is placed.
* No exchange, broker, or account API is called.
* No funds, positions, or portfolios are mutated.
* Registry records are immutable.
* Registry outputs are deterministic and replayable.
* All timestamps are caller supplied.
* All hashing uses canonical JSON and never repr().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .qseries_execution_adapter_contract import (
    AdapterAction,
    AdapterOrderType,
    ExecutionAdapterRequest,
)


SCHEMA_VERSION = "INT-017"
ENGINE_ID = "INT-017"
SOURCE_REQUEST_SCHEMA = "INT-016"


class ExecutionAdapterRegistryError(ValueError):
    """Raised when an execution-adapter registry contract is invalid."""


class AdapterLifecycleStatus(str, Enum):
    REGISTERED = "registered"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class AdapterValidationStatus(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ExecutionAdapterRegistryError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ExecutionAdapterRegistryError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ExecutionAdapterRegistryError(
            f"{field_name} must be a bool"
        )

    return value


def _normalize_timestamp(value: Any, field_name: str) -> str:
    text = _require_non_empty_string(value, field_name)
    parse_value = text

    if parse_value.endswith("Z"):
        parse_value = parse_value[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(parse_value)
    except ValueError as exc:
        raise ExecutionAdapterRegistryError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionAdapterRegistryError(
            f"{field_name} must include a timezone offset"
        )

    return parsed.isoformat()


def _canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ExecutionAdapterRegistryError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ExecutionAdapterRegistryError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    raise ExecutionAdapterRegistryError(
        f"unsupported canonical value type: {type(value).__name__}"
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


def _normalize_string_tuple(
    values: Iterable[Any],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ExecutionAdapterRegistryError(
            f"{field_name} must be an iterable of strings"
        )

    normalized = {
        _require_non_empty_string(value, field_name).lower()
        for value in values
    }

    if not normalized:
        raise ExecutionAdapterRegistryError(
            f"{field_name} must contain at least one value"
        )

    return tuple(sorted(normalized))


def _normalize_action_tuple(
    values: Iterable[AdapterAction | str],
) -> tuple[AdapterAction, ...]:
    if isinstance(values, (str, bytes)):
        raise ExecutionAdapterRegistryError(
            "supported_actions must be an iterable"
        )

    normalized = {
        value
        if isinstance(value, AdapterAction)
        else AdapterAction(str(value).strip().lower())
        for value in values
    }

    if not normalized:
        raise ExecutionAdapterRegistryError(
            "supported_actions must contain at least one value"
        )

    return tuple(sorted(normalized, key=lambda item: item.value))


def _normalize_order_type_tuple(
    values: Iterable[AdapterOrderType | str],
) -> tuple[AdapterOrderType, ...]:
    if isinstance(values, (str, bytes)):
        raise ExecutionAdapterRegistryError(
            "supported_order_types must be an iterable"
        )

    normalized = {
        value
        if isinstance(value, AdapterOrderType)
        else AdapterOrderType(str(value).strip().lower())
        for value in values
    }

    if not normalized:
        raise ExecutionAdapterRegistryError(
            "supported_order_types must contain at least one value"
        )

    return tuple(sorted(normalized, key=lambda item: item.value))


def _freeze_mapping(
    value: Mapping[str, Any] | None,
    field_name: str,
) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})

    if not isinstance(value, Mapping):
        raise ExecutionAdapterRegistryError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise ExecutionAdapterRegistryError(
            f"{field_name} must resolve to a mapping"
        )

    return MappingProxyType(
        json.loads(canonical_json(canonical_value))
    )


def _mapping_to_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(canonical_json(value))


@dataclass(frozen=True, slots=True)
class ExecutionAdapterRegistration:
    """
    Immutable declaration of an execution adapter and its capabilities.

    A registration recognizes an adapter identity. It does not instantiate
    the adapter and does not grant the adapter permission to execute.
    """

    adapter_id: str
    adapter_name: str
    adapter_version: str
    venue_id: str
    supported_market_prefixes: tuple[str, ...]
    supported_actions: tuple[AdapterAction, ...]
    supported_order_types: tuple[AdapterOrderType, ...]
    supported_price_units: tuple[str, ...]
    lifecycle_status: AdapterLifecycleStatus
    registered_at: str
    effective_at: str
    registration_reason: str
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    requires_runtime_adapter: bool = True
    registration_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "adapter_id",
            _require_non_empty_string(
                self.adapter_id,
                "adapter_id",
            ).lower(),
        )
        object.__setattr__(
            self,
            "adapter_name",
            _require_non_empty_string(
                self.adapter_name,
                "adapter_name",
            ),
        )
        object.__setattr__(
            self,
            "adapter_version",
            _require_non_empty_string(
                self.adapter_version,
                "adapter_version",
            ),
        )
        object.__setattr__(
            self,
            "venue_id",
            _require_non_empty_string(
                self.venue_id,
                "venue_id",
            ).lower(),
        )
        object.__setattr__(
            self,
            "supported_market_prefixes",
            _normalize_string_tuple(
                self.supported_market_prefixes,
                "supported_market_prefixes",
            ),
        )
        object.__setattr__(
            self,
            "supported_actions",
            _normalize_action_tuple(
                self.supported_actions
            ),
        )
        object.__setattr__(
            self,
            "supported_order_types",
            _normalize_order_type_tuple(
                self.supported_order_types
            ),
        )
        object.__setattr__(
            self,
            "supported_price_units",
            _normalize_string_tuple(
                self.supported_price_units,
                "supported_price_units",
            ),
        )
        object.__setattr__(
            self,
            "registered_at",
            _normalize_timestamp(
                self.registered_at,
                "registered_at",
            ),
        )
        object.__setattr__(
            self,
            "effective_at",
            _normalize_timestamp(
                self.effective_at,
                "effective_at",
            ),
        )
        object.__setattr__(
            self,
            "registration_reason",
            _require_non_empty_string(
                self.registration_reason,
                "registration_reason",
            ),
        )

        if not isinstance(
            self.lifecycle_status,
            AdapterLifecycleStatus,
        ):
            object.__setattr__(
                self,
                "lifecycle_status",
                AdapterLifecycleStatus(
                    str(self.lifecycle_status).strip().lower()
                ),
            )

        if (
            datetime.fromisoformat(self.effective_at)
            < datetime.fromisoformat(self.registered_at)
        ):
            raise ExecutionAdapterRegistryError(
                "effective_at must not be earlier than registered_at"
            )

        if self.schema_version != SCHEMA_VERSION:
            raise ExecutionAdapterRegistryError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise ExecutionAdapterRegistryError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise ExecutionAdapterRegistryError(
                "INT-017 registrations must be read_only"
            )

        if self.execution_allowed is not False:
            raise ExecutionAdapterRegistryError(
                "INT-017 must not directly allow execution"
            )

        if self.requires_runtime_adapter is not True:
            raise ExecutionAdapterRegistryError(
                "INT-017 must require a runtime adapter"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze_mapping(self.metadata, "metadata"),
        )

        calculated_hash = canonical_hash(
            self._hash_payload()
        )

        if self.registration_hash:
            supplied_hash = _require_non_empty_string(
                self.registration_hash,
                "registration_hash",
            )

            if supplied_hash != calculated_hash:
                raise ExecutionAdapterRegistryError(
                    "registration_hash does not match registration contents"
                )

        object.__setattr__(
            self,
            "registration_hash",
            calculated_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter_name,
            "adapter_version": self.adapter_version,
            "venue_id": self.venue_id,
            "supported_market_prefixes": list(
                self.supported_market_prefixes
            ),
            "supported_actions": [
                item.value for item in self.supported_actions
            ],
            "supported_order_types": [
                item.value for item in self.supported_order_types
            ],
            "supported_price_units": list(
                self.supported_price_units
            ),
            "lifecycle_status": self.lifecycle_status.value,
            "registered_at": self.registered_at,
            "effective_at": self.effective_at,
            "registration_reason": self.registration_reason,
            "metadata": _mapping_to_dict(self.metadata),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "requires_runtime_adapter": (
                self.requires_runtime_adapter
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["registration_hash"] = self.registration_hash
        return payload


@dataclass(frozen=True, slots=True)
class ExecutionAdapterValidation:
    """
    Immutable result of validating an INT-016 request against the registry.
    """

    validation_id: str
    request_id: str
    adapter_id: str
    registration_hash: str | None
    status: AdapterValidationStatus
    validated_at: str
    reason_codes: tuple[str, ...]
    explanation: str
    checks: Mapping[str, Any]
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    runtime_processing_required: bool = True
    validation_hash: str = ""

    def __post_init__(self) -> None:
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

        if self.registration_hash is not None:
            object.__setattr__(
                self,
                "registration_hash",
                _require_non_empty_string(
                    self.registration_hash,
                    "registration_hash",
                ),
            )

        if not isinstance(self.status, AdapterValidationStatus):
            object.__setattr__(
                self,
                "status",
                AdapterValidationStatus(
                    str(self.status).strip().lower()
                ),
            )

        object.__setattr__(
            self,
            "validated_at",
            _normalize_timestamp(
                self.validated_at,
                "validated_at",
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                self.reason_codes,
                "reason_codes",
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
            _freeze_mapping(self.checks, "checks"),
        )

        if self.schema_version != SCHEMA_VERSION:
            raise ExecutionAdapterRegistryError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise ExecutionAdapterRegistryError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise ExecutionAdapterRegistryError(
                "INT-017 validations must be read_only"
            )

        if self.execution_allowed is not False:
            raise ExecutionAdapterRegistryError(
                "INT-017 validations must not directly allow execution"
            )

        if self.runtime_processing_required is not True:
            raise ExecutionAdapterRegistryError(
                "INT-017 validations must require runtime processing"
            )

        calculated_hash = canonical_hash(
            self._hash_payload()
        )

        if self.validation_hash:
            supplied_hash = _require_non_empty_string(
                self.validation_hash,
                "validation_hash",
            )

            if supplied_hash != calculated_hash:
                raise ExecutionAdapterRegistryError(
                    "validation_hash does not match validation contents"
                )

        object.__setattr__(
            self,
            "validation_hash",
            calculated_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "validation_id": self.validation_id,
            "request_id": self.request_id,
            "adapter_id": self.adapter_id,
            "registration_hash": self.registration_hash,
            "status": self.status.value,
            "validated_at": self.validated_at,
            "reason_codes": list(self.reason_codes),
            "explanation": self.explanation,
            "checks": _mapping_to_dict(self.checks),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "runtime_processing_required": (
                self.runtime_processing_required
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["validation_hash"] = self.validation_hash
        return payload


class ExecutionAdapterRegistry:
    """
    Immutable registry of adapter registrations.

    Duplicate adapter identifiers are rejected to preserve one canonical
    registration per adapter identity.
    """

    __slots__ = (
        "_registrations",
        "_registry_hash",
    )

    def __init__(
        self,
        registrations: Iterable[
            ExecutionAdapterRegistration
        ],
    ) -> None:
        registration_map: dict[
            str,
            ExecutionAdapterRegistration,
        ] = {}

        for registration in registrations:
            if not isinstance(
                registration,
                ExecutionAdapterRegistration,
            ):
                raise ExecutionAdapterRegistryError(
                    "registrations must contain "
                    "ExecutionAdapterRegistration records"
                )

            if registration.adapter_id in registration_map:
                raise ExecutionAdapterRegistryError(
                    f"duplicate adapter_id: {registration.adapter_id}"
                )

            registration_map[
                registration.adapter_id
            ] = registration

        ordered = {
            key: registration_map[key]
            for key in sorted(registration_map)
        }

        self._registrations = MappingProxyType(ordered)
        self._registry_hash = canonical_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "registrations": [
                    registration.to_dict()
                    for registration in ordered.values()
                ],
            }
        )

    @property
    def registry_hash(self) -> str:
        return self._registry_hash

    @property
    def adapter_count(self) -> int:
        return len(self._registrations)

    def get(
        self,
        adapter_id: str,
    ) -> ExecutionAdapterRegistration | None:
        normalized = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        ).lower()

        return self._registrations.get(normalized)

    def registrations(
        self,
    ) -> tuple[ExecutionAdapterRegistration, ...]:
        return tuple(self._registrations.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "adapter_count": self.adapter_count,
            "registrations": [
                registration.to_dict()
                for registration in self.registrations()
            ],
            "registry_hash": self.registry_hash,
            "read_only": True,
            "execution_allowed": False,
        }


def build_execution_adapter_registration(
    *,
    adapter_id: str,
    adapter_name: str,
    adapter_version: str,
    venue_id: str,
    supported_market_prefixes: Iterable[str],
    supported_actions: Iterable[AdapterAction | str],
    supported_order_types: Iterable[AdapterOrderType | str],
    supported_price_units: Iterable[str],
    lifecycle_status: AdapterLifecycleStatus | str,
    registered_at: str,
    effective_at: str,
    registration_reason: str,
    metadata: Mapping[str, Any] | None = None,
) -> ExecutionAdapterRegistration:
    return ExecutionAdapterRegistration(
        adapter_id=adapter_id,
        adapter_name=adapter_name,
        adapter_version=adapter_version,
        venue_id=venue_id,
        supported_market_prefixes=tuple(
            supported_market_prefixes
        ),
        supported_actions=tuple(supported_actions),
        supported_order_types=tuple(
            supported_order_types
        ),
        supported_price_units=tuple(
            supported_price_units
        ),
        lifecycle_status=lifecycle_status,
        registered_at=registered_at,
        effective_at=effective_at,
        registration_reason=registration_reason,
        metadata=metadata or {},
    )


def validate_execution_adapter_request(
    *,
    request: ExecutionAdapterRequest,
    registry: ExecutionAdapterRegistry,
    validated_at: str,
) -> ExecutionAdapterValidation:
    """
    Validate an INT-016 request against a canonical adapter registration.

    Approval means only that the adapter identity and declared capabilities
    match the request. It does not mean execution occurred or may occur
    without later runtime controls.
    """

    if not isinstance(request, ExecutionAdapterRequest):
        raise ExecutionAdapterRegistryError(
            "request must be an ExecutionAdapterRequest"
        )

    if request.schema_version != SOURCE_REQUEST_SCHEMA:
        raise ExecutionAdapterRegistryError(
            "request.schema_version must be INT-016"
        )

    if not isinstance(registry, ExecutionAdapterRegistry):
        raise ExecutionAdapterRegistryError(
            "registry must be an ExecutionAdapterRegistry"
        )

    normalized_validated_at = _normalize_timestamp(
        validated_at,
        "validated_at",
    )

    registration = registry.get(request.adapter_id)

    checks: dict[str, bool] = {
        "adapter_registered": registration is not None,
        "adapter_active": False,
        "market_supported": False,
        "action_supported": False,
        "order_type_supported": False,
        "price_unit_supported": False,
        "request_non_executing_contract": (
            request.execution_allowed is False
            and request.requires_concrete_adapter is True
            and request.read_only is True
        ),
    }

    reasons: list[str] = []

    if registration is None:
        reasons.append("adapter_not_registered")
        registration_hash = None
    else:
        registration_hash = registration.registration_hash

        checks["adapter_active"] = (
            registration.lifecycle_status
            is AdapterLifecycleStatus.REGISTERED
        )

        normalized_market_id = request.market_id.lower()

        checks["market_supported"] = any(
            normalized_market_id.startswith(prefix)
            for prefix in registration.supported_market_prefixes
        )

        checks["action_supported"] = (
            request.action in registration.supported_actions
        )

        checks["order_type_supported"] = (
            request.order_type
            in registration.supported_order_types
        )

        if request.price_unit is None:
            checks["price_unit_supported"] = (
                request.order_type is AdapterOrderType.MARKET
            )
        else:
            checks["price_unit_supported"] = (
                request.price_unit.lower()
                in registration.supported_price_units
            )

        if not checks["adapter_active"]:
            reasons.append("adapter_not_active")

        if not checks["market_supported"]:
            reasons.append("market_not_supported")

        if not checks["action_supported"]:
            reasons.append("action_not_supported")

        if not checks["order_type_supported"]:
            reasons.append("order_type_not_supported")

        if not checks["price_unit_supported"]:
            reasons.append("price_unit_not_supported")

    if not checks["request_non_executing_contract"]:
        reasons.append("invalid_request_execution_boundary")

    if all(checks.values()):
        status = AdapterValidationStatus.APPROVED
        reasons = ["adapter_capabilities_verified"]
        explanation = (
            "The INT-016 request targets a registered active adapter "
            "whose declared capabilities support the requested market, "
            "action, order type, and price unit. Runtime processing is "
            "still required and no execution occurred."
        )
    else:
        status = AdapterValidationStatus.BLOCKED
        explanation = (
            "The INT-016 request failed one or more execution-adapter "
            "registry checks. No execution occurred."
        )

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "request_id": request.request_id,
        "adapter_id": request.adapter_id,
        "registration_hash": registration_hash,
        "status": status.value,
        "validated_at": normalized_validated_at,
        "reason_codes": sorted(set(reasons)),
        "checks": checks,
    }

    validation_id = (
        f"int017-{canonical_hash(identity_payload)[:32]}"
    )

    return ExecutionAdapterValidation(
        validation_id=validation_id,
        request_id=request.request_id,
        adapter_id=request.adapter_id,
        registration_hash=registration_hash,
        status=status,
        validated_at=normalized_validated_at,
        reason_codes=tuple(reasons),
        explanation=explanation,
        checks=checks,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_REQUEST_SCHEMA",
    "ExecutionAdapterRegistryError",
    "AdapterLifecycleStatus",
    "AdapterValidationStatus",
    "ExecutionAdapterRegistration",
    "ExecutionAdapterValidation",
    "ExecutionAdapterRegistry",
    "canonical_json",
    "canonical_hash",
    "build_execution_adapter_registration",
    "validate_execution_adapter_request",
]
