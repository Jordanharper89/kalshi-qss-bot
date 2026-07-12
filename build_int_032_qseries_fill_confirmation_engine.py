from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_fill_confirmation_engine.py"
)

TEST_PATH = (
    ROOT
    / "test_int_032_qseries_fill_confirmation_engine.py"
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
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError

    from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
        QSeriesDryRunRuntimeAdapter,
    )
    from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
        evaluate_execution_adapter_admission,
    )
    from qseries_v2.integration.qseries_execution_adapter_contract import (
        build_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_invocation_contract import (
        build_execution_adapter_invocation,
    )
    from qseries_v2.integration.qseries_execution_adapter_registry import (
        ExecutionAdapterRegistry,
        build_execution_adapter_registration,
        validate_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_result_contract import (
        build_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_result_validation_gate import (
        validate_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
        evaluate_execution_adapter_safety,
    )
    from qseries_v2.integration.qseries_execution_result_reconciliation_contract import (
        build_execution_result_reconciliation_request,
    )
    from qseries_v2.integration.qseries_fill_confirmation_contract import (
        build_fill_confirmation_request,
    )
    from qseries_v2.integration.qseries_fill_confirmation_engine import (
        ENGINE_ID,
        SCHEMA_VERSION,
        ConfirmedFillType,
        FillConfirmationEngineError,
        FillConfirmationStatus,
        confirm_fill_evidence,
    )
    from qseries_v2.integration.qseries_fill_confirmation_evidence_contract import (
        build_fill_confirmation_evidence,
        build_not_observed_fill_confirmation_evidence,
    )
    from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
        build_runtime_adapter_dispatch,
    )
    from qseries_v2.integration.qseries_runtime_adapter_interface import (
        build_runtime_adapter_invocation,
    )
    from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
        evaluate_runtime_adapter_invocation_gate,
    )
    from qseries_v2.integration.qseries_venue_reconciliation_evidence_contract import (
        build_venue_reconciliation_evidence,
    )
    from qseries_v2.integration.qseries_venue_reconciliation_engine import (
        reconcile_venue_evidence,
    )


    def expect_engine_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except FillConfirmationEngineError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected FillConfirmationEngineError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-032",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-032",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T06:00:00-05:00"
            ),
        }


    def make_confirmation_request(
        *,
        order_state: str = "filled",
        reported_quantity: str = "2",
        reported_price: str = "0.56",
    ):
        request = build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            account_reference="account-test",
            market_id="KXTEST-INT032",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.56",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id="client-order-int032",
            created_at=(
                "2026-07-11T06:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T06:10:00-05:00"
            ),
            rationale=(
                "Build INT-032 fill confirmation engine test chain."
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
                    "2026-07-11T06:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T06:00:00-05:00"
                ),
                registration_reason=(
                    "INT-032 test registration."
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
                "2026-07-11T06:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T06:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T06:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T06:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T06:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T06:08:00-05:00"
                ),
            )
        )

        dry_run_adapter = QSeriesDryRunRuntimeAdapter(
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            adapter_version="1.0.0-dry-run",
        )

        dry_run_response = dry_run_adapter.simulate(
            invocation=runtime_invocation,
            simulated_at=(
                "2026-07-11T06:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T06:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T06:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T06:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T06:00:09-05:00"
            ),
            safety_evidence={
                "environment": "test",
                "network_access_enabled": False,
                "execution_adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        result = build_execution_adapter_result(
            invocation=execution_invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-11T06:00:10-05:00"
            ),
            adapter_reference="adapter-ref-032",
            venue_reference="venue-ref-032",
            reason_codes=(
                "venue_submission_accepted",
            ),
            explanation=(
                "Submission acceptance evidence."
            ),
            adapter_details={
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        result_validation = (
            validate_execution_adapter_result(
                invocation=execution_invocation,
                safety_decision=safety_decision,
                result=result,
                validated_at=(
                    "2026-07-11T06:00:11-05:00"
                ),
            )
        )

        reconciliation_request = (
            build_execution_result_reconciliation_request(
                validation=result_validation,
                result=result,
                requested_at=(
                    "2026-07-11T06:00:12-05:00"
                ),
            )
        )

        venue_evidence = build_venue_reconciliation_evidence(
            request=reconciliation_request,
            evidence_status="observed",
            order_state=order_state,
            observed_at=(
                "2026-07-11T06:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T06:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                f"Venue evidence reports {order_state}."
            ),
            venue_details={
                "reported_filled_quantity": (
                    reported_quantity
                ),
                "reported_average_price": (
                    reported_price
                ),
            },
        )

        reconciliation = reconcile_venue_evidence(
            request=reconciliation_request,
            evidence=venue_evidence,
            reconciled_at=(
                "2026-07-11T06:00:15-05:00"
            ),
        )

        return build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=venue_evidence,
            requested_at=(
                "2026-07-11T06:00:16-05:00"
            ),
        )


    def test_full_fill_confirmed() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2.000",
            observed_average_price="0.5600",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Independent confirmation evidence matches "
                "the reported full fill."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
            confirmation_details={
                "environment": "test",
                "position_state_updated": False,
            },
        )

        assert decision.schema_version == SCHEMA_VERSION
        assert decision.engine_id == ENGINE_ID

        assert (
            decision.status
            is FillConfirmationStatus.CONFIRMED
        )

        assert (
            decision.confirmed_fill_type
            is ConfirmedFillType.FULL
        )

        assert (
            decision.confirmed_filled_quantity
            == "2"
        )

        assert (
            decision.confirmed_average_price
            == "0.56"
        )

        assert decision.reason_codes == (
            "full_fill_confirmed",
        )

        assert (
            decision.confirmation_request_id
            == request.confirmation_request_id
        )

        assert (
            decision.confirmation_request_hash
            == request.request_hash
        )

        assert (
            decision.confirmation_evidence_id
            == evidence.evidence_id
        )

        assert (
            decision.confirmation_evidence_hash
            == evidence.evidence_hash
        )

        assert decision.read_only is True
        assert decision.execution_allowed is False
        assert decision.fill_confirmed is True
        assert decision.funds_moved is False
        assert decision.portfolio_mutated is False

        assert (
            decision.position_state_update_required
            is True
        )

        assert len(decision.confirmation_hash) == 64


    def test_partial_fill_confirmed() -> None:
        request = make_confirmation_request(
            order_state="partially_filled",
            reported_quantity="1",
            reported_price="0.55",
        )

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="partial",
            observed_filled_quantity="1",
            observed_average_price="0.55",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "partial_fill_evidence_observed",
            ),
            explanation=(
                "Independent confirmation evidence matches "
                "the reported partial fill."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.CONFIRMED
        )

        assert (
            decision.confirmed_fill_type
            is ConfirmedFillType.PARTIAL
        )

        assert decision.reason_codes == (
            "partial_fill_confirmed",
        )

        assert decision.fill_confirmed is True

        assert (
            decision.position_state_update_required
            is True
        )

        assert decision.portfolio_mutated is False


    def test_not_observed_unresolved() -> None:
        request = make_confirmation_request()

        evidence = (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T06:00:18-05:00"
                ),
                reason_code=(
                    "confirmation_evidence_not_observed"
                ),
                explanation=(
                    "No independent confirmation evidence was observed."
                ),
            )
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.UNRESOLVED
        )

        assert (
            decision.confirmed_fill_type
            is ConfirmedFillType.NONE
        )

        assert decision.reason_codes == (
            "fill_confirmation_evidence_unresolved",
        )

        assert decision.fill_confirmed is False

        assert (
            decision.position_state_update_required
            is False
        )


    def test_fill_type_mismatch_blocked() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="partial",
            observed_filled_quantity="2",
            observed_average_price="0.56",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Mismatched evidence type."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.BLOCKED
        )

        assert (
            "fill_evidence_type_mismatch"
            in decision.reason_codes
        )

        assert decision.fill_confirmed is False
        assert decision.portfolio_mutated is False


    def test_quantity_mismatch_blocked() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="1",
            observed_average_price="0.56",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Quantity mismatch evidence."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.BLOCKED
        )

        assert (
            "filled_quantity_mismatch"
            in decision.reason_codes
        )

        assert decision.fill_confirmed is False


    def test_price_mismatch_blocked() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.57",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Price mismatch evidence."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.BLOCKED
        )

        assert (
            "average_price_mismatch"
            in decision.reason_codes
        )

        assert decision.fill_confirmed is False


    def test_determinism() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.56",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Deterministic fill confirmation evidence."
            ),
        )

        first = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
            confirmation_details={
                "position_state_updated": False,
                "environment": "test",
            },
        )

        second = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
            confirmation_details={
                "environment": "test",
                "position_state_updated": False,
            },
        )

        assert (
            first.confirmation_id
            == second.confirmation_id
        )

        assert (
            first.confirmation_hash
            == second.confirmation_hash
        )

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        request = make_confirmation_request()

        evidence = (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T06:00:18-05:00"
                ),
                reason_code="not_observed",
                explanation="Immutability evidence.",
            )
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
            confirmation_details={
                "position_state_updated": False,
            },
        )

        try:
            decision.fill_confirmed = True
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "fill confirmation decision must be immutable"
            )

        try:
            decision.confirmation_details[
                "position_state_updated"
            ] = True
        except TypeError:
            pass
        else:
            raise AssertionError(
                "confirmation details must be immutable"
            )


    def test_confirmation_precedes_evidence_blocked() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.56",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Temporal validation evidence."
            ),
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:17-05:00"
            ),
        )

        assert (
            decision.status
            is FillConfirmationStatus.BLOCKED
        )

        assert (
            "confirmation_precedes_evidence"
            in decision.reason_codes
        )

        assert decision.fill_confirmed is False


    def test_timestamp_required() -> None:
        request = make_confirmation_request()

        evidence = (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T06:00:18-05:00"
                ),
                reason_code="not_observed",
                explanation="Timestamp evidence.",
            )
        )

        expect_engine_error(
            lambda: confirm_fill_evidence(
                request=request,
                evidence=evidence,
                confirmed_at=(
                    "2026-07-11T06:00:19"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_full_fill_confirmed()
        test_partial_fill_confirmed()
        test_not_observed_unresolved()
        test_fill_type_mismatch_blocked()
        test_quantity_mismatch_blocked()
        test_price_mismatch_blocked()
        test_determinism()
        test_immutability()
        test_confirmation_precedes_evidence_blocked()
        test_timestamp_required()

        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.56",
            observed_at=(
                "2026-07-11T06:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T06:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Canonical full-fill confirmation evidence."
            ),
            confirmation_details={
                "environment": "test",
                "portfolio_mutated": False,
            },
        )

        decision = confirm_fill_evidence(
            request=request,
            evidence=evidence,
            confirmed_at=(
                "2026-07-11T06:00:19-05:00"
            ),
            confirmation_details={
                "environment": "test",
                "position_state_updated": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "confirmation_status": (
                decision.status.value
            ),
            "confirmed_fill_type": (
                decision.confirmed_fill_type.value
            ),
            "confirmed_filled_quantity": (
                decision.confirmed_filled_quantity
            ),
            "confirmed_average_price": (
                decision.confirmed_average_price
            ),
            "adapter_id": decision.adapter_id,
            "reason_codes": list(
                decision.reason_codes
            ),
            "read_only": decision.read_only,
            "execution_allowed": (
                decision.execution_allowed
            ),
            "fill_confirmed": (
                decision.fill_confirmed
            ),
            "funds_moved": decision.funds_moved,
            "portfolio_mutated": (
                decision.portfolio_mutated
            ),
            "position_state_update_required": (
                decision.position_state_update_required
            ),
        }

        print(
            "[PASS] INT-032 Q Series "
            "Fill Confirmation Engine"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-032 Q Series Fill Confirmation Engine
    from .qseries_fill_confirmation_engine import (
        ConfirmedFillType,
        FillConfirmationDecision,
        FillConfirmationEngineError,
        FillConfirmationStatus,
        confirm_fill_evidence,
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
        "# INT-032 Q Series "
        "Fill Confirmation Engine"
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
    print(" INT-032 INSTALLER")
    print(" Q Series Fill Confirmation Engine")
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
    print("[DONE] INT-032 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_032_qseries_fill_confirmation_engine.py"
    )


if __name__ == "__main__":
    main()