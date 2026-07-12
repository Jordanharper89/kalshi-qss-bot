from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_execution_result_reconciliation_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_027_qseries_execution_result_reconciliation_contract.py"
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
    INT-027 — Q Series Execution Result Reconciliation Contract.

    This module defines the canonical reconciliation request built from a
    validated INT-026 execution-adapter result.

    INT-027 does not perform reconciliation. It creates the immutable evidence
    envelope required by a later reconciliation engine.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns execution state control.
    * Only VALIDATED INT-026 results may create READY reconciliation requests.
    * No exchange, broker, account, or portfolio API is called.
    * No fill is confirmed.
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

    from .qseries_execution_adapter_result_contract import (
        ExecutionAdapterResult,
        ExecutionAdapterResultStatus,
    )
    from .qseries_execution_adapter_result_validation_gate import (
        ExecutionAdapterResultValidation,
        ExecutionAdapterResultValidationStatus,
    )


    SCHEMA_VERSION = "INT-027"
    ENGINE_ID = "INT-027"
    SOURCE_RESULT_SCHEMA = "INT-025"
    SOURCE_VALIDATION_SCHEMA = "INT-026"


    class ExecutionResultReconciliationContractError(ValueError):
        """Raised when an INT-027 reconciliation contract is invalid."""


    class ReconciliationRequestStatus(str, Enum):
        READY_FOR_RECONCILIATION = "ready_for_reconciliation"
        NO_RECONCILIATION_REQUIRED = "no_reconciliation_required"
        BLOCKED = "blocked"


    class ReconciliationTarget(str, Enum):
        NONE = "none"
        ADAPTER_OUTCOME = "adapter_outcome"
        VENUE_SUBMISSION = "venue_submission"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ExecutionResultReconciliationContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ExecutionResultReconciliationContractError(
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
            raise ExecutionResultReconciliationContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ExecutionResultReconciliationContractError(
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
                raise ExecutionResultReconciliationContractError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise ExecutionResultReconciliationContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise ExecutionResultReconciliationContractError(
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
            raise ExecutionResultReconciliationContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise ExecutionResultReconciliationContractError(
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
            raise ExecutionResultReconciliationContractError(
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
            raise ExecutionResultReconciliationContractError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class ExecutionResultReconciliationRequest:
        """
        Immutable INT-027 reconciliation request.

        READY_FOR_RECONCILIATION means a later reconciliation engine must
        inspect canonical venue or adapter evidence.

        This record does not confirm a fill or mutate portfolio state.
        """

        reconciliation_request_id: str
        result_validation_id: str
        result_validation_hash: str
        result_id: str
        result_hash: str
        execution_invocation_id: str
        adapter_id: str
        adapter_reference: str | None
        venue_reference: str | None
        result_status: str
        target: ReconciliationTarget
        status: ReconciliationRequestStatus
        requested_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        reconciliation_context: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        reconciliation_required: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        request_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "reconciliation_request_id",
                _require_non_empty_string(
                    self.reconciliation_request_id,
                    "reconciliation_request_id",
                ),
            )
            object.__setattr__(
                self,
                "result_validation_id",
                _require_non_empty_string(
                    self.result_validation_id,
                    "result_validation_id",
                ),
            )
            object.__setattr__(
                self,
                "result_validation_hash",
                _require_non_empty_string(
                    self.result_validation_hash,
                    "result_validation_hash",
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
                "execution_invocation_id",
                _require_non_empty_string(
                    self.execution_invocation_id,
                    "execution_invocation_id",
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
                "adapter_reference",
                _normalize_optional_string(
                    self.adapter_reference,
                    "adapter_reference",
                ),
            )
            object.__setattr__(
                self,
                "venue_reference",
                _normalize_optional_string(
                    self.venue_reference,
                    "venue_reference",
                ),
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
                self.target,
                ReconciliationTarget,
            ):
                object.__setattr__(
                    self,
                    "target",
                    ReconciliationTarget(
                        str(self.target).strip().lower()
                    ),
                )

            if not isinstance(
                self.status,
                ReconciliationRequestStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    ReconciliationRequestStatus(
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
                "reconciliation_context",
                _freeze_mapping(
                    self.reconciliation_context,
                    "reconciliation_context",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise ExecutionResultReconciliationContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise ExecutionResultReconciliationContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise ExecutionResultReconciliationContractError(
                    "INT-027 reconciliation requests must be read_only"
                )

            if self.execution_allowed is not False:
                raise ExecutionResultReconciliationContractError(
                    "INT-027 must not directly allow execution"
                )

            if self.fill_confirmed is not False:
                raise ExecutionResultReconciliationContractError(
                    "INT-027 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise ExecutionResultReconciliationContractError(
                    "INT-027 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise ExecutionResultReconciliationContractError(
                    "INT-027 cannot report portfolio mutation"
                )

            if (
                self.status
                is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
            ):
                if self.reconciliation_required is not True:
                    raise ExecutionResultReconciliationContractError(
                        "ready reconciliation requests must require "
                        "reconciliation"
                    )

                if self.target is ReconciliationTarget.NONE:
                    raise ExecutionResultReconciliationContractError(
                        "ready reconciliation requests require a target"
                    )

            if (
                self.status
                is ReconciliationRequestStatus.NO_RECONCILIATION_REQUIRED
            ):
                if self.reconciliation_required is not False:
                    raise ExecutionResultReconciliationContractError(
                        "no-reconciliation requests must set "
                        "reconciliation_required false"
                    )

                if self.target is not ReconciliationTarget.NONE:
                    raise ExecutionResultReconciliationContractError(
                        "no-reconciliation requests must target none"
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
                    raise ExecutionResultReconciliationContractError(
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
                "reconciliation_request_id": (
                    self.reconciliation_request_id
                ),
                "result_validation_id": (
                    self.result_validation_id
                ),
                "result_validation_hash": (
                    self.result_validation_hash
                ),
                "result_id": self.result_id,
                "result_hash": self.result_hash,
                "execution_invocation_id": (
                    self.execution_invocation_id
                ),
                "adapter_id": self.adapter_id,
                "adapter_reference": (
                    self.adapter_reference
                ),
                "venue_reference": (
                    self.venue_reference
                ),
                "result_status": self.result_status,
                "target": self.target.value,
                "status": self.status.value,
                "requested_at": self.requested_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "reconciliation_context": _mapping_to_dict(
                    self.reconciliation_context
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "reconciliation_required": (
                    self.reconciliation_required
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


    def build_execution_result_reconciliation_request(
        *,
        validation: ExecutionAdapterResultValidation,
        result: ExecutionAdapterResult,
        requested_at: str,
        reconciliation_context: Mapping[str, Any] | None = None,
    ) -> ExecutionResultReconciliationRequest:
        """
        Build the canonical INT-027 reconciliation request.

        This function performs contract evaluation only. It does not query a
        venue, confirm a fill, or mutate portfolio state.
        """

        if not isinstance(
            validation,
            ExecutionAdapterResultValidation,
        ):
            raise ExecutionResultReconciliationContractError(
                "validation must be an ExecutionAdapterResultValidation"
            )

        if not isinstance(
            result,
            ExecutionAdapterResult,
        ):
            raise ExecutionResultReconciliationContractError(
                "result must be an ExecutionAdapterResult"
            )

        if validation.schema_version != SOURCE_VALIDATION_SCHEMA:
            raise ExecutionResultReconciliationContractError(
                "validation.schema_version must be INT-026"
            )

        if result.schema_version != SOURCE_RESULT_SCHEMA:
            raise ExecutionResultReconciliationContractError(
                "result.schema_version must be INT-025"
            )

        normalized_requested_at = _normalize_timestamp(
            requested_at,
            "requested_at",
        )

        checks = {
            "validation_validated": (
                validation.status
                is ExecutionAdapterResultValidationStatus.VALIDATED
            ),
            "validation_requires_reconciliation": (
                validation.reconciliation_required is True
            ),
            "validation_result_id_match": (
                validation.result_id
                == result.result_id
            ),
            "validation_result_hash_match": (
                validation.result_hash
                == result.result_hash
            ),
            "execution_invocation_id_match": (
                validation.execution_invocation_id
                == result.execution_invocation_id
            ),
            "adapter_identity_match": (
                validation.adapter_id
                == result.adapter_id
            ),
            "result_status_match": (
                validation.result_status
                == result.status.value
            ),
            "validation_read_only": (
                validation.read_only is True
            ),
            "validation_execution_disabled": (
                validation.execution_allowed is False
            ),
            "validation_fill_not_confirmed": (
                validation.fill_confirmed is False
            ),
            "validation_funds_not_moved": (
                validation.funds_moved is False
            ),
            "validation_portfolio_not_mutated": (
                validation.portfolio_mutated is False
            ),
            "result_read_only": (
                result.read_only is True
            ),
            "result_fill_not_confirmed": (
                result.fill_confirmed is False
            ),
            "result_funds_not_moved": (
                result.funds_moved is False
            ),
            "result_portfolio_not_mutated": (
                result.portfolio_mutated is False
            ),
            "request_not_before_validation": (
                datetime.fromisoformat(
                    normalized_requested_at
                )
                >= datetime.fromisoformat(
                    validation.validated_at
                )
            ),
        }

        reason_mapping = {
            "validation_validated": (
                "result_validation_not_validated"
            ),
            "validation_requires_reconciliation": (
                "reconciliation_requirement_missing"
            ),
            "validation_result_id_match": (
                "validation_result_id_mismatch"
            ),
            "validation_result_hash_match": (
                "validation_result_hash_mismatch"
            ),
            "execution_invocation_id_match": (
                "execution_invocation_id_mismatch"
            ),
            "adapter_identity_match": (
                "adapter_identity_mismatch"
            ),
            "result_status_match": (
                "result_status_mismatch"
            ),
            "validation_read_only": (
                "validation_not_read_only"
            ),
            "validation_execution_disabled": (
                "validation_execution_boundary_invalid"
            ),
            "validation_fill_not_confirmed": (
                "validation_fill_confirmation_detected"
            ),
            "validation_funds_not_moved": (
                "validation_fund_movement_detected"
            ),
            "validation_portfolio_not_mutated": (
                "validation_portfolio_mutation_detected"
            ),
            "result_read_only": (
                "result_not_read_only"
            ),
            "result_fill_not_confirmed": (
                "result_fill_confirmation_detected"
            ),
            "result_funds_not_moved": (
                "result_fund_movement_detected"
            ),
            "result_portfolio_not_mutated": (
                "result_portfolio_mutation_detected"
            ),
            "request_not_before_validation": (
                "reconciliation_request_precedes_validation"
            ),
        }

        reason_codes = [
            reason_mapping[check_name]
            for check_name, passed in checks.items()
            if not passed
        ]

        if all(checks.values()):
            if (
                result.status
                is ExecutionAdapterResultStatus.SUBMISSION_ACCEPTED
            ):
                target = ReconciliationTarget.VENUE_SUBMISSION
                status = (
                    ReconciliationRequestStatus.READY_FOR_RECONCILIATION
                )
                reconciliation_required = True
                reason_codes = [
                    "venue_submission_reconciliation_required"
                ]
                explanation = (
                    "The validated INT-025 result reports submission "
                    "acceptance and contains canonical adapter and venue "
                    "references. A later reconciliation engine must inspect "
                    "venue evidence. No fill is confirmed and no portfolio "
                    "mutation occurs."
                )

            elif (
                result.status
                in {
                    ExecutionAdapterResultStatus.REJECTED,
                    ExecutionAdapterResultStatus.FAILED,
                }
            ):
                target = ReconciliationTarget.ADAPTER_OUTCOME
                status = (
                    ReconciliationRequestStatus.READY_FOR_RECONCILIATION
                )
                reconciliation_required = True
                reason_codes = [
                    "adapter_outcome_reconciliation_required"
                ]
                explanation = (
                    "The validated INT-025 result reports a rejected or failed "
                    "adapter outcome. A later reconciliation engine must record "
                    "and reconcile the terminal adapter evidence. No fill is "
                    "confirmed and no portfolio mutation occurs."
                )

            else:
                target = ReconciliationTarget.NONE
                status = (
                    ReconciliationRequestStatus.NO_RECONCILIATION_REQUIRED
                )
                reconciliation_required = False
                reason_codes = [
                    "adapter_not_called_no_reconciliation_required"
                ]
                explanation = (
                    "The validated INT-025 result proves that the execution "
                    "adapter was not called. No venue submission exists and "
                    "no reconciliation activity is required."
                )
        else:
            target = ReconciliationTarget.NONE
            status = ReconciliationRequestStatus.BLOCKED
            reconciliation_required = True
            explanation = (
                "The INT-026 validation and INT-025 result failed one or more "
                "INT-027 contract checks. Reconciliation advancement is "
                "blocked and no portfolio mutation occurs."
            )

        frozen_context = _freeze_mapping(
            reconciliation_context,
            "reconciliation_context",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "result_validation_id": (
                validation.validation_id
            ),
            "result_validation_hash": (
                validation.validation_hash
            ),
            "result_id": result.result_id,
            "result_hash": result.result_hash,
            "execution_invocation_id": (
                result.execution_invocation_id
            ),
            "adapter_id": result.adapter_id,
            "adapter_reference": (
                result.adapter_reference
            ),
            "venue_reference": (
                result.venue_reference
            ),
            "result_status": result.status.value,
            "target": target.value,
            "status": status.value,
            "requested_at": normalized_requested_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "reconciliation_context": _mapping_to_dict(
                frozen_context
            ),
            "reconciliation_required": (
                reconciliation_required
            ),
        }

        reconciliation_request_id = (
            "int027-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return ExecutionResultReconciliationRequest(
            reconciliation_request_id=(
                reconciliation_request_id
            ),
            result_validation_id=(
                validation.validation_id
            ),
            result_validation_hash=(
                validation.validation_hash
            ),
            result_id=result.result_id,
            result_hash=result.result_hash,
            execution_invocation_id=(
                result.execution_invocation_id
            ),
            adapter_id=result.adapter_id,
            adapter_reference=(
                result.adapter_reference
            ),
            venue_reference=(
                result.venue_reference
            ),
            result_status=result.status.value,
            target=target,
            status=status,
            requested_at=normalized_requested_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            reconciliation_context=frozen_context,
            reconciliation_required=(
                reconciliation_required
            ),
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_RESULT_SCHEMA",
        "SOURCE_VALIDATION_SCHEMA",
        "ExecutionResultReconciliationContractError",
        "ReconciliationRequestStatus",
        "ReconciliationTarget",
        "ExecutionResultReconciliationRequest",
        "canonical_json",
        "canonical_hash",
        "build_execution_result_reconciliation_request",
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
        build_not_called_execution_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_result_validation_gate import (
        validate_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
        evaluate_execution_adapter_safety,
    )
    from qseries_v2.integration.qseries_execution_result_reconciliation_contract import (
        ENGINE_ID,
        SCHEMA_VERSION,
        ExecutionResultReconciliationContractError,
        ReconciliationRequestStatus,
        ReconciliationTarget,
        build_execution_result_reconciliation_request,
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


    def expect_contract_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except ExecutionResultReconciliationContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected ExecutionResultReconciliationContractError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-027",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-027",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T01:00:00-05:00"
            ),
        }


    def make_execution_chain():
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
            market_id="KXTEST-INT027",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.51",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int027"
            ),
            created_at=(
                "2026-07-11T01:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T01:10:00-05:00"
            ),
            rationale=(
                "Build INT-027 reconciliation contract test chain."
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
                    "2026-07-11T01:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T01:00:00-05:00"
                ),
                registration_reason=(
                    "INT-027 test registration."
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
                "2026-07-11T01:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T01:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T01:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T01:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T01:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T01:08:00-05:00"
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
                "2026-07-11T01:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T01:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T01:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T01:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T01:00:09-05:00"
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

        return execution_invocation, safety_decision


    def make_validated_result(
        *,
        result_status: str,
    ):
        invocation, safety_decision = (
            make_execution_chain()
        )

        if result_status == "not_called":
            result = build_not_called_execution_result(
                invocation=invocation,
                completed_at=(
                    "2026-07-11T01:00:10-05:00"
                ),
                reason_code="adapter_not_called",
                explanation=(
                    "Adapter was not called."
                ),
                adapter_details={
                    "execution_adapter_called": False,
                    "exchange_called": False,
                },
            )

        elif result_status == "submission_accepted":
            result = build_execution_adapter_result(
                invocation=invocation,
                status="submission_accepted",
                completed_at=(
                    "2026-07-11T01:00:10-05:00"
                ),
                adapter_reference="adapter-ref-027",
                venue_reference="venue-ref-027",
                reason_codes=(
                    "venue_submission_accepted",
                ),
                explanation=(
                    "Submission accepted evidence."
                ),
                adapter_details={
                    "fill_confirmed": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )

        elif result_status == "rejected":
            result = build_execution_adapter_result(
                invocation=invocation,
                status="rejected",
                completed_at=(
                    "2026-07-11T01:00:10-05:00"
                ),
                adapter_reference="adapter-ref-rejected-027",
                venue_reference=None,
                reason_codes=(
                    "adapter_rejected_submission",
                ),
                explanation=(
                    "Adapter rejected submission."
                ),
                adapter_details={
                    "fill_confirmed": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )

        else:
            raise AssertionError(
                f"unsupported test result status: {result_status}"
            )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T01:00:11-05:00"
            ),
        )

        return validation, result


    def test_submission_reconciliation_request() -> None:
        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
                reconciliation_context={
                    "environment": "test",
                    "venue_query_performed": False,
                    "fill_confirmed": False,
                },
            )
        )

        assert request.schema_version == SCHEMA_VERSION
        assert request.engine_id == ENGINE_ID

        assert (
            request.status
            is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
        )

        assert (
            request.target
            is ReconciliationTarget.VENUE_SUBMISSION
        )

        assert request.reason_codes == (
            "venue_submission_reconciliation_required",
        )

        assert (
            request.result_validation_id
            == validation.validation_id
        )

        assert (
            request.result_validation_hash
            == validation.validation_hash
        )

        assert request.result_id == result.result_id
        assert request.result_hash == result.result_hash

        assert (
            request.execution_invocation_id
            == result.execution_invocation_id
        )

        assert request.adapter_id == result.adapter_id

        assert (
            request.adapter_reference
            == result.adapter_reference
        )

        assert (
            request.venue_reference
            == result.venue_reference
        )

        assert request.read_only is True
        assert request.execution_allowed is False

        assert (
            request.reconciliation_required
            is True
        )

        assert request.fill_confirmed is False
        assert request.funds_moved is False
        assert request.portfolio_mutated is False

        assert len(request.request_hash) == 64


    def test_not_called_requires_no_reconciliation() -> None:
        validation, result = make_validated_result(
            result_status="not_called"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
            )
        )

        assert (
            request.status
            is ReconciliationRequestStatus.NO_RECONCILIATION_REQUIRED
        )

        assert (
            request.target
            is ReconciliationTarget.NONE
        )

        assert request.reason_codes == (
            "adapter_not_called_no_reconciliation_required",
        )

        assert (
            request.reconciliation_required
            is False
        )

        assert request.fill_confirmed is False
        assert request.portfolio_mutated is False


    def test_rejected_result_reconciliation_request() -> None:
        validation, result = make_validated_result(
            result_status="rejected"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
            )
        )

        assert (
            request.status
            is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
        )

        assert (
            request.target
            is ReconciliationTarget.ADAPTER_OUTCOME
        )

        assert request.reason_codes == (
            "adapter_outcome_reconciliation_required",
        )

        assert (
            request.reconciliation_required
            is True
        )

        assert request.fill_confirmed is False


    def test_determinism() -> None:
        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        first = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
                reconciliation_context={
                    "fill_confirmed": False,
                    "environment": "test",
                },
            )
        )

        second = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
                reconciliation_context={
                    "environment": "test",
                    "fill_confirmed": False,
                },
            )
        )

        assert (
            first.reconciliation_request_id
            == second.reconciliation_request_id
        )

        assert (
            first.request_hash
            == second.request_hash
        )

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
            )
        )

        try:
            request.status = (
                ReconciliationRequestStatus.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "reconciliation request must be immutable"
            )

        try:
            request.checks[
                "validation_validated"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "reconciliation checks must be immutable"
            )


    def test_request_precedes_validation_blocked() -> None:
        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:10-05:00"
                ),
            )
        )

        assert (
            request.status
            is ReconciliationRequestStatus.BLOCKED
        )

        assert (
            "reconciliation_request_precedes_validation"
            in request.reason_codes
        )

        assert request.execution_allowed is False
        assert request.fill_confirmed is False
        assert request.portfolio_mutated is False


    def test_timestamp_required() -> None:
        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        expect_contract_error(
            lambda: (
                build_execution_result_reconciliation_request(
                    validation=validation,
                    result=result,
                    requested_at=(
                        "2026-07-11T01:00:12"
                    ),
                )
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_submission_reconciliation_request()
        test_not_called_requires_no_reconciliation()
        test_rejected_result_reconciliation_request()
        test_determinism()
        test_immutability()
        test_request_precedes_validation_blocked()
        test_timestamp_required()

        validation, result = make_validated_result(
            result_status="submission_accepted"
        )

        request = (
            build_execution_result_reconciliation_request(
                validation=validation,
                result=result,
                requested_at=(
                    "2026-07-11T01:00:12-05:00"
                ),
                reconciliation_context={
                    "environment": "test",
                    "venue_query_performed": False,
                    "fill_confirmed": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "reconciliation_status": (
                request.status.value
            ),
            "target": request.target.value,
            "result_status": request.result_status,
            "adapter_id": request.adapter_id,
            "reason_codes": list(
                request.reason_codes
            ),
            "read_only": request.read_only,
            "execution_allowed": (
                request.execution_allowed
            ),
            "reconciliation_required": (
                request.reconciliation_required
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
            "[PASS] INT-027 Q Series "
            "Execution Result Reconciliation Contract"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-027 Q Series Execution Result Reconciliation Contract
    from .qseries_execution_result_reconciliation_contract import (
        ExecutionResultReconciliationContractError,
        ExecutionResultReconciliationRequest,
        ReconciliationRequestStatus,
        ReconciliationTarget,
        build_execution_result_reconciliation_request,
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
        "# INT-027 Q Series "
        "Execution Result Reconciliation Contract"
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
    print(" INT-027 INSTALLER")
    print(" Q Series Execution Result")
    print(" Reconciliation Contract")
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
    print("[DONE] INT-027 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_027_qseries_execution_result_reconciliation_contract.py"
    )


if __name__ == "__main__":
    main()