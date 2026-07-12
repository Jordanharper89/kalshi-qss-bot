"""
INT-026 — Q Series Execution Adapter Result Validation Gate.

This module validates an INT-025 execution-adapter result against the
originating INT-023 execution invocation and INT-024 safety decision.

INT-026 is a post-adapter result validation boundary only.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns authorization and execution control.
* Adapter results must match canonical invocation evidence.
* Safety evidence must match the originating invocation.
* No exchange, broker, account, or portfolio API is called.
* No live order is submitted by this module.
* No fill is confirmed by this module.
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
from .qseries_execution_adapter_result_contract import (
    ExecutionAdapterResult,
    ExecutionAdapterResultStatus,
)
from .qseries_execution_adapter_safety_gate import (
    ExecutionAdapterSafetyDecision,
    ExecutionAdapterSafetyStatus,
)


SCHEMA_VERSION = "INT-026"
ENGINE_ID = "INT-026"
SOURCE_INVOCATION_SCHEMA = "INT-023"
SOURCE_SAFETY_SCHEMA = "INT-024"
SOURCE_RESULT_SCHEMA = "INT-025"


class ExecutionAdapterResultValidationError(ValueError):
    """Raised when an INT-026 result-validation contract is invalid."""


class ExecutionAdapterResultValidationStatus(str, Enum):
    VALIDATED = "validated"
    BLOCKED = "blocked"


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ExecutionAdapterResultValidationError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ExecutionAdapterResultValidationError(
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
        raise ExecutionAdapterResultValidationError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionAdapterResultValidationError(
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
            raise ExecutionAdapterResultValidationError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ExecutionAdapterResultValidationError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise ExecutionAdapterResultValidationError(
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
        raise ExecutionAdapterResultValidationError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise ExecutionAdapterResultValidationError(
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
        raise ExecutionAdapterResultValidationError(
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
        raise ExecutionAdapterResultValidationError(
            "reason_codes must contain at least one value"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class ExecutionAdapterResultValidation:
    """
    Immutable validation decision for an INT-025 adapter result.

    VALIDATED means the result matches the originating invocation and
    safety evidence. It does not confirm a fill, move funds, or mutate a
    portfolio.
    """

    validation_id: str
    execution_invocation_id: str
    execution_invocation_hash: str
    safety_decision_id: str
    safety_hash: str
    result_id: str
    result_hash: str
    adapter_id: str
    result_status: str
    status: ExecutionAdapterResultValidationStatus
    validated_at: str
    reason_codes: tuple[str, ...]
    explanation: str
    checks: Mapping[str, Any]
    evidence: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    fill_confirmed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False
    reconciliation_required: bool = True
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
            "safety_decision_id",
            _require_non_empty_string(
                self.safety_decision_id,
                "safety_decision_id",
            ),
        )
        object.__setattr__(
            self,
            "safety_hash",
            _require_non_empty_string(
                self.safety_hash,
                "safety_hash",
            ),
        )
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
            "result_hash",
            _require_non_empty_string(
                self.result_hash,
                "result_hash",
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
        object.__setattr__(
            self,
            "result_status",
            _require_non_empty_string(
                self.result_status,
                "result_status",
            ).lower(),
        )

        if not isinstance(
            self.status,
            ExecutionAdapterResultValidationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                ExecutionAdapterResultValidationStatus(
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
            "evidence",
            _freeze_mapping(
                self.evidence,
                "evidence",
            ),
        )

        if self.schema_version != SCHEMA_VERSION:
            raise ExecutionAdapterResultValidationError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise ExecutionAdapterResultValidationError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise ExecutionAdapterResultValidationError(
                "INT-026 validation records must be read_only"
            )

        if self.execution_allowed is not False:
            raise ExecutionAdapterResultValidationError(
                "INT-026 must not directly allow execution"
            )

        if self.fill_confirmed is not False:
            raise ExecutionAdapterResultValidationError(
                "INT-026 cannot confirm fills"
            )

        if self.funds_moved is not False:
            raise ExecutionAdapterResultValidationError(
                "INT-026 cannot report fund movement"
            )

        if self.portfolio_mutated is not False:
            raise ExecutionAdapterResultValidationError(
                "INT-026 cannot report portfolio mutation"
            )

        if self.reconciliation_required is not True:
            raise ExecutionAdapterResultValidationError(
                "INT-026 must require later reconciliation"
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
                raise ExecutionAdapterResultValidationError(
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
            "execution_invocation_id": (
                self.execution_invocation_id
            ),
            "execution_invocation_hash": (
                self.execution_invocation_hash
            ),
            "safety_decision_id": (
                self.safety_decision_id
            ),
            "safety_hash": self.safety_hash,
            "result_id": self.result_id,
            "result_hash": self.result_hash,
            "adapter_id": self.adapter_id,
            "result_status": self.result_status,
            "status": self.status.value,
            "validated_at": self.validated_at,
            "reason_codes": list(
                self.reason_codes
            ),
            "explanation": self.explanation,
            "checks": _mapping_to_dict(
                self.checks
            ),
            "evidence": _mapping_to_dict(
                self.evidence
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "fill_confirmed": self.fill_confirmed,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
            "reconciliation_required": (
                self.reconciliation_required
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["validation_hash"] = (
            self.validation_hash
        )
        return payload

    def to_canonical_json(self) -> str:
        return canonical_json(
            self.to_dict()
        )


def validate_execution_adapter_result(
    *,
    invocation: ExecutionAdapterInvocation,
    safety_decision: ExecutionAdapterSafetyDecision,
    result: ExecutionAdapterResult,
    validated_at: str,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionAdapterResultValidation:
    """
    Validate an INT-025 adapter result against INT-023 and INT-024.

    Validation does not confirm a fill or mutate execution state.
    """

    if not isinstance(
        invocation,
        ExecutionAdapterInvocation,
    ):
        raise ExecutionAdapterResultValidationError(
            "invocation must be an ExecutionAdapterInvocation"
        )

    if not isinstance(
        safety_decision,
        ExecutionAdapterSafetyDecision,
    ):
        raise ExecutionAdapterResultValidationError(
            "safety_decision must be an ExecutionAdapterSafetyDecision"
        )

    if not isinstance(
        result,
        ExecutionAdapterResult,
    ):
        raise ExecutionAdapterResultValidationError(
            "result must be an ExecutionAdapterResult"
        )

    if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
        raise ExecutionAdapterResultValidationError(
            "invocation.schema_version must be INT-023"
        )

    if safety_decision.schema_version != SOURCE_SAFETY_SCHEMA:
        raise ExecutionAdapterResultValidationError(
            "safety_decision.schema_version must be INT-024"
        )

    if result.schema_version != SOURCE_RESULT_SCHEMA:
        raise ExecutionAdapterResultValidationError(
            "result.schema_version must be INT-025"
        )

    normalized_validated_at = _normalize_timestamp(
        validated_at,
        "validated_at",
    )

    checks = {
        "invocation_ready": (
            invocation.status
            is ExecutionInvocationStatus.READY_FOR_EXECUTION_ADAPTER
        ),
        "safety_verified": (
            safety_decision.status
            is ExecutionAdapterSafetyStatus.SAFETY_VERIFIED
        ),
        "safety_invocation_id_match": (
            safety_decision.execution_invocation_id
            == invocation.execution_invocation_id
        ),
        "safety_invocation_hash_match": (
            safety_decision.execution_invocation_hash
            == invocation.invocation_hash
        ),
        "result_invocation_id_match": (
            result.execution_invocation_id
            == invocation.execution_invocation_id
        ),
        "result_invocation_hash_match": (
            result.execution_invocation_hash
            == invocation.invocation_hash
        ),
        "adapter_identity_match": (
            invocation.adapter_id
            == safety_decision.adapter_id
            == result.adapter_id
        ),
        "invocation_read_only": (
            invocation.read_only is True
        ),
        "invocation_execution_disabled": (
            invocation.execution_allowed is False
        ),
        "safety_read_only": (
            safety_decision.read_only is True
        ),
        "safety_execution_disabled": (
            safety_decision.execution_allowed is False
        ),
        "result_read_only": (
            result.read_only is True
        ),
        "result_record_declared": (
            result.execution_result_record is True
        ),
        "fill_not_confirmed": (
            result.fill_confirmed is False
        ),
        "funds_not_moved": (
            result.funds_moved is False
        ),
        "portfolio_not_mutated": (
            result.portfolio_mutated is False
        ),
        "result_hash_present": bool(
            result.result_hash
        ),
        "safety_hash_present": bool(
            safety_decision.safety_hash
        ),
        "result_not_before_invocation": (
            datetime.fromisoformat(
                result.completed_at
            )
            >= datetime.fromisoformat(
                invocation.prepared_at
            )
        ),
        "validation_not_before_result": (
            datetime.fromisoformat(
                normalized_validated_at
            )
            >= datetime.fromisoformat(
                result.completed_at
            )
        ),
    }

    reason_mapping = {
        "invocation_ready": (
            "execution_invocation_not_ready"
        ),
        "safety_verified": (
            "execution_safety_not_verified"
        ),
        "safety_invocation_id_match": (
            "safety_invocation_id_mismatch"
        ),
        "safety_invocation_hash_match": (
            "safety_invocation_hash_mismatch"
        ),
        "result_invocation_id_match": (
            "result_invocation_id_mismatch"
        ),
        "result_invocation_hash_match": (
            "result_invocation_hash_mismatch"
        ),
        "adapter_identity_match": (
            "adapter_identity_mismatch"
        ),
        "invocation_read_only": (
            "execution_invocation_not_read_only"
        ),
        "invocation_execution_disabled": (
            "execution_boundary_invalid"
        ),
        "safety_read_only": (
            "safety_decision_not_read_only"
        ),
        "safety_execution_disabled": (
            "safety_execution_boundary_invalid"
        ),
        "result_read_only": (
            "execution_result_not_read_only"
        ),
        "result_record_declared": (
            "execution_result_record_invalid"
        ),
        "fill_not_confirmed": (
            "unexpected_fill_confirmation"
        ),
        "funds_not_moved": (
            "unexpected_fund_movement"
        ),
        "portfolio_not_mutated": (
            "unexpected_portfolio_mutation"
        ),
        "result_hash_present": (
            "result_hash_missing"
        ),
        "safety_hash_present": (
            "safety_hash_missing"
        ),
        "result_not_before_invocation": (
            "result_precedes_invocation"
        ),
        "validation_not_before_result": (
            "validation_precedes_result"
        ),
    }

    reason_codes = [
        reason_mapping[check_name]
        for check_name, passed in checks.items()
        if not passed
    ]

    if all(checks.values()):
        status = (
            ExecutionAdapterResultValidationStatus.VALIDATED
        )
        reason_codes = [
            "execution_adapter_result_validated"
        ]
        explanation = (
            "The INT-025 adapter result matches the originating INT-023 "
            "execution invocation and INT-024 safety decision. The result "
            "is validated as canonical adapter outcome evidence. No fill "
            "is confirmed, no funds are moved, and no portfolio mutation "
            "is performed. Later reconciliation is required."
        )
    else:
        status = (
            ExecutionAdapterResultValidationStatus.BLOCKED
        )
        explanation = (
            "The INT-025 adapter result failed one or more INT-026 "
            "validation checks. The result is blocked from later "
            "reconciliation and no portfolio mutation occurred."
        )

    frozen_evidence = _freeze_mapping(
        evidence,
        "evidence",
    )

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "execution_invocation_id": (
            invocation.execution_invocation_id
        ),
        "execution_invocation_hash": (
            invocation.invocation_hash
        ),
        "safety_decision_id": (
            safety_decision.safety_decision_id
        ),
        "safety_hash": (
            safety_decision.safety_hash
        ),
        "result_id": result.result_id,
        "result_hash": result.result_hash,
        "adapter_id": result.adapter_id,
        "result_status": result.status.value,
        "status": status.value,
        "validated_at": normalized_validated_at,
        "reason_codes": sorted(
            set(reason_codes)
        ),
        "checks": checks,
        "evidence": _mapping_to_dict(
            frozen_evidence
        ),
    }

    validation_id = (
        "int026-"
        f"{canonical_hash(identity_payload)[:32]}"
    )

    return ExecutionAdapterResultValidation(
        validation_id=validation_id,
        execution_invocation_id=(
            invocation.execution_invocation_id
        ),
        execution_invocation_hash=(
            invocation.invocation_hash
        ),
        safety_decision_id=(
            safety_decision.safety_decision_id
        ),
        safety_hash=(
            safety_decision.safety_hash
        ),
        result_id=result.result_id,
        result_hash=result.result_hash,
        adapter_id=result.adapter_id,
        result_status=result.status.value,
        status=status,
        validated_at=normalized_validated_at,
        reason_codes=tuple(reason_codes),
        explanation=explanation,
        checks=checks,
        evidence=frozen_evidence,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_INVOCATION_SCHEMA",
    "SOURCE_SAFETY_SCHEMA",
    "SOURCE_RESULT_SCHEMA",
    "ExecutionAdapterResultValidationError",
    "ExecutionAdapterResultValidationStatus",
    "ExecutionAdapterResultValidation",
    "canonical_json",
    "canonical_hash",
    "validate_execution_adapter_result",
]
