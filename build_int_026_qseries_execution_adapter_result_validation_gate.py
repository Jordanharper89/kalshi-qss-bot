from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_execution_adapter_result_validation_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_int_026_qseries_execution_adapter_result_validation_gate.py"
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
        ENGINE_ID,
        SCHEMA_VERSION,
        ExecutionAdapterResultValidationError,
        ExecutionAdapterResultValidationStatus,
        validate_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
        evaluate_execution_adapter_safety,
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


    def expect_validation_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except ExecutionAdapterResultValidationError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected ExecutionAdapterResultValidationError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-026",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-026",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T00:00:00-05:00"
            ),
        }


    def make_chain():
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
            market_id="KXTEST-INT026",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.50",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int026"
            ),
            created_at=(
                "2026-07-11T00:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T00:10:00-05:00"
            ),
            rationale=(
                "Build INT-026 result validation test chain."
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
                    "2026-07-11T00:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T00:00:00-05:00"
                ),
                registration_reason=(
                    "INT-026 test registration."
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
                "2026-07-11T00:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T00:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T00:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T00:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T00:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T00:08:00-05:00"
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
                "2026-07-11T00:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T00:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T00:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T00:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T00:00:09-05:00"
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


    def test_not_called_result_validated() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation=(
                "INT-026 validates a canonical not-called result."
            ),
            adapter_details={
                "execution_adapter_called": False,
                "exchange_called": False,
            },
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
            evidence={
                "environment": "test",
                "result_received": True,
                "fill_reconciliation_performed": False,
            },
        )

        assert validation.schema_version == SCHEMA_VERSION
        assert validation.engine_id == ENGINE_ID

        assert (
            validation.status
            is ExecutionAdapterResultValidationStatus.VALIDATED
        )

        assert validation.reason_codes == (
            "execution_adapter_result_validated",
        )

        assert (
            validation.execution_invocation_id
            == invocation.execution_invocation_id
        )

        assert (
            validation.execution_invocation_hash
            == invocation.invocation_hash
        )

        assert (
            validation.safety_decision_id
            == safety_decision.safety_decision_id
        )

        assert (
            validation.safety_hash
            == safety_decision.safety_hash
        )

        assert validation.result_id == result.result_id
        assert validation.result_hash == result.result_hash

        assert validation.adapter_id == result.adapter_id

        assert (
            validation.result_status
            == result.status.value
        )

        assert validation.read_only is True
        assert validation.execution_allowed is False
        assert validation.fill_confirmed is False
        assert validation.funds_moved is False
        assert validation.portfolio_mutated is False

        assert (
            validation.reconciliation_required
            is True
        )

        assert len(validation.validation_hash) == 64


    def test_submission_accepted_result_validated() -> None:
        invocation, safety_decision = make_chain()

        result = build_execution_adapter_result(
            invocation=invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            adapter_reference="adapter-ref-026",
            venue_reference="venue-ref-026",
            reason_codes=(
                "venue_submission_accepted",
            ),
            explanation=(
                "Caller-supplied evidence reports submission "
                "acceptance only."
            ),
            adapter_details={
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
        )

        assert (
            validation.status
            is ExecutionAdapterResultValidationStatus.VALIDATED
        )

        assert (
            validation.result_status
            == "submission_accepted"
        )

        assert validation.fill_confirmed is False

        assert (
            validation.reconciliation_required
            is True
        )


    def test_determinism() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation=(
                "Deterministic validation result."
            ),
        )

        first = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
            evidence={
                "result_received": True,
                "environment": "test",
            },
        )

        second = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
            evidence={
                "environment": "test",
                "result_received": True,
            },
        )

        assert (
            first.validation_id
            == second.validation_id
        )

        assert (
            first.validation_hash
            == second.validation_hash
        )

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation="Immutability result.",
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
        )

        try:
            validation.status = (
                ExecutionAdapterResultValidationStatus.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "result validation must be immutable"
            )

        try:
            validation.checks[
                "adapter_identity_match"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "result validation checks must be immutable"
            )


    def test_result_precedes_invocation_blocked() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:07-05:00"
            ),
            reason_code="adapter_not_called",
            explanation=(
                "Deliberately early result."
            ),
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
        )

        assert (
            validation.status
            is ExecutionAdapterResultValidationStatus.BLOCKED
        )

        assert (
            "result_precedes_invocation"
            in validation.reason_codes
        )

        assert validation.execution_allowed is False
        assert validation.fill_confirmed is False
        assert validation.portfolio_mutated is False


    def test_validation_precedes_result_blocked() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation=(
                "Canonical result."
            ),
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:09-05:00"
            ),
        )

        assert (
            validation.status
            is ExecutionAdapterResultValidationStatus.BLOCKED
        )

        assert (
            "validation_precedes_result"
            in validation.reason_codes
        )


    def test_timestamp_required() -> None:
        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code="adapter_not_called",
            explanation="Timestamp test result.",
        )

        expect_validation_error(
            lambda: validate_execution_adapter_result(
                invocation=invocation,
                safety_decision=safety_decision,
                result=result,
                validated_at=(
                    "2026-07-11T00:00:11"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_not_called_result_validated()
        test_submission_accepted_result_validated()
        test_determinism()
        test_immutability()
        test_result_precedes_invocation_blocked()
        test_validation_precedes_result_blocked()
        test_timestamp_required()

        invocation, safety_decision = make_chain()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-11T00:00:10-05:00"
            ),
            reason_code=(
                "adapter_not_called"
            ),
            explanation=(
                "Execution adapter result validation "
                "completed without adapter invocation."
            ),
            adapter_details={
                "environment": "test",
                "execution_adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        validation = validate_execution_adapter_result(
            invocation=invocation,
            safety_decision=safety_decision,
            result=result,
            validated_at=(
                "2026-07-11T00:00:11-05:00"
            ),
            evidence={
                "environment": "test",
                "result_received": True,
                "fill_reconciliation_performed": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "validation_status": (
                validation.status.value
            ),
            "result_status": (
                validation.result_status
            ),
            "adapter_id": (
                validation.adapter_id
            ),
            "reason_codes": list(
                validation.reason_codes
            ),
            "read_only": validation.read_only,
            "execution_allowed": (
                validation.execution_allowed
            ),
            "fill_confirmed": (
                validation.fill_confirmed
            ),
            "funds_moved": (
                validation.funds_moved
            ),
            "portfolio_mutated": (
                validation.portfolio_mutated
            ),
            "reconciliation_required": (
                validation.reconciliation_required
            ),
        }

        print(
            "[PASS] INT-026 Q Series "
            "Execution Adapter Result Validation Gate"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-026 Q Series Execution Adapter Result Validation Gate
    from .qseries_execution_adapter_result_validation_gate import (
        ExecutionAdapterResultValidation,
        ExecutionAdapterResultValidationError,
        ExecutionAdapterResultValidationStatus,
        validate_execution_adapter_result,
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
        "# INT-026 Q Series "
        "Execution Adapter Result Validation Gate"
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
    print(" INT-026 INSTALLER")
    print(" Q Series Execution Adapter")
    print(" Result Validation Gate")
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
    print("[DONE] INT-026 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_026_qseries_execution_adapter_result_validation_gate.py"
    )


if __name__ == "__main__":
    main()