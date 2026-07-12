"""
INT-032 — Q Series Fill Confirmation Engine.

This module evaluates canonical INT-030 fill-confirmation requests against
INT-031 fill-confirmation evidence.

INT-032 may confirm a partial or full fill as immutable Q Series execution
evidence. It does not mutate position or portfolio state.

Architectural guarantees
-------------------------
* Oracle remains read-only intelligence.
* Q Series owns execution-state and fill-confirmation control.
* Confirmation evidence must match the canonical request.
* Reported fill type, quantity, and price must match.
* Confirmed fills remain immutable evidence records.
* No exchange, broker, account, or portfolio API is called.
* No funds are moved by this module.
* No positions or portfolios are mutated by this module.
* All timestamps are caller supplied.
* All records are deterministic, immutable, replayable, auditable,
  and explainable.
* All hashing uses canonical JSON and never repr().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from .qseries_fill_confirmation_contract import (
    FillConfirmationRequest,
    FillConfirmationRequestStatus,
    ReportedFillType,
)
from .qseries_fill_confirmation_evidence_contract import (
    FillConfirmationEvidence,
    FillConfirmationEvidenceStatus,
    FillConfirmationEvidenceType,
)


SCHEMA_VERSION = "INT-032"
ENGINE_ID = "INT-032"
SOURCE_REQUEST_SCHEMA = "INT-030"
SOURCE_EVIDENCE_SCHEMA = "INT-031"


class FillConfirmationEngineError(ValueError):
    """Raised when an INT-032 fill-confirmation contract is invalid."""


class FillConfirmationStatus(str, Enum):
    CONFIRMED = "confirmed"
    UNRESOLVED = "unresolved"
    BLOCKED = "blocked"


class ConfirmedFillType(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise FillConfirmationEngineError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise FillConfirmationEngineError(
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


def _normalize_decimal_string(
    value: Any,
    field_name: str,
) -> str:
    text = _require_non_empty_string(
        value,
        field_name,
    )

    try:
        decimal_value = Decimal(text)
    except InvalidOperation as exc:
        raise FillConfirmationEngineError(
            f"{field_name} must be a valid decimal"
        ) from exc

    if not decimal_value.is_finite():
        raise FillConfirmationEngineError(
            f"{field_name} must be finite"
        )

    normalized = format(
        decimal_value.normalize(),
        "f",
    )

    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")

    return normalized


def _normalize_optional_decimal_string(
    value: Any,
    field_name: str,
) -> str | None:
    if value is None:
        return None

    return _normalize_decimal_string(
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
        raise FillConfirmationEngineError(
            f"{field_name} must be a valid ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FillConfirmationEngineError(
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
            raise FillConfirmationEngineError(
                "non-finite floats are not canonical"
            )

        return format(value, ".15g")

    if isinstance(value, Enum):
        return _canonicalize(value.value)

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise FillConfirmationEngineError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(item)

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise FillConfirmationEngineError(
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
        raise FillConfirmationEngineError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise FillConfirmationEngineError(
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
        raise FillConfirmationEngineError(
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
        raise FillConfirmationEngineError(
            "reason_codes must contain at least one value"
        )

    return normalized


def _decimal_values_match(
    left: str | None,
    right: str | None,
) -> bool:
    if left is None or right is None:
        return left is right

    try:
        return Decimal(left) == Decimal(right)
    except InvalidOperation:
        return False


@dataclass(frozen=True, slots=True)
class FillConfirmationDecision:
    """
    Immutable INT-032 fill-confirmation decision.

    CONFIRMED means canonical request and evidence values match and Q Series
    recognizes the reported fill as confirmed execution evidence.

    This record does not mutate a portfolio or position.
    """

    confirmation_id: str
    confirmation_request_id: str
    confirmation_request_hash: str
    confirmation_evidence_id: str
    confirmation_evidence_hash: str
    reconciliation_id: str
    reconciliation_hash: str
    result_id: str
    result_hash: str
    adapter_id: str
    venue_reference: str
    status: FillConfirmationStatus
    confirmed_fill_type: ConfirmedFillType
    confirmed_filled_quantity: str | None
    confirmed_average_price: str | None
    confirmed_at: str
    reason_codes: tuple[str, ...]
    explanation: str
    checks: Mapping[str, Any]
    confirmation_details: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False
    fill_confirmed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False
    position_state_update_required: bool = False
    confirmation_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "confirmation_id",
            _require_non_empty_string(
                self.confirmation_id,
                "confirmation_id",
            ),
        )
        object.__setattr__(
            self,
            "confirmation_request_id",
            _require_non_empty_string(
                self.confirmation_request_id,
                "confirmation_request_id",
            ),
        )
        object.__setattr__(
            self,
            "confirmation_request_hash",
            _require_non_empty_string(
                self.confirmation_request_hash,
                "confirmation_request_hash",
            ),
        )
        object.__setattr__(
            self,
            "confirmation_evidence_id",
            _require_non_empty_string(
                self.confirmation_evidence_id,
                "confirmation_evidence_id",
            ),
        )
        object.__setattr__(
            self,
            "confirmation_evidence_hash",
            _require_non_empty_string(
                self.confirmation_evidence_hash,
                "confirmation_evidence_hash",
            ),
        )
        object.__setattr__(
            self,
            "reconciliation_id",
            _require_non_empty_string(
                self.reconciliation_id,
                "reconciliation_id",
            ),
        )
        object.__setattr__(
            self,
            "reconciliation_hash",
            _require_non_empty_string(
                self.reconciliation_hash,
                "reconciliation_hash",
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
            "venue_reference",
            _require_non_empty_string(
                self.venue_reference,
                "venue_reference",
            ),
        )

        if not isinstance(
            self.status,
            FillConfirmationStatus,
        ):
            object.__setattr__(
                self,
                "status",
                FillConfirmationStatus(
                    str(self.status).strip().lower()
                ),
            )

        if not isinstance(
            self.confirmed_fill_type,
            ConfirmedFillType,
        ):
            object.__setattr__(
                self,
                "confirmed_fill_type",
                ConfirmedFillType(
                    str(
                        self.confirmed_fill_type
                    ).strip().lower()
                ),
            )

        object.__setattr__(
            self,
            "confirmed_filled_quantity",
            _normalize_optional_decimal_string(
                self.confirmed_filled_quantity,
                "confirmed_filled_quantity",
            ),
        )
        object.__setattr__(
            self,
            "confirmed_average_price",
            _normalize_optional_decimal_string(
                self.confirmed_average_price,
                "confirmed_average_price",
            ),
        )
        object.__setattr__(
            self,
            "confirmed_at",
            _normalize_timestamp(
                self.confirmed_at,
                "confirmed_at",
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
            "confirmation_details",
            _freeze_mapping(
                self.confirmation_details,
                "confirmation_details",
            ),
        )

        if self.schema_version != SCHEMA_VERSION:
            raise FillConfirmationEngineError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if self.engine_id != ENGINE_ID:
            raise FillConfirmationEngineError(
                f"engine_id must be {ENGINE_ID}"
            )

        if self.read_only is not True:
            raise FillConfirmationEngineError(
                "INT-032 confirmation decisions must be read_only"
            )

        if self.execution_allowed is not False:
            raise FillConfirmationEngineError(
                "INT-032 must not directly allow execution"
            )

        if self.funds_moved is not False:
            raise FillConfirmationEngineError(
                "INT-032 cannot report fund movement"
            )

        if self.portfolio_mutated is not False:
            raise FillConfirmationEngineError(
                "INT-032 cannot report portfolio mutation"
            )

        if self.status is FillConfirmationStatus.CONFIRMED:
            if self.fill_confirmed is not True:
                raise FillConfirmationEngineError(
                    "confirmed status must set fill_confirmed true"
                )

            if (
                self.confirmed_fill_type
                is ConfirmedFillType.NONE
            ):
                raise FillConfirmationEngineError(
                    "confirmed status requires a confirmed fill type"
                )

            if self.confirmed_filled_quantity is None:
                raise FillConfirmationEngineError(
                    "confirmed status requires "
                    "confirmed_filled_quantity"
                )

            if self.confirmed_average_price is None:
                raise FillConfirmationEngineError(
                    "confirmed status requires "
                    "confirmed_average_price"
                )

            if (
                Decimal(
                    self.confirmed_filled_quantity
                )
                <= 0
            ):
                raise FillConfirmationEngineError(
                    "confirmed_filled_quantity must be greater than zero"
                )

            if (
                Decimal(
                    self.confirmed_average_price
                )
                <= 0
            ):
                raise FillConfirmationEngineError(
                    "confirmed_average_price must be greater than zero"
                )

            if self.position_state_update_required is not True:
                raise FillConfirmationEngineError(
                    "confirmed fills must require a position-state update"
                )

        else:
            if self.fill_confirmed is not False:
                raise FillConfirmationEngineError(
                    "non-confirmed status must set fill_confirmed false"
                )

            if (
                self.confirmed_fill_type
                is not ConfirmedFillType.NONE
            ):
                raise FillConfirmationEngineError(
                    "non-confirmed status must use fill type none"
                )

            if self.confirmed_filled_quantity is not None:
                raise FillConfirmationEngineError(
                    "non-confirmed status must not contain "
                    "confirmed_filled_quantity"
                )

            if self.confirmed_average_price is not None:
                raise FillConfirmationEngineError(
                    "non-confirmed status must not contain "
                    "confirmed_average_price"
                )

            if self.position_state_update_required is not False:
                raise FillConfirmationEngineError(
                    "non-confirmed status must not require "
                    "a position-state update"
                )

        calculated_hash = canonical_hash(
            self._hash_payload()
        )

        if self.confirmation_hash:
            supplied_hash = _require_non_empty_string(
                self.confirmation_hash,
                "confirmation_hash",
            )

            if supplied_hash != calculated_hash:
                raise FillConfirmationEngineError(
                    "confirmation_hash does not match decision contents"
                )

        object.__setattr__(
            self,
            "confirmation_hash",
            calculated_hash,
        )

    def _hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "confirmation_id": self.confirmation_id,
            "confirmation_request_id": (
                self.confirmation_request_id
            ),
            "confirmation_request_hash": (
                self.confirmation_request_hash
            ),
            "confirmation_evidence_id": (
                self.confirmation_evidence_id
            ),
            "confirmation_evidence_hash": (
                self.confirmation_evidence_hash
            ),
            "reconciliation_id": (
                self.reconciliation_id
            ),
            "reconciliation_hash": (
                self.reconciliation_hash
            ),
            "result_id": self.result_id,
            "result_hash": self.result_hash,
            "adapter_id": self.adapter_id,
            "venue_reference": (
                self.venue_reference
            ),
            "status": self.status.value,
            "confirmed_fill_type": (
                self.confirmed_fill_type.value
            ),
            "confirmed_filled_quantity": (
                self.confirmed_filled_quantity
            ),
            "confirmed_average_price": (
                self.confirmed_average_price
            ),
            "confirmed_at": self.confirmed_at,
            "reason_codes": list(
                self.reason_codes
            ),
            "explanation": self.explanation,
            "checks": _mapping_to_dict(
                self.checks
            ),
            "confirmation_details": _mapping_to_dict(
                self.confirmation_details
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "fill_confirmed": self.fill_confirmed,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
            "position_state_update_required": (
                self.position_state_update_required
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._hash_payload()
        payload["confirmation_hash"] = (
            self.confirmation_hash
        )
        return payload

    def to_canonical_json(self) -> str:
        return canonical_json(
            self.to_dict()
        )


def confirm_fill_evidence(
    *,
    request: FillConfirmationRequest,
    evidence: FillConfirmationEvidence,
    confirmed_at: str,
    confirmation_details: Mapping[str, Any] | None = None,
) -> FillConfirmationDecision:
    """
    Evaluate canonical fill-confirmation evidence.

    A matching observed partial or full fill may become confirmed execution
    evidence. This function does not mutate positions or portfolios.
    """

    if not isinstance(
        request,
        FillConfirmationRequest,
    ):
        raise FillConfirmationEngineError(
            "request must be a FillConfirmationRequest"
        )

    if not isinstance(
        evidence,
        FillConfirmationEvidence,
    ):
        raise FillConfirmationEngineError(
            "evidence must be a FillConfirmationEvidence"
        )

    if request.schema_version != SOURCE_REQUEST_SCHEMA:
        raise FillConfirmationEngineError(
            "request.schema_version must be INT-030"
        )

    if evidence.schema_version != SOURCE_EVIDENCE_SCHEMA:
        raise FillConfirmationEngineError(
            "evidence.schema_version must be INT-031"
        )

    normalized_confirmed_at = _normalize_timestamp(
        confirmed_at,
        "confirmed_at",
    )

    expected_evidence_type = {
        ReportedFillType.PARTIAL: (
            FillConfirmationEvidenceType.PARTIAL
        ),
        ReportedFillType.FULL: (
            FillConfirmationEvidenceType.FULL
        ),
    }.get(
        request.reported_fill_type,
        FillConfirmationEvidenceType.NONE,
    )

    checks = {
        "request_ready": (
            request.status
            is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
        ),
        "request_requires_confirmation": (
            request.fill_confirmation_required is True
        ),
        "confirmation_request_id_match": (
            request.confirmation_request_id
            == evidence.confirmation_request_id
        ),
        "confirmation_request_hash_match": (
            request.request_hash
            == evidence.confirmation_request_hash
        ),
        "reconciliation_id_match": (
            request.reconciliation_id
            == evidence.reconciliation_id
        ),
        "reconciliation_hash_match": (
            request.reconciliation_hash
            == evidence.reconciliation_hash
        ),
        "venue_evidence_id_match": (
            request.venue_evidence_id
            == evidence.venue_evidence_id
        ),
        "venue_evidence_hash_match": (
            request.venue_evidence_hash
            == evidence.venue_evidence_hash
        ),
        "result_id_match": (
            request.result_id
            == evidence.result_id
        ),
        "result_hash_match": (
            request.result_hash
            == evidence.result_hash
        ),
        "adapter_identity_match": (
            request.adapter_id
            == evidence.adapter_id
        ),
        "venue_reference_match": (
            request.venue_reference
            == evidence.venue_reference
        ),
        "request_read_only": (
            request.read_only is True
        ),
        "request_execution_disabled": (
            request.execution_allowed is False
        ),
        "request_fill_not_confirmed": (
            request.fill_confirmed is False
        ),
        "request_funds_not_moved": (
            request.funds_moved is False
        ),
        "request_portfolio_not_mutated": (
            request.portfolio_mutated is False
        ),
        "evidence_read_only": (
            evidence.read_only is True
        ),
        "evidence_fill_not_confirmed": (
            evidence.fill_confirmed is False
        ),
        "evidence_funds_not_moved": (
            evidence.funds_moved is False
        ),
        "evidence_portfolio_not_mutated": (
            evidence.portfolio_mutated is False
        ),
        "evidence_requires_engine": (
            evidence.confirmation_engine_required is True
        ),
        "confirmation_not_before_evidence": (
            datetime.fromisoformat(
                normalized_confirmed_at
            )
            >= datetime.fromisoformat(
                evidence.observed_at
            )
        ),
    }

    reason_mapping = {
        "request_ready": (
            "confirmation_request_not_ready"
        ),
        "request_requires_confirmation": (
            "fill_confirmation_requirement_missing"
        ),
        "confirmation_request_id_match": (
            "confirmation_request_id_mismatch"
        ),
        "confirmation_request_hash_match": (
            "confirmation_request_hash_mismatch"
        ),
        "reconciliation_id_match": (
            "reconciliation_id_mismatch"
        ),
        "reconciliation_hash_match": (
            "reconciliation_hash_mismatch"
        ),
        "venue_evidence_id_match": (
            "venue_evidence_id_mismatch"
        ),
        "venue_evidence_hash_match": (
            "venue_evidence_hash_mismatch"
        ),
        "result_id_match": (
            "result_id_mismatch"
        ),
        "result_hash_match": (
            "result_hash_mismatch"
        ),
        "adapter_identity_match": (
            "adapter_identity_mismatch"
        ),
        "venue_reference_match": (
            "venue_reference_mismatch"
        ),
        "request_read_only": (
            "confirmation_request_not_read_only"
        ),
        "request_execution_disabled": (
            "confirmation_execution_boundary_invalid"
        ),
        "request_fill_not_confirmed": (
            "request_fill_confirmation_already_detected"
        ),
        "request_funds_not_moved": (
            "request_fund_movement_detected"
        ),
        "request_portfolio_not_mutated": (
            "request_portfolio_mutation_detected"
        ),
        "evidence_read_only": (
            "confirmation_evidence_not_read_only"
        ),
        "evidence_fill_not_confirmed": (
            "evidence_fill_confirmation_already_detected"
        ),
        "evidence_funds_not_moved": (
            "evidence_fund_movement_detected"
        ),
        "evidence_portfolio_not_mutated": (
            "evidence_portfolio_mutation_detected"
        ),
        "evidence_requires_engine": (
            "confirmation_engine_requirement_missing"
        ),
        "confirmation_not_before_evidence": (
            "confirmation_precedes_evidence"
        ),
    }

    reason_codes = [
        reason_mapping[check_name]
        for check_name, passed in checks.items()
        if not passed
    ]

    if reason_codes:
        status = FillConfirmationStatus.BLOCKED
        confirmed_fill_type = ConfirmedFillType.NONE
        confirmed_quantity = None
        confirmed_price = None
        fill_confirmed = False
        position_state_update_required = False
        explanation = (
            "The INT-030 confirmation request and INT-031 confirmation "
            "evidence failed one or more INT-032 evidence-chain checks. "
            "Fill confirmation is blocked and no portfolio mutation occurs."
        )

    elif (
        evidence.evidence_status
        is not FillConfirmationEvidenceStatus.OBSERVED
    ):
        status = FillConfirmationStatus.UNRESOLVED
        confirmed_fill_type = ConfirmedFillType.NONE
        confirmed_quantity = None
        confirmed_price = None
        fill_confirmed = False
        position_state_update_required = False
        reason_codes = [
            "fill_confirmation_evidence_unresolved"
        ]
        explanation = (
            "Canonical fill-confirmation evidence is not observed. The "
            "reported venue fill remains unresolved and no fill is "
            "confirmed."
        )

    elif evidence.evidence_type is not expected_evidence_type:
        status = FillConfirmationStatus.BLOCKED
        confirmed_fill_type = ConfirmedFillType.NONE
        confirmed_quantity = None
        confirmed_price = None
        fill_confirmed = False
        position_state_update_required = False
        reason_codes = [
            "fill_evidence_type_mismatch"
        ]
        explanation = (
            "The INT-031 evidence type does not match the fill type "
            "reported by the INT-030 request. Fill confirmation is blocked."
        )

    elif not _decimal_values_match(
        request.reported_filled_quantity,
        evidence.observed_filled_quantity,
    ):
        status = FillConfirmationStatus.BLOCKED
        confirmed_fill_type = ConfirmedFillType.NONE
        confirmed_quantity = None
        confirmed_price = None
        fill_confirmed = False
        position_state_update_required = False
        reason_codes = [
            "filled_quantity_mismatch"
        ]
        explanation = (
            "The observed filled quantity does not match the canonical "
            "reported filled quantity. Fill confirmation is blocked."
        )

    elif not _decimal_values_match(
        request.reported_average_price,
        evidence.observed_average_price,
    ):
        status = FillConfirmationStatus.BLOCKED
        confirmed_fill_type = ConfirmedFillType.NONE
        confirmed_quantity = None
        confirmed_price = None
        fill_confirmed = False
        position_state_update_required = False
        reason_codes = [
            "average_price_mismatch"
        ]
        explanation = (
            "The observed average price does not match the canonical "
            "reported average price. Fill confirmation is blocked."
        )

    else:
        status = FillConfirmationStatus.CONFIRMED

        if (
            request.reported_fill_type
            is ReportedFillType.PARTIAL
        ):
            confirmed_fill_type = (
                ConfirmedFillType.PARTIAL
            )
            reason_codes = [
                "partial_fill_confirmed"
            ]
            explanation = (
                "Canonical INT-030 and INT-031 evidence matches for the "
                "reported partial fill. Q Series confirms the partial fill "
                "as immutable execution evidence. A later position-state "
                "boundary must process the confirmed fill."
            )
        else:
            confirmed_fill_type = (
                ConfirmedFillType.FULL
            )
            reason_codes = [
                "full_fill_confirmed"
            ]
            explanation = (
                "Canonical INT-030 and INT-031 evidence matches for the "
                "reported full fill. Q Series confirms the full fill as "
                "immutable execution evidence. A later position-state "
                "boundary must process the confirmed fill."
            )

        confirmed_quantity = (
            evidence.observed_filled_quantity
        )
        confirmed_price = (
            evidence.observed_average_price
        )
        fill_confirmed = True
        position_state_update_required = True

    frozen_details = _freeze_mapping(
        confirmation_details,
        "confirmation_details",
    )

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "confirmation_request_id": (
            request.confirmation_request_id
        ),
        "confirmation_request_hash": (
            request.request_hash
        ),
        "confirmation_evidence_id": (
            evidence.evidence_id
        ),
        "confirmation_evidence_hash": (
            evidence.evidence_hash
        ),
        "reconciliation_id": (
            request.reconciliation_id
        ),
        "reconciliation_hash": (
            request.reconciliation_hash
        ),
        "result_id": request.result_id,
        "result_hash": request.result_hash,
        "adapter_id": request.adapter_id,
        "venue_reference": (
            request.venue_reference
        ),
        "status": status.value,
        "confirmed_fill_type": (
            confirmed_fill_type.value
        ),
        "confirmed_filled_quantity": (
            confirmed_quantity
        ),
        "confirmed_average_price": (
            confirmed_price
        ),
        "confirmed_at": normalized_confirmed_at,
        "reason_codes": sorted(
            set(reason_codes)
        ),
        "checks": checks,
        "confirmation_details": _mapping_to_dict(
            frozen_details
        ),
        "fill_confirmed": fill_confirmed,
        "position_state_update_required": (
            position_state_update_required
        ),
    }

    confirmation_id = (
        "int032-"
        f"{canonical_hash(identity_payload)[:32]}"
    )

    return FillConfirmationDecision(
        confirmation_id=confirmation_id,
        confirmation_request_id=(
            request.confirmation_request_id
        ),
        confirmation_request_hash=(
            request.request_hash
        ),
        confirmation_evidence_id=(
            evidence.evidence_id
        ),
        confirmation_evidence_hash=(
            evidence.evidence_hash
        ),
        reconciliation_id=(
            request.reconciliation_id
        ),
        reconciliation_hash=(
            request.reconciliation_hash
        ),
        result_id=request.result_id,
        result_hash=request.result_hash,
        adapter_id=request.adapter_id,
        venue_reference=request.venue_reference,
        status=status,
        confirmed_fill_type=confirmed_fill_type,
        confirmed_filled_quantity=(
            confirmed_quantity
        ),
        confirmed_average_price=(
            confirmed_price
        ),
        confirmed_at=normalized_confirmed_at,
        reason_codes=tuple(reason_codes),
        explanation=explanation,
        checks=checks,
        confirmation_details=frozen_details,
        fill_confirmed=fill_confirmed,
        position_state_update_required=(
            position_state_update_required
        ),
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SOURCE_REQUEST_SCHEMA",
    "SOURCE_EVIDENCE_SCHEMA",
    "FillConfirmationEngineError",
    "FillConfirmationStatus",
    "ConfirmedFillType",
    "FillConfirmationDecision",
    "canonical_json",
    "canonical_hash",
    "confirm_fill_evidence",
]
