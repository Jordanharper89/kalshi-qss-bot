from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_fill_confirmation_evidence_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_031_qseries_fill_confirmation_evidence_contract.py"
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
    INT-031 — Q Series Fill Confirmation Evidence Contract.

    This module defines the canonical immutable evidence record consumed by a
    later fill-confirmation engine for an INT-030 confirmation request.

    INT-031 records caller-supplied confirmation evidence only.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns execution-state and fill-confirmation control.
    * Evidence must reference a canonical INT-030 confirmation request.
    * Raw venue fill observations cannot directly mutate Q Series state.
    * INT-031 does not confirm a fill.
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


    SCHEMA_VERSION = "INT-031"
    ENGINE_ID = "INT-031"
    SOURCE_REQUEST_SCHEMA = "INT-030"


    class FillConfirmationEvidenceContractError(ValueError):
        """Raised when an INT-031 confirmation evidence contract is invalid."""


    class FillConfirmationEvidenceStatus(str, Enum):
        NOT_OBSERVED = "not_observed"
        OBSERVED = "observed"
        UNAVAILABLE = "unavailable"
        FAILED = "failed"


    class FillConfirmationEvidenceType(str, Enum):
        NONE = "none"
        PARTIAL = "partial"
        FULL = "full"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise FillConfirmationEvidenceContractError(
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


    def _normalize_positive_decimal_string(
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
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be a valid decimal"
            ) from exc

        if not decimal_value.is_finite():
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be finite"
            )

        if decimal_value <= 0:
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be greater than zero"
            )

        normalized = format(
            decimal_value.normalize(),
            "f",
        )

        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")

        return normalized


    def _normalize_optional_positive_decimal_string(
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        return _normalize_positive_decimal_string(
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
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise FillConfirmationEvidenceContractError(
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
                raise FillConfirmationEvidenceContractError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise FillConfirmationEvidenceContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise FillConfirmationEvidenceContractError(
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
            raise FillConfirmationEvidenceContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise FillConfirmationEvidenceContractError(
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
            raise FillConfirmationEvidenceContractError(
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
            raise FillConfirmationEvidenceContractError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class FillConfirmationEvidence:
        """
        Immutable INT-031 fill confirmation evidence.

        OBSERVED evidence carries reported quantity and price information to a
        later confirmation engine. It does not itself confirm the fill.
        """

        evidence_id: str
        confirmation_request_id: str
        confirmation_request_hash: str
        reconciliation_id: str
        reconciliation_hash: str
        venue_evidence_id: str
        venue_evidence_hash: str
        result_id: str
        result_hash: str
        adapter_id: str
        venue_reference: str
        evidence_status: FillConfirmationEvidenceStatus
        evidence_type: FillConfirmationEvidenceType
        observed_filled_quantity: str | None
        observed_average_price: str | None
        observed_at: str
        source_updated_at: str | None
        reason_codes: tuple[str, ...]
        explanation: str
        confirmation_details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        evidence_record: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        confirmation_engine_required: bool = True
        evidence_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "evidence_id",
                _require_non_empty_string(
                    self.evidence_id,
                    "evidence_id",
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
                self.evidence_status,
                FillConfirmationEvidenceStatus,
            ):
                object.__setattr__(
                    self,
                    "evidence_status",
                    FillConfirmationEvidenceStatus(
                        str(
                            self.evidence_status
                        ).strip().lower()
                    ),
                )

            if not isinstance(
                self.evidence_type,
                FillConfirmationEvidenceType,
            ):
                object.__setattr__(
                    self,
                    "evidence_type",
                    FillConfirmationEvidenceType(
                        str(
                            self.evidence_type
                        ).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "observed_filled_quantity",
                _normalize_optional_positive_decimal_string(
                    self.observed_filled_quantity,
                    "observed_filled_quantity",
                ),
            )
            object.__setattr__(
                self,
                "observed_average_price",
                _normalize_optional_positive_decimal_string(
                    self.observed_average_price,
                    "observed_average_price",
                ),
            )
            object.__setattr__(
                self,
                "observed_at",
                _normalize_timestamp(
                    self.observed_at,
                    "observed_at",
                ),
            )

            if self.source_updated_at is not None:
                object.__setattr__(
                    self,
                    "source_updated_at",
                    _normalize_timestamp(
                        self.source_updated_at,
                        "source_updated_at",
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
                "confirmation_details",
                _freeze_mapping(
                    self.confirmation_details,
                    "confirmation_details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise FillConfirmationEvidenceContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise FillConfirmationEvidenceContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 evidence records must be read_only"
                )

            if self.evidence_record is not True:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 must identify a confirmation evidence record"
                )

            if self.fill_confirmed is not False:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 cannot report portfolio mutation"
                )

            if self.confirmation_engine_required is not True:
                raise FillConfirmationEvidenceContractError(
                    "INT-031 must require a confirmation engine"
                )

            if (
                self.evidence_status
                is FillConfirmationEvidenceStatus.OBSERVED
            ):
                if (
                    self.evidence_type
                    is FillConfirmationEvidenceType.NONE
                ):
                    raise FillConfirmationEvidenceContractError(
                        "observed evidence requires a fill evidence type"
                    )

                if self.observed_filled_quantity is None:
                    raise FillConfirmationEvidenceContractError(
                        "observed evidence requires "
                        "observed_filled_quantity"
                    )

                if self.observed_average_price is None:
                    raise FillConfirmationEvidenceContractError(
                        "observed evidence requires "
                        "observed_average_price"
                    )

            if (
                self.evidence_status
                is not FillConfirmationEvidenceStatus.OBSERVED
            ):
                if (
                    self.evidence_type
                    is not FillConfirmationEvidenceType.NONE
                ):
                    raise FillConfirmationEvidenceContractError(
                        "non-observed evidence must use evidence type none"
                    )

                if self.observed_filled_quantity is not None:
                    raise FillConfirmationEvidenceContractError(
                        "non-observed evidence must not contain "
                        "observed_filled_quantity"
                    )

                if self.observed_average_price is not None:
                    raise FillConfirmationEvidenceContractError(
                        "non-observed evidence must not contain "
                        "observed_average_price"
                    )

            if self.source_updated_at is not None:
                if (
                    datetime.fromisoformat(
                        self.source_updated_at
                    )
                    > datetime.fromisoformat(
                        self.observed_at
                    )
                ):
                    raise FillConfirmationEvidenceContractError(
                        "source_updated_at must not be later than observed_at"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.evidence_hash:
                supplied_hash = _require_non_empty_string(
                    self.evidence_hash,
                    "evidence_hash",
                )

                if supplied_hash != calculated_hash:
                    raise FillConfirmationEvidenceContractError(
                        "evidence_hash does not match evidence contents"
                    )

            object.__setattr__(
                self,
                "evidence_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "evidence_id": self.evidence_id,
                "confirmation_request_id": (
                    self.confirmation_request_id
                ),
                "confirmation_request_hash": (
                    self.confirmation_request_hash
                ),
                "reconciliation_id": self.reconciliation_id,
                "reconciliation_hash": self.reconciliation_hash,
                "venue_evidence_id": self.venue_evidence_id,
                "venue_evidence_hash": self.venue_evidence_hash,
                "result_id": self.result_id,
                "result_hash": self.result_hash,
                "adapter_id": self.adapter_id,
                "venue_reference": self.venue_reference,
                "evidence_status": self.evidence_status.value,
                "evidence_type": self.evidence_type.value,
                "observed_filled_quantity": (
                    self.observed_filled_quantity
                ),
                "observed_average_price": (
                    self.observed_average_price
                ),
                "observed_at": self.observed_at,
                "source_updated_at": self.source_updated_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "confirmation_details": _mapping_to_dict(
                    self.confirmation_details
                ),
                "read_only": self.read_only,
                "evidence_record": self.evidence_record,
                "fill_confirmed": self.fill_confirmed,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
                "confirmation_engine_required": (
                    self.confirmation_engine_required
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["evidence_hash"] = self.evidence_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def _validate_request(
        request: FillConfirmationRequest,
    ) -> None:
        if not isinstance(
            request,
            FillConfirmationRequest,
        ):
            raise FillConfirmationEvidenceContractError(
                "request must be a FillConfirmationRequest"
            )

        if request.schema_version != SOURCE_REQUEST_SCHEMA:
            raise FillConfirmationEvidenceContractError(
                "request.schema_version must be INT-030"
            )

        if (
            request.status
            is not FillConfirmationRequestStatus.READY_FOR_CONFIRMATION
        ):
            raise FillConfirmationEvidenceContractError(
                "request must be ready_for_confirmation"
            )

        if request.fill_confirmation_required is not True:
            raise FillConfirmationEvidenceContractError(
                "request must require fill confirmation"
            )

        if request.reported_fill_type is ReportedFillType.NONE:
            raise FillConfirmationEvidenceContractError(
                "request must contain a reported fill type"
            )


    def build_fill_confirmation_evidence(
        *,
        request: FillConfirmationRequest,
        evidence_status: FillConfirmationEvidenceStatus | str,
        evidence_type: FillConfirmationEvidenceType | str,
        observed_filled_quantity: str | None,
        observed_average_price: str | None,
        observed_at: str,
        source_updated_at: str | None,
        reason_codes: tuple[str, ...],
        explanation: str,
        confirmation_details: Mapping[str, Any] | None = None,
    ) -> FillConfirmationEvidence:
        """
        Build canonical INT-031 fill confirmation evidence.

        All evidence is caller supplied. No fill is confirmed here.
        """

        _validate_request(request)

        normalized_evidence_status = (
            evidence_status
            if isinstance(
                evidence_status,
                FillConfirmationEvidenceStatus,
            )
            else FillConfirmationEvidenceStatus(
                str(evidence_status).strip().lower()
            )
        )

        normalized_evidence_type = (
            evidence_type
            if isinstance(
                evidence_type,
                FillConfirmationEvidenceType,
            )
            else FillConfirmationEvidenceType(
                str(evidence_type).strip().lower()
            )
        )

        normalized_quantity = (
            _normalize_optional_positive_decimal_string(
                observed_filled_quantity,
                "observed_filled_quantity",
            )
        )

        normalized_price = (
            _normalize_optional_positive_decimal_string(
                observed_average_price,
                "observed_average_price",
            )
        )

        normalized_observed_at = _normalize_timestamp(
            observed_at,
            "observed_at",
        )

        normalized_source_updated_at = (
            None
            if source_updated_at is None
            else _normalize_timestamp(
                source_updated_at,
                "source_updated_at",
            )
        )

        normalized_reason_codes = (
            _normalize_reason_codes(
                reason_codes
            )
        )

        normalized_explanation = (
            _require_non_empty_string(
                explanation,
                "explanation",
            )
        )

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
            "reconciliation_id": request.reconciliation_id,
            "reconciliation_hash": request.reconciliation_hash,
            "venue_evidence_id": request.venue_evidence_id,
            "venue_evidence_hash": request.venue_evidence_hash,
            "result_id": request.result_id,
            "result_hash": request.result_hash,
            "adapter_id": request.adapter_id,
            "venue_reference": request.venue_reference,
            "evidence_status": normalized_evidence_status.value,
            "evidence_type": normalized_evidence_type.value,
            "observed_filled_quantity": normalized_quantity,
            "observed_average_price": normalized_price,
            "observed_at": normalized_observed_at,
            "source_updated_at": normalized_source_updated_at,
            "reason_codes": list(
                normalized_reason_codes
            ),
            "explanation": normalized_explanation,
            "confirmation_details": _mapping_to_dict(
                frozen_details
            ),
        }

        evidence_id = (
            "int031-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return FillConfirmationEvidence(
            evidence_id=evidence_id,
            confirmation_request_id=(
                request.confirmation_request_id
            ),
            confirmation_request_hash=(
                request.request_hash
            ),
            reconciliation_id=(
                request.reconciliation_id
            ),
            reconciliation_hash=(
                request.reconciliation_hash
            ),
            venue_evidence_id=(
                request.venue_evidence_id
            ),
            venue_evidence_hash=(
                request.venue_evidence_hash
            ),
            result_id=request.result_id,
            result_hash=request.result_hash,
            adapter_id=request.adapter_id,
            venue_reference=request.venue_reference,
            evidence_status=normalized_evidence_status,
            evidence_type=normalized_evidence_type,
            observed_filled_quantity=normalized_quantity,
            observed_average_price=normalized_price,
            observed_at=normalized_observed_at,
            source_updated_at=normalized_source_updated_at,
            reason_codes=normalized_reason_codes,
            explanation=normalized_explanation,
            confirmation_details=frozen_details,
        )


    def build_not_observed_fill_confirmation_evidence(
        *,
        request: FillConfirmationRequest,
        observed_at: str,
        reason_code: str,
        explanation: str,
        confirmation_details: Mapping[str, Any] | None = None,
    ) -> FillConfirmationEvidence:
        """
        Build deterministic evidence proving confirmation evidence was not
        observed.
        """

        return build_fill_confirmation_evidence(
            request=request,
            evidence_status=(
                FillConfirmationEvidenceStatus.NOT_OBSERVED
            ),
            evidence_type=FillConfirmationEvidenceType.NONE,
            observed_filled_quantity=None,
            observed_average_price=None,
            observed_at=observed_at,
            source_updated_at=None,
            reason_codes=(
                _require_non_empty_string(
                    reason_code,
                    "reason_code",
                ).lower(),
            ),
            explanation=explanation,
            confirmation_details=confirmation_details,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_REQUEST_SCHEMA",
        "FillConfirmationEvidenceContractError",
        "FillConfirmationEvidenceStatus",
        "FillConfirmationEvidenceType",
        "FillConfirmationEvidence",
        "canonical_json",
        "canonical_hash",
        "build_fill_confirmation_evidence",
        "build_not_observed_fill_confirmation_evidence",
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
    from qseries_v2.integration.qseries_fill_confirmation_evidence_contract import (
        ENGINE_ID,
        SCHEMA_VERSION,
        FillConfirmationEvidenceContractError,
        FillConfirmationEvidenceStatus,
        FillConfirmationEvidenceType,
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


    def expect_evidence_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except FillConfirmationEvidenceContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected FillConfirmationEvidenceContractError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-031",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-031",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T05:00:00-05:00"
            ),
        }


    def make_confirmation_request(
        *,
        order_state: str = "filled",
        reported_quantity: str = "2",
        reported_price: str = "0.55",
    ):
        request = build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            account_reference="account-test",
            market_id="KXTEST-INT031",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.55",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id="client-order-int031",
            created_at=(
                "2026-07-11T05:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T05:10:00-05:00"
            ),
            rationale=(
                "Build INT-031 fill confirmation evidence "
                "contract test chain."
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
                    "2026-07-11T05:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T05:00:00-05:00"
                ),
                registration_reason=(
                    "INT-031 test registration."
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
                "2026-07-11T05:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T05:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T05:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T05:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T05:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T05:08:00-05:00"
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
                "2026-07-11T05:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T05:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T05:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T05:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T05:00:09-05:00"
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
                "2026-07-11T05:00:10-05:00"
            ),
            adapter_reference="adapter-ref-031",
            venue_reference="venue-ref-031",
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
                    "2026-07-11T05:00:11-05:00"
                ),
            )
        )

        reconciliation_request = (
            build_execution_result_reconciliation_request(
                validation=result_validation,
                result=result,
                requested_at=(
                    "2026-07-11T05:00:12-05:00"
                ),
            )
        )

        venue_evidence = build_venue_reconciliation_evidence(
            request=reconciliation_request,
            evidence_status="observed",
            order_state=order_state,
            observed_at=(
                "2026-07-11T05:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T05:00:13-05:00"
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
                "2026-07-11T05:00:15-05:00"
            ),
        )

        return build_fill_confirmation_request(
            reconciliation=reconciliation,
            evidence=venue_evidence,
            requested_at=(
                "2026-07-11T05:00:16-05:00"
            ),
        )


    def test_observed_full_fill_evidence() -> None:
        request = make_confirmation_request()

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2.000",
            observed_average_price="0.5500",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Caller-supplied confirmation evidence reports "
                "a complete fill observation."
            ),
            confirmation_details={
                "source": "test",
                "fill_confirmation_performed": False,
            },
        )

        assert evidence.schema_version == SCHEMA_VERSION
        assert evidence.engine_id == ENGINE_ID

        assert (
            evidence.evidence_status
            is FillConfirmationEvidenceStatus.OBSERVED
        )

        assert (
            evidence.evidence_type
            is FillConfirmationEvidenceType.FULL
        )

        assert (
            evidence.observed_filled_quantity
            == "2"
        )

        assert (
            evidence.observed_average_price
            == "0.55"
        )

        assert (
            evidence.confirmation_request_id
            == request.confirmation_request_id
        )

        assert (
            evidence.confirmation_request_hash
            == request.request_hash
        )

        assert (
            evidence.reconciliation_id
            == request.reconciliation_id
        )

        assert (
            evidence.reconciliation_hash
            == request.reconciliation_hash
        )

        assert evidence.read_only is True
        assert evidence.evidence_record is True
        assert evidence.fill_confirmed is False
        assert evidence.funds_moved is False
        assert evidence.portfolio_mutated is False

        assert (
            evidence.confirmation_engine_required
            is True
        )

        assert len(evidence.evidence_hash) == 64


    def test_partial_fill_evidence() -> None:
        request = make_confirmation_request(
            order_state="partially_filled",
            reported_quantity="1",
            reported_price="0.54",
        )

        evidence = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="partial",
            observed_filled_quantity="1",
            observed_average_price="0.54",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "partial_fill_evidence_observed",
            ),
            explanation=(
                "Partial fill evidence observed."
            ),
        )

        assert (
            evidence.evidence_type
            is FillConfirmationEvidenceType.PARTIAL
        )

        assert (
            evidence.observed_filled_quantity
            == "1"
        )

        assert evidence.fill_confirmed is False
        assert evidence.portfolio_mutated is False


    def test_not_observed_evidence() -> None:
        request = make_confirmation_request()

        evidence = (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                reason_code=(
                    "confirmation_evidence_not_observed"
                ),
                explanation=(
                    "No independent confirmation evidence was observed."
                ),
                confirmation_details={
                    "source_queried": False,
                },
            )
        )

        assert (
            evidence.evidence_status
            is FillConfirmationEvidenceStatus.NOT_OBSERVED
        )

        assert (
            evidence.evidence_type
            is FillConfirmationEvidenceType.NONE
        )

        assert evidence.observed_filled_quantity is None
        assert evidence.observed_average_price is None
        assert evidence.source_updated_at is None
        assert evidence.fill_confirmed is False


    def test_determinism() -> None:
        request = make_confirmation_request()

        first = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2",
            observed_average_price="0.55",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Deterministic confirmation evidence."
            ),
            confirmation_details={
                "verified": False,
                "source": "test",
            },
        )

        second = build_fill_confirmation_evidence(
            request=request,
            evidence_status="observed",
            evidence_type="full",
            observed_filled_quantity="2.0",
            observed_average_price="0.550",
            observed_at=(
                "2026-07-11T05:00:18-05:00"
            ),
            source_updated_at=(
                "2026-07-11T05:00:17-05:00"
            ),
            reason_codes=(
                "fill_evidence_observed",
            ),
            explanation=(
                "Deterministic confirmation evidence."
            ),
            confirmation_details={
                "source": "test",
                "verified": False,
            },
        )

        assert first.evidence_id == second.evidence_id

        assert (
            first.evidence_hash
            == second.evidence_hash
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
                    "2026-07-11T05:00:18-05:00"
                ),
                reason_code="not_observed",
                explanation="Immutability evidence.",
                confirmation_details={
                    "source_queried": False,
                },
            )
        )

        try:
            evidence.fill_confirmed = True
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "fill confirmation evidence must be immutable"
            )

        try:
            evidence.confirmation_details[
                "source_queried"
            ] = True
        except TypeError:
            pass
        else:
            raise AssertionError(
                "confirmation details must be immutable"
            )


    def test_observed_requires_quantity() -> None:
        request = make_confirmation_request()

        expect_evidence_error(
            lambda: build_fill_confirmation_evidence(
                request=request,
                evidence_status="observed",
                evidence_type="full",
                observed_filled_quantity=None,
                observed_average_price="0.55",
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                source_updated_at=(
                    "2026-07-11T05:00:17-05:00"
                ),
                reason_codes=(
                    "fill_evidence_observed",
                ),
                explanation=(
                    "Invalid observed evidence."
                ),
            ),
            "requires observed_filled_quantity",
        )


    def test_observed_requires_price() -> None:
        request = make_confirmation_request()

        expect_evidence_error(
            lambda: build_fill_confirmation_evidence(
                request=request,
                evidence_status="observed",
                evidence_type="full",
                observed_filled_quantity="2",
                observed_average_price=None,
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                source_updated_at=(
                    "2026-07-11T05:00:17-05:00"
                ),
                reason_codes=(
                    "fill_evidence_observed",
                ),
                explanation=(
                    "Invalid observed evidence."
                ),
            ),
            "requires observed_average_price",
        )


    def test_non_observed_rejects_fill_values() -> None:
        request = make_confirmation_request()

        expect_evidence_error(
            lambda: build_fill_confirmation_evidence(
                request=request,
                evidence_status="failed",
                evidence_type="none",
                observed_filled_quantity="2",
                observed_average_price=None,
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                source_updated_at=None,
                reason_codes=(
                    "confirmation_source_failed",
                ),
                explanation=(
                    "Invalid failed evidence."
                ),
            ),
            "must not contain observed_filled_quantity",
        )


    def test_source_update_cannot_follow_observation() -> None:
        request = make_confirmation_request()

        expect_evidence_error(
            lambda: build_fill_confirmation_evidence(
                request=request,
                evidence_status="observed",
                evidence_type="full",
                observed_filled_quantity="2",
                observed_average_price="0.55",
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                source_updated_at=(
                    "2026-07-11T05:00:19-05:00"
                ),
                reason_codes=(
                    "fill_evidence_observed",
                ),
                explanation=(
                    "Invalid temporal evidence."
                ),
            ),
            "must not be later than observed_at",
        )


    def test_timestamp_required() -> None:
        request = make_confirmation_request()

        expect_evidence_error(
            lambda: (
                build_not_observed_fill_confirmation_evidence(
                    request=request,
                    observed_at=(
                        "2026-07-11T05:00:18"
                    ),
                    reason_code="not_observed",
                    explanation=(
                        "Timestamp validation evidence."
                    ),
                )
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_observed_full_fill_evidence()
        test_partial_fill_evidence()
        test_not_observed_evidence()
        test_determinism()
        test_immutability()
        test_observed_requires_quantity()
        test_observed_requires_price()
        test_non_observed_rejects_fill_values()
        test_source_update_cannot_follow_observation()
        test_timestamp_required()

        request = make_confirmation_request()

        evidence = (
            build_not_observed_fill_confirmation_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T05:00:18-05:00"
                ),
                reason_code=(
                    "confirmation_evidence_contract_only"
                ),
                explanation=(
                    "Fill confirmation evidence contract validated "
                    "without confirming a fill."
                ),
                confirmation_details={
                    "environment": "test",
                    "source_queried": False,
                    "fill_confirmation_performed": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "evidence_status": (
                evidence.evidence_status.value
            ),
            "evidence_type": (
                evidence.evidence_type.value
            ),
            "adapter_id": evidence.adapter_id,
            "reason_codes": list(
                evidence.reason_codes
            ),
            "read_only": evidence.read_only,
            "evidence_record": (
                evidence.evidence_record
            ),
            "fill_confirmed": (
                evidence.fill_confirmed
            ),
            "funds_moved": evidence.funds_moved,
            "portfolio_mutated": (
                evidence.portfolio_mutated
            ),
            "confirmation_engine_required": (
                evidence.confirmation_engine_required
            ),
        }

        print(
            "[PASS] INT-031 Q Series "
            "Fill Confirmation Evidence Contract"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-031 Q Series Fill Confirmation Evidence Contract
    from .qseries_fill_confirmation_evidence_contract import (
        FillConfirmationEvidence,
        FillConfirmationEvidenceContractError,
        FillConfirmationEvidenceStatus,
        FillConfirmationEvidenceType,
        build_fill_confirmation_evidence,
        build_not_observed_fill_confirmation_evidence,
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
        "# INT-031 Q Series "
        "Fill Confirmation Evidence Contract"
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
    print(" INT-031 INSTALLER")
    print(" Q Series Fill Confirmation")
    print(" Evidence Contract")
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
    print("[DONE] INT-031 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_031_qseries_fill_confirmation_evidence_contract.py"
    )


if __name__ == "__main__":
    main()