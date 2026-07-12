from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_fill_confirmation_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_030_qseries_fill_confirmation_contract.py"
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
    INT-030 — Q Series Fill Confirmation Contract.

    This module defines the canonical immutable request required before a later
    fill-confirmation engine may evaluate venue-reported fill evidence.

    INT-030 does not confirm fills.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns execution-state and fill-confirmation control.
    * Only canonical INT-029 reported-fill outcomes may advance.
    * Venue-reported quantities and prices remain unconfirmed evidence.
    * No exchange, broker, account, or portfolio API is called.
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

    from .qseries_venue_reconciliation_evidence_contract import (
        VenueOrderState,
        VenueReconciliationEvidence,
    )
    from .qseries_venue_reconciliation_engine import (
        VenueReconciliationDecision,
        VenueReconciliationOutcome,
        VenueReconciliationStatus,
    )


    SCHEMA_VERSION = "INT-030"
    ENGINE_ID = "INT-030"
    SOURCE_RECONCILIATION_SCHEMA = "INT-029"
    SOURCE_EVIDENCE_SCHEMA = "INT-028"


    class FillConfirmationContractError(ValueError):
        """Raised when an INT-030 fill-confirmation contract is invalid."""


    class FillConfirmationRequestStatus(str, Enum):
        READY_FOR_CONFIRMATION = "ready_for_confirmation"
        NOT_REQUIRED = "not_required"
        BLOCKED = "blocked"


    class ReportedFillType(str, Enum):
        NONE = "none"
        PARTIAL = "partial"
        FULL = "full"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise FillConfirmationContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise FillConfirmationContractError(
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
            raise FillConfirmationContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise FillConfirmationContractError(
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
                raise FillConfirmationContractError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise FillConfirmationContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise FillConfirmationContractError(
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
            raise FillConfirmationContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise FillConfirmationContractError(
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
            raise FillConfirmationContractError(
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
            raise FillConfirmationContractError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class FillConfirmationRequest:
        """
        Immutable INT-030 fill-confirmation request.

        READY_FOR_CONFIRMATION means canonical venue evidence reports a partial
        or full fill and a later confirmation engine must validate it.

        This record does not confirm the fill.
        """

        confirmation_request_id: str
        reconciliation_id: str
        reconciliation_hash: str
        venue_evidence_id: str
        venue_evidence_hash: str
        result_id: str
        result_hash: str
        adapter_id: str
        venue_reference: str
        reported_fill_type: ReportedFillType
        reported_order_state: VenueOrderState
        reported_filled_quantity: str | None
        reported_average_price: str | None
        status: FillConfirmationRequestStatus
        requested_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        confirmation_context: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        fill_confirmation_required: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        request_hash: str = ""

        def __post_init__(self) -> None:
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
                "venue_evidence_id",
                _require_non_empty_string(
                    self.venue_evidence_id,
                    "venue_evidence_id",
                ),
            )
            object.__setattr__(
                self,
                "venue_evidence_hash",
                _require_non_empty_string(
                    self.venue_evidence_hash,
                    "venue_evidence_hash",
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
                self.reported_fill_type,
                ReportedFillType,
            ):
                object.__setattr__(
                    self,
                    "reported_fill_type",
                    ReportedFillType(
                        str(
                            self.reported_fill_type
                        ).strip().lower()
                    ),
                )

            if not isinstance(
                self.reported_order_state,
                VenueOrderState,
            ):
                object.__setattr__(
                    self,
                    "reported_order_state",
                    VenueOrderState(
                        str(
                            self.reported_order_state
                        ).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "reported_filled_quantity",
                _normalize_optional_string(
                    self.reported_filled_quantity,
                    "reported_filled_quantity",
                ),
            )
            object.__setattr__(
                self,
                "reported_average_price",
                _normalize_optional_string(
                    self.reported_average_price,
                    "reported_average_price",
                ),
            )

            if not isinstance(
                self.status,
                FillConfirmationRequestStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    FillConfirmationRequestStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "requested_at",
                _normalize_timestamp(
                    self.requested_at,
                    "requested_at",
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
                "confirmation_context",
                _freeze_mapping(
                    self.confirmation_context,
                    "confirmation_context",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise FillConfirmationContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise FillConfirmationContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise FillConfirmationContractError(
                    "INT-030 confirmation requests must be read_only"
                )

            if self.execution_allowed is not False:
                raise FillConfirmationContractError(
                    "INT-030 must not directly allow execution"
                )

            if self.fill_confirmed is not False:
                raise FillConfirmationContractError(
                    "INT-030 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise FillConfirmationContractError(
                    "INT-030 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise FillConfirmationContractError(
                    "INT-030 cannot report portfolio mutation"
                )

            if (
                self.status
                is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
            ):
                if self.fill_confirmation_required is not True:
                    raise FillConfirmationContractError(
                        "ready requests must require fill confirmation"
                    )

                if self.reported_fill_type is ReportedFillType.NONE:
                    raise FillConfirmationContractError(
                        "ready requests require a reported fill type"
                    )

            if (
                self.status
                is FillConfirmationRequestStatus.NOT_REQUIRED
            ):
                if self.fill_confirmation_required is not False:
                    raise FillConfirmationContractError(
                        "not-required requests must set "
                        "fill_confirmation_required false"
                    )

                if self.reported_fill_type is not ReportedFillType.NONE:
                    raise FillConfirmationContractError(
                        "not-required requests must use fill type none"
                    )

            if self.reported_fill_type is ReportedFillType.PARTIAL:
                if (
                    self.reported_order_state
                    is not VenueOrderState.PARTIALLY_FILLED
                ):
                    raise FillConfirmationContractError(
                        "partial fill type requires partially_filled state"
                    )

            if self.reported_fill_type is ReportedFillType.FULL:
                if (
                    self.reported_order_state
                    is not VenueOrderState.FILLED
                ):
                    raise FillConfirmationContractError(
                        "full fill type requires filled state"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.request_hash:
                supplied_hash = _require_non_empty_string(
                    self.request_hash,
                    "request_hash",
                )

                if supplied_hash != calculated_hash:
                    raise FillConfirmationContractError(
                        "request_hash does not match request contents"
                    )

            object.__setattr__(
                self,
                "request_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "confirmation_request_id": (
                    self.confirmation_request_id
                ),
                "reconciliation_id": (
                    self.reconciliation_id
                ),
                "reconciliation_hash": (
                    self.reconciliation_hash
                ),
                "venue_evidence_id": (
                    self.venue_evidence_id
                ),
                "venue_evidence_hash": (
                    self.venue_evidence_hash
                ),
                "result_id": self.result_id,
                "result_hash": self.result_hash,
                "adapter_id": self.adapter_id,
                "venue_reference": (
                    self.venue_reference
                ),
                "reported_fill_type": (
                    self.reported_fill_type.value
                ),
                "reported_order_state": (
                    self.reported_order_state.value
                ),
                "reported_filled_quantity": (
                    self.reported_filled_quantity
                ),
                "reported_average_price": (
                    self.reported_average_price
                ),
                "status": self.status.value,
                "requested_at": self.requested_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "confirmation_context": _mapping_to_dict(
                    self.confirmation_context
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "fill_confirmation_required": (
                    self.fill_confirmation_required
                ),
                "fill_confirmed": self.fill_confirmed,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["request_hash"] = self.request_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def _reported_values(
        evidence: VenueReconciliationEvidence,
    ) -> tuple[str | None, str | None]:
        quantity = evidence.venue_details.get(
            "reported_filled_quantity"
        )

        price = evidence.venue_details.get(
            "reported_average_price"
        )

        normalized_quantity = (
            None
            if quantity is None
            else _require_non_empty_string(
                quantity,
                "reported_filled_quantity",
            )
        )

        normalized_price = (
            None
            if price is None
            else _require_non_empty_string(
                price,
                "reported_average_price",
            )
        )

        return (
            normalized_quantity,
            normalized_price,
        )


    def build_fill_confirmation_request(
        *,
        reconciliation: VenueReconciliationDecision,
        evidence: VenueReconciliationEvidence,
        requested_at: str,
        confirmation_context: Mapping[str, Any] | None = None,
    ) -> FillConfirmationRequest:
        """
        Build the canonical INT-030 fill-confirmation request.

        No fill is confirmed by this function.
        """

        if not isinstance(
            reconciliation,
            VenueReconciliationDecision,
        ):
            raise FillConfirmationContractError(
                "reconciliation must be a VenueReconciliationDecision"
            )

        if not isinstance(
            evidence,
            VenueReconciliationEvidence,
        ):
            raise FillConfirmationContractError(
                "evidence must be a VenueReconciliationEvidence"
            )

        if (
            reconciliation.schema_version
            != SOURCE_RECONCILIATION_SCHEMA
        ):
            raise FillConfirmationContractError(
                "reconciliation.schema_version must be INT-029"
            )

        if evidence.schema_version != SOURCE_EVIDENCE_SCHEMA:
            raise FillConfirmationContractError(
                "evidence.schema_version must be INT-028"
            )

        normalized_requested_at = _normalize_timestamp(
            requested_at,
            "requested_at",
        )

        checks = {
            "reconciliation_not_blocked": (
                reconciliation.status
                is not VenueReconciliationStatus.BLOCKED
            ),
            "reconciliation_id_match": (
                reconciliation.venue_evidence_id
                == evidence.evidence_id
            ),
            "reconciliation_hash_match": (
                reconciliation.venue_evidence_hash
                == evidence.evidence_hash
            ),
            "result_id_match": (
                reconciliation.result_id
                == evidence.result_id
            ),
            "result_hash_match": (
                reconciliation.result_hash
                == evidence.result_hash
            ),
            "adapter_identity_match": (
                reconciliation.adapter_id
                == evidence.adapter_id
            ),
            "venue_reference_match": (
                reconciliation.venue_reference
                == evidence.venue_reference
            ),
            "order_state_match": (
                reconciliation.observed_order_state
                is evidence.order_state
            ),
            "reconciliation_read_only": (
                reconciliation.read_only is True
            ),
            "reconciliation_execution_disabled": (
                reconciliation.execution_allowed is False
            ),
            "reconciliation_fill_not_confirmed": (
                reconciliation.fill_confirmed is False
            ),
            "reconciliation_funds_not_moved": (
                reconciliation.funds_moved is False
            ),
            "reconciliation_portfolio_not_mutated": (
                reconciliation.portfolio_mutated is False
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
            "request_not_before_reconciliation": (
                datetime.fromisoformat(
                    normalized_requested_at
                )
                >= datetime.fromisoformat(
                    reconciliation.reconciled_at
                )
            ),
        }

        reason_mapping = {
            "reconciliation_not_blocked": (
                "reconciliation_blocked"
            ),
            "reconciliation_id_match": (
                "venue_evidence_id_mismatch"
            ),
            "reconciliation_hash_match": (
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
            "order_state_match": (
                "order_state_mismatch"
            ),
            "reconciliation_read_only": (
                "reconciliation_not_read_only"
            ),
            "reconciliation_execution_disabled": (
                "reconciliation_execution_boundary_invalid"
            ),
            "reconciliation_fill_not_confirmed": (
                "reconciliation_fill_confirmation_detected"
            ),
            "reconciliation_funds_not_moved": (
                "reconciliation_fund_movement_detected"
            ),
            "reconciliation_portfolio_not_mutated": (
                "reconciliation_portfolio_mutation_detected"
            ),
            "evidence_read_only": (
                "venue_evidence_not_read_only"
            ),
            "evidence_fill_not_confirmed": (
                "venue_evidence_fill_confirmation_detected"
            ),
            "evidence_funds_not_moved": (
                "venue_evidence_fund_movement_detected"
            ),
            "evidence_portfolio_not_mutated": (
                "venue_evidence_portfolio_mutation_detected"
            ),
            "request_not_before_reconciliation": (
                "confirmation_request_precedes_reconciliation"
            ),
        }

        reason_codes = [
            reason_mapping[check_name]
            for check_name, passed in checks.items()
            if not passed
        ]

        reported_quantity, reported_price = (
            _reported_values(
                evidence
            )
        )

        if reason_codes:
            status = FillConfirmationRequestStatus.BLOCKED
            reported_fill_type = ReportedFillType.NONE
            fill_confirmation_required = True
            explanation = (
                "The INT-029 reconciliation decision and INT-028 venue "
                "evidence failed one or more INT-030 contract checks. Fill "
                "confirmation advancement is blocked and no Q Series fill "
                "is confirmed."
            )

        elif (
            reconciliation.outcome
            is VenueReconciliationOutcome.PARTIAL_FILL_REPORTED
        ):
            status = (
                FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
            )
            reported_fill_type = ReportedFillType.PARTIAL
            fill_confirmation_required = True
            reason_codes = [
                "partial_fill_confirmation_required"
            ]
            explanation = (
                "Canonical venue reconciliation reports a partial fill. "
                "The reported quantity and price remain unconfirmed evidence "
                "and must be validated by a later fill-confirmation engine."
            )

        elif (
            reconciliation.outcome
            is VenueReconciliationOutcome.FULL_FILL_REPORTED
        ):
            status = (
                FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
            )
            reported_fill_type = ReportedFillType.FULL
            fill_confirmation_required = True
            reason_codes = [
                "full_fill_confirmation_required"
            ]
            explanation = (
                "Canonical venue reconciliation reports a full fill. "
                "The reported quantity and price remain unconfirmed evidence "
                "and must be validated by a later fill-confirmation engine."
            )

        else:
            status = FillConfirmationRequestStatus.NOT_REQUIRED
            reported_fill_type = ReportedFillType.NONE
            fill_confirmation_required = False
            reason_codes = [
                "fill_confirmation_not_required"
            ]
            explanation = (
                "The INT-029 reconciliation outcome does not report a partial "
                "or full fill. No fill-confirmation request is required."
            )

        frozen_context = _freeze_mapping(
            confirmation_context,
            "confirmation_context",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "reconciliation_id": (
                reconciliation.reconciliation_id
            ),
            "reconciliation_hash": (
                reconciliation.reconciliation_hash
            ),
            "venue_evidence_id": (
                evidence.evidence_id
            ),
            "venue_evidence_hash": (
                evidence.evidence_hash
            ),
            "result_id": evidence.result_id,
            "result_hash": evidence.result_hash,
            "adapter_id": evidence.adapter_id,
            "venue_reference": (
                evidence.venue_reference
            ),
            "reported_fill_type": (
                reported_fill_type.value
            ),
            "reported_order_state": (
                evidence.order_state.value
            ),
            "reported_filled_quantity": (
                reported_quantity
            ),
            "reported_average_price": (
                reported_price
            ),
            "status": status.value,
            "requested_at": normalized_requested_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "confirmation_context": _mapping_to_dict(
                frozen_context
            ),
            "fill_confirmation_required": (
                fill_confirmation_required
            ),
        }

        confirmation_request_id = (
            "int030-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return FillConfirmationRequest(
            confirmation_request_id=(
                confirmation_request_id
            ),
            reconciliation_id=(
                reconciliation.reconciliation_id
            ),
            reconciliation_hash=(
                reconciliation.reconciliation_hash
            ),
            venue_evidence_id=(
                evidence.evidence_id
            ),
            venue_evidence_hash=(
                evidence.evidence_hash
            ),
            result_id=evidence.result_id,
            result_hash=evidence.result_hash,
            adapter_id=evidence.adapter_id,
            venue_reference=(
                evidence.venue_reference
            ),
            reported_fill_type=(
                reported_fill_type
            ),
            reported_order_state=(
                evidence.order_state
            ),
            reported_filled_quantity=(
                reported_quantity
            ),
            reported_average_price=(
                reported_price
            ),
            status=status,
            requested_at=normalized_requested_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            confirmation_context=frozen_context,
            fill_confirmation_required=(
                fill_confirmation_required
            ),
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_RECONCILIATION_SCHEMA",
        "SOURCE_EVIDENCE_SCHEMA",
        "FillConfirmationContractError",
        "FillConfirmationRequestStatus",
        "ReportedFillType",
        "FillConfirmationRequest",
        "canonical_json",
        "canonical_hash",
        "build_fill_confirmation_request",
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
        ENGINE_ID,
        SCHEMA_VERSION,
        FillConfirmationContractError,
        FillConfirmationRequestStatus,
        ReportedFillType,
        build_fill_confirmation_request,
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
        VenueOrderState,
        build_venue_reconciliation_evidence,
    )
    from qseries_v2.integration.qseries_venue_reconciliation_engine import (
        VenueReconciliationOutcome,
        reconcile_venue_evidence,
    )


    def expect_contract_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except FillConfirmationContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected FillConfirmationContractError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-030",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-030",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T04:00:00-05:00"
            ),
        }


    def make_reconciliation_request():
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
            market_id="KXTEST-INT030",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.54",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int030"
            ),
            created_at=(
                "2026-07-11T04:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T04:10:00-05:00"
            ),
            rationale=(
                "Build INT-030 fill confirmation contract test chain."
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
                    "2026-07-11T04:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T04:00:00-05:00"
                ),
                registration_reason=(
                    "INT-030 test registration."
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
                "2026-07-11T04:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T04:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T04:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T04:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T04:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T04:08:00-05:00"
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
                "2026-07-11T04:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T04:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T04:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T04:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T04:00:09-05:00"
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
                "2026-07-11T04:00:10-05:00"
            ),
            adapter_reference="adapter-ref-030",
            venue_reference="venue-ref-030",
            reason_codes=(
                "venue_submission_accepted",
            ),
            explanation=(
                "Caller-supplied adapter evidence reports "
                "submission acceptance only."
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
                    "2026-07-11T04:00:11-05:00"
                ),
            )
        )

        return (
            build_execution_result_reconciliation_request(
                validation=result_validation,
                result=result,
                requested_at=(
                    "2026-07-11T04:00:12-05:00"
                ),
            )
        )


    def make_reconciliation(
        *,
        order_state: str,
        venue_details: dict | None = None,
    ):
        request = make_reconciliation_request()

        evidence = build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state=order_state,
            observed_at=(
                "2026-07-11T04:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T04:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                f"Venue evidence reports {order_state}."
            ),
            venue_details=venue_details,
        )

        reconciliation = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T04:00:15-05:00"
            ),
        )

        return reconciliation, evidence


    def test_full_fill_confirmation_request() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.54",
            },
        )

        assert (
            reconciliation.outcome
            is VenueReconciliationOutcome.FULL_FILL_REPORTED
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
            confirmation_context={
                "environment": "test",
                "fill_confirmation_performed": False,
            },
        )

        assert request.schema_version == SCHEMA_VERSION
        assert request.engine_id == ENGINE_ID

        assert (
            request.status
            is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
        )

        assert (
            request.reported_fill_type
            is ReportedFillType.FULL
        )

        assert (
            request.reported_order_state
            is VenueOrderState.FILLED
        )

        assert (
            request.reported_filled_quantity
            == "2"
        )

        assert (
            request.reported_average_price
            == "0.54"
        )

        assert request.reason_codes == (
            "full_fill_confirmation_required",
        )

        assert (
            request.reconciliation_id
            == reconciliation.reconciliation_id
        )

        assert (
            request.reconciliation_hash
            == reconciliation.reconciliation_hash
        )

        assert (
            request.venue_evidence_id
            == evidence.evidence_id
        )

        assert (
            request.venue_evidence_hash
            == evidence.evidence_hash
        )

        assert request.result_id == evidence.result_id
        assert request.result_hash == evidence.result_hash

        assert request.adapter_id == evidence.adapter_id

        assert (
            request.venue_reference
            == evidence.venue_reference
        )

        assert request.read_only is True
        assert request.execution_allowed is False

        assert (
            request.fill_confirmation_required
            is True
        )

        assert request.fill_confirmed is False
        assert request.funds_moved is False
        assert request.portfolio_mutated is False

        assert len(request.request_hash) == 64


    def test_partial_fill_confirmation_request() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="partially_filled",
            venue_details={
                "reported_filled_quantity": "1",
                "reported_average_price": "0.53",
                "reported_remaining_quantity": "1",
            },
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
        )

        assert (
            request.status
            is FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
        )

        assert (
            request.reported_fill_type
            is ReportedFillType.PARTIAL
        )

        assert (
            request.reported_order_state
            is VenueOrderState.PARTIALLY_FILLED
        )

        assert (
            request.reported_filled_quantity
            == "1"
        )

        assert (
            request.reported_average_price
            == "0.53"
        )

        assert request.reason_codes == (
            "partial_fill_confirmation_required",
        )

        assert request.fill_confirmed is False


    def test_resting_order_not_required() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="resting",
            venue_details={
                "reported_filled_quantity": "0",
            },
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
        )

        assert (
            request.status
            is FillConfirmationRequestStatus.NOT_REQUIRED
        )

        assert (
            request.reported_fill_type
            is ReportedFillType.NONE
        )

        assert request.reason_codes == (
            "fill_confirmation_not_required",
        )

        assert (
            request.fill_confirmation_required
            is False
        )

        assert request.fill_confirmed is False
        assert request.portfolio_mutated is False


    def test_determinism() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_average_price": "0.54",
                "reported_filled_quantity": "2",
            },
        )

        first = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
            confirmation_context={
                "fill_confirmation_performed": False,
                "environment": "test",
            },
        )

        second = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
            confirmation_context={
                "environment": "test",
                "fill_confirmation_performed": False,
            },
        )

        assert (
            first.confirmation_request_id
            == second.confirmation_request_id
        )

        assert first.request_hash == second.request_hash

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.54",
            },
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
        )

        try:
            request.status = (
                FillConfirmationRequestStatus.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "fill confirmation request must be immutable"
            )

        try:
            request.checks[
                "result_id_match"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "fill confirmation checks must be immutable"
            )


    def test_request_precedes_reconciliation_blocked() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.54",
            },
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:14-05:00"
            ),
        )

        assert (
            request.status
            is FillConfirmationRequestStatus.BLOCKED
        )

        assert (
            "confirmation_request_precedes_reconciliation"
            in request.reason_codes
        )

        assert request.fill_confirmed is False
        assert request.funds_moved is False
        assert request.portfolio_mutated is False


    def test_timestamp_required() -> None:
        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.54",
            },
        )

        expect_contract_error(
            lambda: build_fill_confirmation_request(
                reconciliation=reconciliation,
                evidence=evidence,
                requested_at=(
                    "2026-07-11T04:00:16"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_full_fill_confirmation_request()
        test_partial_fill_confirmation_request()
        test_resting_order_not_required()
        test_determinism()
        test_immutability()
        test_request_precedes_reconciliation_blocked()
        test_timestamp_required()

        reconciliation, evidence = make_reconciliation(
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.54",
            },
        )

        request = build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=evidence,
            requested_at=(
                "2026-07-11T04:00:16-05:00"
            ),
            confirmation_context={
                "environment": "test",
                "fill_confirmation_performed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "confirmation_status": (
                request.status.value
            ),
            "reported_fill_type": (
                request.reported_fill_type.value
            ),
            "reported_order_state": (
                request.reported_order_state.value
            ),
            "reported_filled_quantity": (
                request.reported_filled_quantity
            ),
            "reported_average_price": (
                request.reported_average_price
            ),
            "adapter_id": request.adapter_id,
            "reason_codes": list(
                request.reason_codes
            ),
            "read_only": request.read_only,
            "execution_allowed": (
                request.execution_allowed
            ),
            "fill_confirmation_required": (
                request.fill_confirmation_required
            ),
            "fill_confirmed": (
                request.fill_confirmed
            ),
            "funds_moved": request.funds_moved,
            "portfolio_mutated": (
                request.portfolio_mutated
            ),
        }

        print(
            "[PASS] INT-030 Q Series "
            "Fill Confirmation Contract"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-030 Q Series Fill Confirmation Contract
    from .qseries_fill_confirmation_contract import (
        FillConfirmationContractError,
        FillConfirmationRequest,
        FillConfirmationRequestStatus,
        ReportedFillType,
        build_fill_confirmation_request,
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
        "# INT-030 Q Series "
        "Fill Confirmation Contract"
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
    print(" INT-030 INSTALLER")
    print(" Q Series Fill Confirmation Contract")
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
    print("[DONE] INT-030 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_030_qseries_fill_confirmation_contract.py"
    )


if __name__ == "__main__":
    main()