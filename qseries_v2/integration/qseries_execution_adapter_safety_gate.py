"""
INT-024 — Q Series Execution Adapter Safety Gate.

This module performs the final canonical safety evaluation of an INT-023
execution-adapter invocation before a future concrete execution-capable
adapter may be considered for invocation.

INT-024 does not invoke an adapter.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns authorization and execution safety control.
* INT-023 invocation evidence is required.
* Safety evidence must explicitly preserve the closed execution boundary.
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
from typing import Any, Mapping

from .qseries_execution_adapter_invocation_contract import (
    ExecutionAdapterInvocation,
    ExecutionInvocationStatus,
)


SCHEMA_VERSION = "INT-024"
ENGINE_ID = "INT-024"
SOURCE_INVOCATION_SCHEMA = "INT-023"


class ExecutionAdapterSafetyGateError(ValueError):
    """Raised when an INT-024 safety-gate contract is invalid."""


class ExecutionAdapterSafetyStatus(str, Enum):
    SAFETY_VERIFIED = "safety_verified"
    BLOCKED = "blocked"


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ExecutionAdapterSafetyGateError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ExecutionAdapterSafetyGateError(
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
        raise ExecutionAdapterSafetyGateError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionAdapterSafetyGateError(
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
            raise ExecutionAdapterSafetyGateError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ExecutionAdapterSafetyGateError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise ExecutionAdapterSafetyGateError(
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
        raise ExecutionAdapterSafetyGateError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise ExecutionAdapterSafetyGateError(
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
        raise ExecutionAdapterSafetyGateError(
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
        raise ExecutionAdapterSafetyGateError(
            "reason_codes must contain at least one value"
        )

    return normalized


def _require_evidence_bool(
    evidence: Mapping[str, Any],
    field_name: str,
    expected: bool,
) -> bool:
    value = evidence.get(field_name)

    if not isinstance(value, bool):
        return False

    return value is expected


@dataclass(frozen=True, slots=True)
class ExecutionAdapterSafetyDecision:
    """
    Immutable INT-024 safety decision.

    SAFETY_VERIFIED means the INT-023 invocation and caller-supplied safety
    evidence preserve the required execution boundary.

    It does not allow execution and does not invoke an adapter.
    """

    safety_decision_id: str
    execution_invocation_id: str
    execution_invocation_hash: str
    adapter_id: str
    status: ExecutionAdapterSafetyStatus
    evaluated_at: str
    reason_codes: tuple[str, ...]
    explanation: str
    checks: Mapping[str, Any]
    safety_evidence: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    concrete_adapter_required: bool = True
    execution_adapter_called: bool = False
    exchange_called: bool = False
    live_order_submitted: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False
    safety_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "safety_decision_id",
            _require_non_empty_string(
                self.safety_decision_id,
                "safety_decision_id",
            ),
        )
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
            "execution_invocation_hash",
            _require_non_empty_string(
                self.execution_invocation_hash,
                "execution_invocation_hash",
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
            ExecutionAdapterSafetyStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ExecutionAdapterSafetyStatus(
                    str(self.status).strip().lower()
                ),
            )

        object.__setattr__(
            self,
            "evaluated_at",
            _normalize_timestamp(
                self.evaluated_at,
                "evaluated_at",
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
            "safety_evidence",
            _freeze_mapping(
                self.safety_evidence,
                "safety_evidence",
            ),
        )

        if self.schema_version != SCHEMA_VERSION:
            raise ExecutionAdapterSafetyGateError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise ExecutionAdapterSafetyGateError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise ExecutionAdapterSafetyGateError(
                "INT-024 safety decisions must be read_only"
            )

        if self.execution_allowed is not False:
            raise ExecutionAdapterSafetyGateError(
                "INT-024 must not directly allow execution"
            )

        if self.concrete_adapter_required is not True:
            raise ExecutionAdapterSafetyGateError(
                "INT-024 must require a later concrete adapter"
            )

        forbidden_true_fields = {
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

        for field_name, field_value in forbidden_true_fields.items():
            if field_value is not False:
                raise ExecutionAdapterSafetyGateError(
                    f"{field_name} must remain false"
                )

        calculated_hash = canonical_hash(
            self._hash_payload()
        )

        if self.safety_hash:
            supplied_hash = _require_non_empty_string(
                self.safety_hash,
                "safety_hash",
            )

            if supplied_hash != calculated_hash:
                raise ExecutionAdapterSafetyGateError(
                    "safety_hash does not match decision contents"
                )

        object.__setattr__(
            self,
            "safety_hash",
            calculated_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "safety_decision_id": (
                self.safety_decision_id
            ),
            "execution_invocation_id": (
                self.execution_invocation_id
            ),
            "execution_invocation_hash": (
                self.execution_invocation_hash
            ),
            "adapter_id": self.adapter_id,
            "status": self.status.value,
            "evaluated_at": self.evaluated_at,
            "reason_codes": list(
                self.reason_codes
            ),
            "explanation": self.explanation,
            "checks": _mapping_to_dict(
                self.checks
            ),
            "safety_evidence": _mapping_to_dict(
                self.safety_evidence
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "concrete_adapter_required": (
                self.concrete_adapter_required
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
        payload["safety_hash"] = self.safety_hash
        return payload

    def to_canonical_json(self) -> str:
        return canonical_json(
            self.to_dict()
        )


def evaluate_execution_adapter_safety(
    *,
    invocation: ExecutionAdapterInvocation,
    evaluated_at: str,
    safety_evidence: Mapping[str, Any],
) -> ExecutionAdapterSafetyDecision:
    """
    Evaluate an INT-023 execution-adapter invocation against the canonical
    INT-024 safety boundary.

    The caller must explicitly supply non-execution safety evidence.

    This function invokes nothing and executes nothing.
    """

    if not isinstance(
        invocation,
        ExecutionAdapterInvocation,
    ):
        raise ExecutionAdapterSafetyGateError(
            "invocation must be an ExecutionAdapterInvocation"
        )

    if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
        raise ExecutionAdapterSafetyGateError(
            "invocation.schema_version must be INT-023"
        )

    if not isinstance(safety_evidence, Mapping):
        raise ExecutionAdapterSafetyGateError(
            "safety_evidence must be a mapping"
        )

    normalized_evaluated_at = _normalize_timestamp(
        evaluated_at,
        "evaluated_at",
    )

    frozen_evidence = _freeze_mapping(
        safety_evidence,
        "safety_evidence",
    )

    checks = {
        "invocation_ready": (
            invocation.status
            is ExecutionInvocationStatus.READY_FOR_EXECUTION_ADAPTER
        ),
        "invocation_read_only": (
            invocation.read_only is True
        ),
        "invocation_execution_disabled": (
            invocation.execution_allowed is False
        ),
        "execution_adapter_call_required": (
            invocation.execution_adapter_call_required is True
        ),
        "execution_adapter_not_called": (
            invocation.execution_adapter_called is False
        ),
        "exchange_not_called": (
            invocation.exchange_called is False
        ),
        "live_order_not_submitted": (
            invocation.live_order_submitted is False
        ),
        "funds_not_moved": (
            invocation.funds_moved is False
        ),
        "portfolio_not_mutated": (
            invocation.portfolio_mutated is False
        ),
        "invocation_hash_present": bool(
            invocation.invocation_hash
        ),
        "invocation_not_expired": (
            datetime.fromisoformat(
                normalized_evaluated_at
            )
            <= datetime.fromisoformat(
                invocation.expires_at
            )
        ),
        "evidence_network_disabled": (
            _require_evidence_bool(
                frozen_evidence,
                "network_access_enabled",
                False,
            )
        ),
        "evidence_adapter_not_called": (
            _require_evidence_bool(
                frozen_evidence,
                "execution_adapter_called",
                False,
            )
        ),
        "evidence_exchange_not_called": (
            _require_evidence_bool(
                frozen_evidence,
                "exchange_called",
                False,
            )
        ),
        "evidence_order_not_submitted": (
            _require_evidence_bool(
                frozen_evidence,
                "live_order_submitted",
                False,
            )
        ),
        "evidence_funds_not_moved": (
            _require_evidence_bool(
                frozen_evidence,
                "funds_moved",
                False,
            )
        ),
        "evidence_portfolio_not_mutated": (
            _require_evidence_bool(
                frozen_evidence,
                "portfolio_mutated",
                False,
            )
        ),
    }

    reason_mapping = {
        "invocation_ready": (
            "execution_invocation_not_ready"
        ),
        "invocation_read_only": (
            "execution_invocation_not_read_only"
        ),
        "invocation_execution_disabled": (
            "execution_boundary_invalid"
        ),
        "execution_adapter_call_required": (
            "execution_adapter_requirement_missing"
        ),
        "execution_adapter_not_called": (
            "execution_adapter_already_called"
        ),
        "exchange_not_called": (
            "exchange_call_already_detected"
        ),
        "live_order_not_submitted": (
            "order_submission_already_detected"
        ),
        "funds_not_moved": (
            "fund_movement_already_detected"
        ),
        "portfolio_not_mutated": (
            "portfolio_mutation_already_detected"
        ),
        "invocation_hash_present": (
            "invocation_hash_missing"
        ),
        "invocation_not_expired": (
            "execution_invocation_expired"
        ),
        "evidence_network_disabled": (
            "network_safety_evidence_invalid"
        ),
        "evidence_adapter_not_called": (
            "adapter_call_safety_evidence_invalid"
        ),
        "evidence_exchange_not_called": (
            "exchange_call_safety_evidence_invalid"
        ),
        "evidence_order_not_submitted": (
            "order_submission_safety_evidence_invalid"
        ),
        "evidence_funds_not_moved": (
            "fund_movement_safety_evidence_invalid"
        ),
        "evidence_portfolio_not_mutated": (
            "portfolio_mutation_safety_evidence_invalid"
        ),
    }

    reason_codes = [
        reason_mapping[check_name]
        for check_name, passed in checks.items()
        if not passed
    ]

    if all(checks.values()):
        status = (
            ExecutionAdapterSafetyStatus.SAFETY_VERIFIED
        )
        reason_codes = [
            "execution_adapter_safety_verified"
        ]
        explanation = (
            "The INT-023 execution-adapter invocation preserves all "
            "required Q Series execution-boundary invariants and the "
            "caller-supplied safety evidence confirms that no network, "
            "adapter, exchange, order, fund, or portfolio mutation "
            "activity has occurred. A later concrete adapter is still "
            "required. INT-024 does not allow or perform execution."
        )
    else:
        status = ExecutionAdapterSafetyStatus.BLOCKED
        explanation = (
            "The INT-023 invocation or supplied safety evidence failed "
            "one or more INT-024 checks. Concrete adapter advancement is "
            "blocked and no execution occurred."
        )

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "execution_invocation_id": (
            invocation.execution_invocation_id
        ),
        "execution_invocation_hash": (
            invocation.invocation_hash
        ),
        "adapter_id": invocation.adapter_id,
        "status": status.value,
        "evaluated_at": normalized_evaluated_at,
        "reason_codes": sorted(
            set(reason_codes)
        ),
        "checks": checks,
        "safety_evidence": _mapping_to_dict(
            frozen_evidence
        ),
    }

    safety_decision_id = (
        "int024-"
        f"{canonical_hash(identity_payload)[:32]}"
    )

    return ExecutionAdapterSafetyDecision(
        safety_decision_id=safety_decision_id,
        execution_invocation_id=(
            invocation.execution_invocation_id
        ),
        execution_invocation_hash=(
            invocation.invocation_hash
        ),
        adapter_id=invocation.adapter_id,
        status=status,
        evaluated_at=normalized_evaluated_at,
        reason_codes=tuple(reason_codes),
        explanation=explanation,
        checks=checks,
        safety_evidence=frozen_evidence,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_INVOCATION_SCHEMA",
    "ExecutionAdapterSafetyGateError",
    "ExecutionAdapterSafetyStatus",
    "ExecutionAdapterSafetyDecision",
    "canonical_json",
    "canonical_hash",
    "evaluate_execution_adapter_safety",
]
