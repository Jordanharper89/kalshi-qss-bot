"""
INT-021 — Q Series Dry-Run Runtime Adapter.

This module provides the first concrete implementation of the INT-020
runtime adapter protocol.

The adapter is intentionally non-live. It validates a READY invocation,
creates a deterministic simulation receipt, and returns an immutable
NOT_INVOKED runtime result.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns authorization and execution control.
* No exchange, broker, account, or portfolio API is called.
* No live order is submitted.
* No funds are moved.
* No positions or portfolios are mutated.
* All timestamps are caller supplied.
* All records are deterministic, immutable, replayable, auditable,
  and explainable.
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

from .qseries_runtime_adapter_interface import (
    RuntimeAdapterInvocation,
    RuntimeAdapterResult,
    RuntimeExecutionAdapterProtocol,
    RuntimeInvocationStatus,
    RuntimeResultStatus,
)


SCHEMA_VERSION = "INT-021"
ENGINE_ID = "INT-021"
SOURCE_INVOCATION_SCHEMA = "INT-020"


class DryRunRuntimeAdapterError(ValueError):
    """Raised when the INT-021 dry-run adapter contract is invalid."""


class DryRunDecision(str, Enum):
    SIMULATED = "simulated"
    BLOCKED = "blocked"


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise DryRunRuntimeAdapterError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise DryRunRuntimeAdapterError(
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
        raise DryRunRuntimeAdapterError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DryRunRuntimeAdapterError(
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
            raise DryRunRuntimeAdapterError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise DryRunRuntimeAdapterError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise DryRunRuntimeAdapterError(
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
        raise DryRunRuntimeAdapterError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise DryRunRuntimeAdapterError(
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


@dataclass(frozen=True, slots=True)
class DryRunSimulationReceipt:
    """
    Immutable receipt describing the INT-021 dry-run simulation.

    The receipt is evidence that the runtime invocation was evaluated
    without calling a live adapter.
    """

    receipt_id: str
    invocation_id: str
    invocation_hash: str
    adapter_id: str
    decision: DryRunDecision
    simulated_at: str
    checks: Mapping[str, Any]
    simulation_details: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    network_access_enabled: bool = False
    adapter_called: bool = False
    exchange_called: bool = False
    live_order_submitted: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False
    receipt_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "receipt_id",
            _require_non_empty_string(
                self.receipt_id,
                "receipt_id",
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
            self.decision,
            DryRunDecision,
        ):
            object.__setattr__(
                self,
                "decision",
                DryRunDecision(
                    str(self.decision).strip().lower()
                ),
            )

        object.__setattr__(
            self,
            "simulated_at",
            _normalize_timestamp(
                self.simulated_at,
                "simulated_at",
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
            "simulation_details",
            _freeze_mapping(
                self.simulation_details,
                "simulation_details",
            ),
        )

        if self.schema_version != SCHEMA_VERSION:
            raise DryRunRuntimeAdapterError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise DryRunRuntimeAdapterError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise DryRunRuntimeAdapterError(
                "INT-021 receipts must be read_only"
            )

        forbidden_true_fields = {
            "network_access_enabled": self.network_access_enabled,
            "adapter_called": self.adapter_called,
            "exchange_called": self.exchange_called,
            "live_order_submitted": self.live_order_submitted,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        for field_name, field_value in forbidden_true_fields.items():
            if field_value is not False:
                raise DryRunRuntimeAdapterError(
                    f"{field_name} must remain false"
                )

        calculated_hash = canonical_hash(
            self._hash_payload()
        )

        if self.receipt_hash:
            supplied_hash = _require_non_empty_string(
                self.receipt_hash,
                "receipt_hash",
            )

            if supplied_hash != calculated_hash:
                raise DryRunRuntimeAdapterError(
                    "receipt_hash does not match receipt contents"
                )

        object.__setattr__(
            self,
            "receipt_hash",
            calculated_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "receipt_id": self.receipt_id,
            "invocation_id": self.invocation_id,
            "invocation_hash": self.invocation_hash,
            "adapter_id": self.adapter_id,
            "decision": self.decision.value,
            "simulated_at": self.simulated_at,
            "checks": _mapping_to_dict(
                self.checks
            ),
            "simulation_details": _mapping_to_dict(
                self.simulation_details
            ),
            "read_only": self.read_only,
            "network_access_enabled": (
                self.network_access_enabled
            ),
            "adapter_called": self.adapter_called,
            "exchange_called": self.exchange_called,
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
        payload["receipt_hash"] = self.receipt_hash
        return payload

    def to_canonical_json(self) -> str:
        return canonical_json(
            self.to_dict()
        )


@dataclass(frozen=True, slots=True)
class DryRunAdapterResponse:
    """Combined immutable response from the dry-run adapter."""

    receipt: DryRunSimulationReceipt
    result: RuntimeAdapterResult

    def __post_init__(self) -> None:
        if not isinstance(
            self.receipt,
            DryRunSimulationReceipt,
        ):
            raise DryRunRuntimeAdapterError(
                "receipt must be a DryRunSimulationReceipt"
            )

        if not isinstance(
            self.result,
            RuntimeAdapterResult,
        ):
            raise DryRunRuntimeAdapterError(
                "result must be a RuntimeAdapterResult"
            )

        if (
            self.receipt.invocation_id
            != self.result.invocation_id
        ):
            raise DryRunRuntimeAdapterError(
                "receipt and result invocation_id values must match"
            )

        if (
            self.receipt.invocation_hash
            != self.result.invocation_hash
        ):
            raise DryRunRuntimeAdapterError(
                "receipt and result invocation_hash values must match"
            )

        if (
            self.receipt.adapter_id
            != self.result.adapter_id
        ):
            raise DryRunRuntimeAdapterError(
                "receipt and result adapter_id values must match"
            )


class QSeriesDryRunRuntimeAdapter(
    RuntimeExecutionAdapterProtocol
):
    """
    Deterministic non-live implementation of the INT-020 protocol.

    This class never performs network I/O and never executes an order.
    """

    __slots__ = (
        "adapter_id",
        "_adapter_version",
    )

    def __init__(
        self,
        *,
        adapter_id: str,
        adapter_version: str,
    ) -> None:
        self.adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        ).lower()

        self._adapter_version = _require_non_empty_string(
            adapter_version,
            "adapter_version",
        )

    @property
    def adapter_version(self) -> str:
        return self._adapter_version

    def simulate(
        self,
        *,
        invocation: RuntimeAdapterInvocation,
        simulated_at: str,
        simulation_context: Mapping[str, Any] | None = None,
    ) -> DryRunAdapterResponse:
        """
        Evaluate an INT-020 invocation and return a dry-run receipt/result.

        No adapter call, exchange call, or execution occurs.
        """

        if not isinstance(
            invocation,
            RuntimeAdapterInvocation,
        ):
            raise DryRunRuntimeAdapterError(
                "invocation must be a RuntimeAdapterInvocation"
            )

        if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
            raise DryRunRuntimeAdapterError(
                "invocation.schema_version must be INT-020"
            )

        normalized_simulated_at = _normalize_timestamp(
            simulated_at,
            "simulated_at",
        )

        checks = {
            "invocation_ready": (
                invocation.status
                is RuntimeInvocationStatus.READY
            ),
            "adapter_id_matches": (
                invocation.adapter_id
                == self.adapter_id
            ),
            "invocation_read_only": (
                invocation.read_only is True
            ),
            "execution_disabled": (
                invocation.execution_allowed is False
            ),
            "adapter_call_required": (
                invocation.adapter_call_required is True
            ),
            "adapter_not_previously_called": (
                invocation.adapter_called is False
            ),
            "invocation_hash_present": bool(
                invocation.invocation_hash
            ),
            "invocation_not_expired": (
                datetime.fromisoformat(
                    normalized_simulated_at
                )
                <= datetime.fromisoformat(
                    invocation.expires_at
                )
            ),
        }

        decision = (
            DryRunDecision.SIMULATED
            if all(checks.values())
            else DryRunDecision.BLOCKED
        )

        frozen_context = _freeze_mapping(
            simulation_context,
            "simulation_context",
        )

        simulation_details = {
            "adapter_version": self.adapter_version,
            "simulation_context": _mapping_to_dict(
                frozen_context
            ),
            "network_access_enabled": False,
            "adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "invocation_id": invocation.invocation_id,
            "invocation_hash": invocation.invocation_hash,
            "adapter_id": self.adapter_id,
            "decision": decision.value,
            "simulated_at": normalized_simulated_at,
            "checks": checks,
            "simulation_details": simulation_details,
        }

        receipt_id = (
            "int021-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        receipt = DryRunSimulationReceipt(
            receipt_id=receipt_id,
            invocation_id=invocation.invocation_id,
            invocation_hash=invocation.invocation_hash,
            adapter_id=self.adapter_id,
            decision=decision,
            simulated_at=normalized_simulated_at,
            checks=checks,
            simulation_details=simulation_details,
        )

        if decision is DryRunDecision.SIMULATED:
            result_status = RuntimeResultStatus.NOT_INVOKED
            reason_codes = (
                "dry_run_simulation_completed",
            )
            explanation = (
                "The INT-020 invocation was processed by the INT-021 "
                "dry-run adapter. No runtime network adapter was called, "
                "no exchange request was sent, and no execution occurred."
            )
        else:
            result_status = RuntimeResultStatus.REJECTED
            reason_codes = tuple(
                sorted(
                    key
                    for key, passed in checks.items()
                    if not passed
                )
            )
            explanation = (
                "The INT-020 invocation failed one or more INT-021 "
                "dry-run adapter checks. The simulation was blocked and "
                "no execution occurred."
            )

        result_identity = {
            "schema_version": SOURCE_INVOCATION_SCHEMA,
            "invocation_id": invocation.invocation_id,
            "invocation_hash": invocation.invocation_hash,
            "adapter_id": self.adapter_id,
            "status": result_status.value,
            "completed_at": normalized_simulated_at,
            "reason_codes": list(reason_codes),
            "receipt_id": receipt.receipt_id,
            "receipt_hash": receipt.receipt_hash,
        }

        result_id = (
            "int021-result-"
            f"{canonical_hash(result_identity)[:32]}"
        )

        result = RuntimeAdapterResult(
            result_id=result_id,
            invocation_id=invocation.invocation_id,
            invocation_hash=invocation.invocation_hash,
            adapter_id=self.adapter_id,
            status=result_status,
            completed_at=normalized_simulated_at,
            adapter_reference=None,
            reason_codes=reason_codes,
            explanation=explanation,
            details={
                "dry_run_receipt_id": receipt.receipt_id,
                "dry_run_receipt_hash": receipt.receipt_hash,
                "decision": receipt.decision.value,
                "network_access_enabled": False,
                "adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
            read_only=True,
            live_order_submitted=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        return DryRunAdapterResponse(
            receipt=receipt,
            result=result,
        )

    def invoke(
        self,
        invocation: RuntimeAdapterInvocation,
    ) -> RuntimeAdapterResult:
        """
        Protocol method intentionally disabled for deterministic safety.

        Call simulate() with a caller-supplied timestamp instead.
        """

        raise DryRunRuntimeAdapterError(
            "invoke() is disabled because INT-021 requires a "
            "caller-supplied simulated_at timestamp; use simulate()"
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_INVOCATION_SCHEMA",
    "DryRunRuntimeAdapterError",
    "DryRunDecision",
    "DryRunSimulationReceipt",
    "DryRunAdapterResponse",
    "QSeriesDryRunRuntimeAdapter",
    "canonical_json",
    "canonical_hash",
]
