"""
INT-023 — Q Series Execution Adapter Invocation Contract.

This module defines the canonical immutable invocation envelope delivered
to a future execution-capable adapter after an INT-022 eligibility decision.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns authorization and execution control.
* INT-022 eligibility evidence is required.
* No adapter is invoked.
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
from typing import Any, Mapping, Protocol, runtime_checkable

from .qseries_runtime_adapter_interface import (
    RuntimeAdapterInvocation,
    RuntimeInvocationStatus,
)
from .qseries_runtime_adapter_invocation_gate import (
    RuntimeAdapterInvocationGateDecision,
    RuntimeInvocationGateStatus,
)


SCHEMA_VERSION = "INT-023"
ENGINE_ID = "INT-023"
SOURCE_INVOCATION_SCHEMA = "INT-020"
SOURCE_GATE_SCHEMA = "INT-022"


class ExecutionAdapterInvocationContractError(ValueError):
    """Raised when an INT-023 invocation contract is invalid."""


class ExecutionInvocationStatus(str, Enum):
    READY_FOR_EXECUTION_ADAPTER = "ready_for_execution_adapter"
    BLOCKED = "blocked"


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ExecutionAdapterInvocationContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ExecutionAdapterInvocationContractError(
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
        raise ExecutionAdapterInvocationContractError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionAdapterInvocationContractError(
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
            raise ExecutionAdapterInvocationContractError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ExecutionAdapterInvocationContractError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise ExecutionAdapterInvocationContractError(
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
        raise ExecutionAdapterInvocationContractError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise ExecutionAdapterInvocationContractError(
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
        raise ExecutionAdapterInvocationContractError(
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
        raise ExecutionAdapterInvocationContractError(
            "reason_codes must contain at least one value"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class ExecutionAdapterInvocation:
    """
    Immutable INT-023 execution-adapter invocation envelope.

    READY_FOR_EXECUTION_ADAPTER means the invocation may be delivered to a
    later approved execution adapter implementation. INT-023 itself does not
    invoke that adapter and does not authorize bypassing later safety gates.
    """

    execution_invocation_id: str
    runtime_invocation_id: str
    runtime_invocation_hash: str
    gate_id: str
    gate_hash: str
    adapter_id: str
    status: ExecutionInvocationStatus
    prepared_at: str
    expires_at: str
    reason_codes: tuple[str, ...]
    explanation: str
    checks: Mapping[str, Any]
    execution_context: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    execution_adapter_call_required: bool = True
    execution_adapter_called: bool = False
    exchange_called: bool = False
    live_order_submitted: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False
    invocation_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "execution_invocation_id",
            _require_non_empty_string(
                self.execution_invocation_id,
                "execution_invocation_id",
            ),
        )
        object.__setattr__(
            self,
            "runtime_invocation_id",
            _require_non_empty_string(
                self.runtime_invocation_id,
                "runtime_invocation_id",
            ),
        )
        object.__setattr__(
            self,
            "runtime_invocation_hash",
            _require_non_empty_string(
                self.runtime_invocation_hash,
                "runtime_invocation_hash",
            ),
        )
        object.__setattr__(
            self,
            "gate_id",
            _require_non_empty_string(
                self.gate_id,
                "gate_id",
            ),
        )
        object.__setattr__(
            self,
            "gate_hash",
            _require_non_empty_string(
                self.gate_hash,
                "gate_hash",
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
            ExecutionInvocationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ExecutionInvocationStatus(
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
            "execution_context",
            _freeze_mapping(
                self.execution_context,
                "execution_context",
            ),
        )

        if (
            datetime.fromisoformat(self.expires_at)
            <= datetime.fromisoformat(self.prepared_at)
        ):
            raise ExecutionAdapterInvocationContractError(
                "expires_at must be later than prepared_at"
            )

        if self.schema_version != SCHEMA_VERSION:
            raise ExecutionAdapterInvocationContractError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise ExecutionAdapterInvocationContractError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise ExecutionAdapterInvocationContractError(
                "INT-023 invocation records must be read_only"
            )

        if self.execution_allowed is not False:
            raise ExecutionAdapterInvocationContractError(
                "INT-023 must not directly allow execution"
            )

        if self.execution_adapter_call_required is not True:
            raise ExecutionAdapterInvocationContractError(
                "INT-023 must require a later execution-adapter call"
            )

        forbidden_true_fields = {
            "execution_adapter_called": self.execution_adapter_called,
            "exchange_called": self.exchange_called,
            "live_order_submitted": self.live_order_submitted,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        for field_name, field_value in forbidden_true_fields.items():
            if field_value is not False:
                raise ExecutionAdapterInvocationContractError(
                    f"{field_name} must remain false"
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
                raise ExecutionAdapterInvocationContractError(
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
            "execution_invocation_id": (
                self.execution_invocation_id
            ),
            "runtime_invocation_id": (
                self.runtime_invocation_id
            ),
            "runtime_invocation_hash": (
                self.runtime_invocation_hash
            ),
            "gate_id": self.gate_id,
            "gate_hash": self.gate_hash,
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
            "execution_context": _mapping_to_dict(
                self.execution_context
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_call_required": (
                self.execution_adapter_call_required
            ),
            "execution_adapter_called": (
                self.execution_adapter_called
            ),
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
        payload["invocation_hash"] = (
            self.invocation_hash
        )
        return payload

    def to_canonical_json(self) -> str:
        return canonical_json(
            self.to_dict()
        )


@runtime_checkable
class ExecutionCapableAdapterProtocol(Protocol):
    """
    Structural contract for a later execution-capable adapter.

    INT-023 defines this interface but provides no implementation.
    """

    adapter_id: str

    def invoke_execution(
        self,
        invocation: ExecutionAdapterInvocation,
    ) -> Any:
        ...


def build_execution_adapter_invocation(
    *,
    runtime_invocation: RuntimeAdapterInvocation,
    gate_decision: RuntimeAdapterInvocationGateDecision,
    prepared_at: str,
    expires_at: str,
    execution_context: Mapping[str, Any] | None = None,
) -> ExecutionAdapterInvocation:
    """
    Build the canonical INT-023 execution-adapter invocation envelope.

    The function validates the INT-020 and INT-022 evidence chain. It does
    not invoke an execution adapter and does not execute an order.
    """

    if not isinstance(
        runtime_invocation,
        RuntimeAdapterInvocation,
    ):
        raise ExecutionAdapterInvocationContractError(
            "runtime_invocation must be a RuntimeAdapterInvocation"
        )

    if not isinstance(
        gate_decision,
        RuntimeAdapterInvocationGateDecision,
    ):
        raise ExecutionAdapterInvocationContractError(
            "gate_decision must be a "
            "RuntimeAdapterInvocationGateDecision"
        )

    if (
        runtime_invocation.schema_version
        != SOURCE_INVOCATION_SCHEMA
    ):
        raise ExecutionAdapterInvocationContractError(
            "runtime_invocation.schema_version must be INT-020"
        )

    if gate_decision.schema_version != SOURCE_GATE_SCHEMA:
        raise ExecutionAdapterInvocationContractError(
            "gate_decision.schema_version must be INT-022"
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
        "runtime_invocation_ready": (
            runtime_invocation.status
            is RuntimeInvocationStatus.READY
        ),
        "gate_eligible": (
            gate_decision.status
            is RuntimeInvocationGateStatus.ELIGIBLE
        ),
        "invocation_id_match": (
            runtime_invocation.invocation_id
            == gate_decision.invocation_id
        ),
        "invocation_hash_match": (
            runtime_invocation.invocation_hash
            == gate_decision.invocation_hash
        ),
        "adapter_id_match": (
            runtime_invocation.adapter_id
            == gate_decision.adapter_id
        ),
        "runtime_invocation_read_only": (
            runtime_invocation.read_only is True
        ),
        "runtime_execution_disabled": (
            runtime_invocation.execution_allowed is False
        ),
        "runtime_adapter_not_called": (
            runtime_invocation.adapter_called is False
        ),
        "gate_read_only": (
            gate_decision.read_only is True
        ),
        "gate_execution_disabled": (
            gate_decision.execution_allowed is False
        ),
        "gate_requires_execution_adapter": (
            gate_decision.execution_adapter_required is True
        ),
        "gate_adapter_not_invoked": (
            gate_decision.adapter_invoked is False
        ),
        "gate_exchange_not_called": (
            gate_decision.exchange_called is False
        ),
        "gate_order_not_submitted": (
            gate_decision.live_order_submitted is False
        ),
        "gate_funds_not_moved": (
            gate_decision.funds_moved is False
        ),
        "gate_portfolio_not_mutated": (
            gate_decision.portfolio_mutated is False
        ),
        "runtime_invocation_not_expired": (
            datetime.fromisoformat(
                normalized_prepared_at
            )
            <= datetime.fromisoformat(
                runtime_invocation.expires_at
            )
        ),
        "gate_hash_present": bool(
            gate_decision.gate_hash
        ),
    }

    reason_mapping = {
        "runtime_invocation_ready": (
            "runtime_invocation_not_ready"
        ),
        "gate_eligible": (
            "invocation_gate_not_eligible"
        ),
        "invocation_id_match": (
            "invocation_id_mismatch"
        ),
        "invocation_hash_match": (
            "invocation_hash_mismatch"
        ),
        "adapter_id_match": (
            "adapter_id_mismatch"
        ),
        "runtime_invocation_read_only": (
            "runtime_invocation_not_read_only"
        ),
        "runtime_execution_disabled": (
            "runtime_execution_boundary_invalid"
        ),
        "runtime_adapter_not_called": (
            "runtime_adapter_already_called"
        ),
        "gate_read_only": (
            "gate_not_read_only"
        ),
        "gate_execution_disabled": (
            "gate_execution_boundary_invalid"
        ),
        "gate_requires_execution_adapter": (
            "execution_adapter_requirement_missing"
        ),
        "gate_adapter_not_invoked": (
            "adapter_invocation_already_detected"
        ),
        "gate_exchange_not_called": (
            "exchange_call_already_detected"
        ),
        "gate_order_not_submitted": (
            "order_submission_already_detected"
        ),
        "gate_funds_not_moved": (
            "fund_movement_already_detected"
        ),
        "gate_portfolio_not_mutated": (
            "portfolio_mutation_already_detected"
        ),
        "runtime_invocation_not_expired": (
            "runtime_invocation_expired"
        ),
        "gate_hash_present": (
            "gate_hash_missing"
        ),
    }

    reason_codes = [
        reason_mapping[check_name]
        for check_name, passed in checks.items()
        if not passed
    ]

    if all(checks.values()):
        status = (
            ExecutionInvocationStatus.READY_FOR_EXECUTION_ADAPTER
        )
        reason_codes = [
            "execution_adapter_invocation_ready"
        ]
        explanation = (
            "The INT-020 runtime invocation and INT-022 eligibility "
            "decision form a valid evidence chain. The INT-023 envelope "
            "is ready for a later approved execution-capable adapter. "
            "No adapter was called and no execution occurred."
        )
    else:
        status = ExecutionInvocationStatus.BLOCKED
        explanation = (
            "The execution-adapter invocation evidence chain failed one "
            "or more INT-023 contract checks. Adapter delivery is blocked "
            "and no execution occurred."
        )

    frozen_context = _freeze_mapping(
        execution_context,
        "execution_context",
    )

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "runtime_invocation_id": (
            runtime_invocation.invocation_id
        ),
        "runtime_invocation_hash": (
            runtime_invocation.invocation_hash
        ),
        "gate_id": gate_decision.gate_id,
        "gate_hash": gate_decision.gate_hash,
        "adapter_id": runtime_invocation.adapter_id,
        "status": status.value,
        "prepared_at": normalized_prepared_at,
        "expires_at": normalized_expires_at,
        "reason_codes": sorted(
            set(reason_codes)
        ),
        "checks": checks,
        "execution_context": _mapping_to_dict(
            frozen_context
        ),
    }

    execution_invocation_id = (
        "int023-"
        f"{canonical_hash(identity_payload)[:32]}"
    )

    return ExecutionAdapterInvocation(
        execution_invocation_id=(
            execution_invocation_id
        ),
        runtime_invocation_id=(
            runtime_invocation.invocation_id
        ),
        runtime_invocation_hash=(
            runtime_invocation.invocation_hash
        ),
        gate_id=gate_decision.gate_id,
        gate_hash=gate_decision.gate_hash,
        adapter_id=runtime_invocation.adapter_id,
        status=status,
        prepared_at=normalized_prepared_at,
        expires_at=normalized_expires_at,
        reason_codes=tuple(reason_codes),
        explanation=explanation,
        checks=checks,
        execution_context=frozen_context,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_INVOCATION_SCHEMA",
    "SOURCE_GATE_SCHEMA",
    "ExecutionAdapterInvocationContractError",
    "ExecutionInvocationStatus",
    "ExecutionAdapterInvocation",
    "ExecutionCapableAdapterProtocol",
    "canonical_json",
    "canonical_hash",
    "build_execution_adapter_invocation",
]
