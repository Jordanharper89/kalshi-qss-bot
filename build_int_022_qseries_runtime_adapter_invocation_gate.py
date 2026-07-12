from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_runtime_adapter_invocation_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_int_022_qseries_runtime_adapter_invocation_gate.py"
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
    INT-022 — Q Series Runtime Adapter Invocation Gate.

    This module validates an INT-020 runtime invocation against INT-021 dry-run
    adapter evidence and produces the canonical decision required before a
    future execution-capable adapter layer may be considered.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and execution control.
    * Dry-run evidence is required before advancement.
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

    from .qseries_dry_run_runtime_adapter import (
        DryRunAdapterResponse,
        DryRunDecision,
    )
    from .qseries_runtime_adapter_interface import (
        RuntimeAdapterInvocation,
        RuntimeInvocationStatus,
        RuntimeResultStatus,
    )


    SCHEMA_VERSION = "INT-022"
    ENGINE_ID = "INT-022"
    SOURCE_INVOCATION_SCHEMA = "INT-020"
    SOURCE_DRY_RUN_SCHEMA = "INT-021"


    class RuntimeAdapterInvocationGateError(ValueError):
        """Raised when an INT-022 invocation-gate contract is invalid."""


    class RuntimeInvocationGateStatus(str, Enum):
        ELIGIBLE = "eligible"
        BLOCKED = "blocked"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RuntimeAdapterInvocationGateError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise RuntimeAdapterInvocationGateError(
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
            raise RuntimeAdapterInvocationGateError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise RuntimeAdapterInvocationGateError(
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
                raise RuntimeAdapterInvocationGateError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise RuntimeAdapterInvocationGateError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise RuntimeAdapterInvocationGateError(
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
            raise RuntimeAdapterInvocationGateError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise RuntimeAdapterInvocationGateError(
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
            raise RuntimeAdapterInvocationGateError(
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
            raise RuntimeAdapterInvocationGateError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class RuntimeAdapterInvocationGateDecision:
        """
        Immutable INT-022 runtime invocation gate decision.

        ELIGIBLE means the invocation and dry-run evidence passed the required
        checks. It does not permit execution and does not invoke an adapter.
        """

        gate_id: str
        invocation_id: str
        invocation_hash: str
        dry_run_receipt_id: str
        dry_run_receipt_hash: str
        dry_run_result_id: str
        dry_run_result_hash: str
        adapter_id: str
        status: RuntimeInvocationGateStatus
        evaluated_at: str
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
        execution_adapter_required: bool = True
        adapter_invoked: bool = False
        exchange_called: bool = False
        live_order_submitted: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        gate_hash: str = ""

        def __post_init__(self) -> None:
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
                "dry_run_receipt_id",
                _require_non_empty_string(
                    self.dry_run_receipt_id,
                    "dry_run_receipt_id",
                ),
            )
            object.__setattr__(
                self,
                "dry_run_receipt_hash",
                _require_non_empty_string(
                    self.dry_run_receipt_hash,
                    "dry_run_receipt_hash",
                ),
            )
            object.__setattr__(
                self,
                "dry_run_result_id",
                _require_non_empty_string(
                    self.dry_run_result_id,
                    "dry_run_result_id",
                ),
            )
            object.__setattr__(
                self,
                "dry_run_result_hash",
                _require_non_empty_string(
                    self.dry_run_result_hash,
                    "dry_run_result_hash",
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
                RuntimeInvocationGateStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    RuntimeInvocationGateStatus(
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
                "evidence",
                _freeze_mapping(
                    self.evidence,
                    "evidence",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise RuntimeAdapterInvocationGateError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise RuntimeAdapterInvocationGateError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise RuntimeAdapterInvocationGateError(
                    "INT-022 gate decisions must be read_only"
                )

            if self.execution_allowed is not False:
                raise RuntimeAdapterInvocationGateError(
                    "INT-022 must not directly allow execution"
                )

            if self.execution_adapter_required is not True:
                raise RuntimeAdapterInvocationGateError(
                    "INT-022 must require a later execution adapter"
                )

            forbidden_true_fields = {
                "adapter_invoked": self.adapter_invoked,
                "exchange_called": self.exchange_called,
                "live_order_submitted": self.live_order_submitted,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": self.portfolio_mutated,
            }

            for field_name, field_value in forbidden_true_fields.items():
                if field_value is not False:
                    raise RuntimeAdapterInvocationGateError(
                        f"{field_name} must remain false"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.gate_hash:
                supplied_hash = _require_non_empty_string(
                    self.gate_hash,
                    "gate_hash",
                )

                if supplied_hash != calculated_hash:
                    raise RuntimeAdapterInvocationGateError(
                        "gate_hash does not match gate contents"
                    )

            object.__setattr__(
                self,
                "gate_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "gate_id": self.gate_id,
                "invocation_id": self.invocation_id,
                "invocation_hash": self.invocation_hash,
                "dry_run_receipt_id": self.dry_run_receipt_id,
                "dry_run_receipt_hash": self.dry_run_receipt_hash,
                "dry_run_result_id": self.dry_run_result_id,
                "dry_run_result_hash": self.dry_run_result_hash,
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
                "evidence": _mapping_to_dict(
                    self.evidence
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "execution_adapter_required": (
                    self.execution_adapter_required
                ),
                "adapter_invoked": self.adapter_invoked,
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
            payload["gate_hash"] = self.gate_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def evaluate_runtime_adapter_invocation_gate(
        *,
        invocation: RuntimeAdapterInvocation,
        dry_run_response: DryRunAdapterResponse,
        evaluated_at: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> RuntimeAdapterInvocationGateDecision:
        """
        Validate INT-020 invocation and INT-021 dry-run evidence.

        The returned decision is eligibility evidence only. It does not permit
        direct execution and does not invoke an execution adapter.
        """

        if not isinstance(
            invocation,
            RuntimeAdapterInvocation,
        ):
            raise RuntimeAdapterInvocationGateError(
                "invocation must be a RuntimeAdapterInvocation"
            )

        if not isinstance(
            dry_run_response,
            DryRunAdapterResponse,
        ):
            raise RuntimeAdapterInvocationGateError(
                "dry_run_response must be a DryRunAdapterResponse"
            )

        if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
            raise RuntimeAdapterInvocationGateError(
                "invocation.schema_version must be INT-020"
            )

        receipt = dry_run_response.receipt
        result = dry_run_response.result

        if receipt.schema_version != SOURCE_DRY_RUN_SCHEMA:
            raise RuntimeAdapterInvocationGateError(
                "dry-run receipt schema_version must be INT-021"
            )

        normalized_evaluated_at = _normalize_timestamp(
            evaluated_at,
            "evaluated_at",
        )

        checks = {
            "invocation_ready": (
                invocation.status
                is RuntimeInvocationStatus.READY
            ),
            "receipt_simulated": (
                receipt.decision
                is DryRunDecision.SIMULATED
            ),
            "result_not_invoked": (
                result.status
                is RuntimeResultStatus.NOT_INVOKED
            ),
            "invocation_receipt_id_match": (
                invocation.invocation_id
                == receipt.invocation_id
            ),
            "invocation_result_id_match": (
                invocation.invocation_id
                == result.invocation_id
            ),
            "invocation_receipt_hash_match": (
                invocation.invocation_hash
                == receipt.invocation_hash
            ),
            "invocation_result_hash_match": (
                invocation.invocation_hash
                == result.invocation_hash
            ),
            "adapter_identity_match": (
                invocation.adapter_id
                == receipt.adapter_id
                == result.adapter_id
            ),
            "invocation_read_only": (
                invocation.read_only is True
            ),
            "invocation_execution_disabled": (
                invocation.execution_allowed is False
            ),
            "receipt_read_only": (
                receipt.read_only is True
            ),
            "receipt_network_disabled": (
                receipt.network_access_enabled is False
            ),
            "receipt_adapter_not_called": (
                receipt.adapter_called is False
            ),
            "receipt_exchange_not_called": (
                receipt.exchange_called is False
            ),
            "receipt_order_not_submitted": (
                receipt.live_order_submitted is False
            ),
            "receipt_funds_not_moved": (
                receipt.funds_moved is False
            ),
            "receipt_portfolio_not_mutated": (
                receipt.portfolio_mutated is False
            ),
            "result_read_only": (
                result.read_only is True
            ),
            "result_order_not_submitted": (
                result.live_order_submitted is False
            ),
            "result_funds_not_moved": (
                result.funds_moved is False
            ),
            "result_portfolio_not_mutated": (
                result.portfolio_mutated is False
            ),
            "invocation_not_expired": (
                datetime.fromisoformat(
                    normalized_evaluated_at
                )
                <= datetime.fromisoformat(
                    invocation.expires_at
                )
            ),
        }

        reason_codes: list[str] = []

        reason_mapping = {
            "invocation_ready": "invocation_not_ready",
            "receipt_simulated": "dry_run_not_simulated",
            "result_not_invoked": "dry_run_result_invalid",
            "invocation_receipt_id_match": (
                "invocation_receipt_id_mismatch"
            ),
            "invocation_result_id_match": (
                "invocation_result_id_mismatch"
            ),
            "invocation_receipt_hash_match": (
                "invocation_receipt_hash_mismatch"
            ),
            "invocation_result_hash_match": (
                "invocation_result_hash_mismatch"
            ),
            "adapter_identity_match": (
                "adapter_identity_mismatch"
            ),
            "invocation_read_only": (
                "invocation_not_read_only"
            ),
            "invocation_execution_disabled": (
                "invocation_execution_boundary_invalid"
            ),
            "receipt_read_only": (
                "receipt_not_read_only"
            ),
            "receipt_network_disabled": (
                "dry_run_network_access_detected"
            ),
            "receipt_adapter_not_called": (
                "dry_run_adapter_call_detected"
            ),
            "receipt_exchange_not_called": (
                "dry_run_exchange_call_detected"
            ),
            "receipt_order_not_submitted": (
                "dry_run_order_submission_detected"
            ),
            "receipt_funds_not_moved": (
                "dry_run_fund_movement_detected"
            ),
            "receipt_portfolio_not_mutated": (
                "dry_run_portfolio_mutation_detected"
            ),
            "result_read_only": (
                "result_not_read_only"
            ),
            "result_order_not_submitted": (
                "result_order_submission_detected"
            ),
            "result_funds_not_moved": (
                "result_fund_movement_detected"
            ),
            "result_portfolio_not_mutated": (
                "result_portfolio_mutation_detected"
            ),
            "invocation_not_expired": (
                "invocation_expired"
            ),
        }

        for check_name, passed in checks.items():
            if not passed:
                reason_codes.append(
                    reason_mapping[check_name]
                )

        if all(checks.values()):
            status = RuntimeInvocationGateStatus.ELIGIBLE
            reason_codes = [
                "runtime_invocation_eligible"
            ]
            explanation = (
                "The INT-020 runtime invocation and INT-021 dry-run evidence "
                "form a valid non-executing evidence chain. The invocation is "
                "eligible for a later execution-adapter boundary. INT-022 "
                "does not allow execution and no adapter was invoked."
            )
        else:
            status = RuntimeInvocationGateStatus.BLOCKED
            explanation = (
                "The runtime invocation or dry-run evidence failed one or "
                "more INT-022 gate checks. Advancement is blocked and no "
                "execution occurred."
            )

        frozen_evidence = _freeze_mapping(
            evidence,
            "evidence",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "invocation_id": invocation.invocation_id,
            "invocation_hash": invocation.invocation_hash,
            "dry_run_receipt_id": receipt.receipt_id,
            "dry_run_receipt_hash": receipt.receipt_hash,
            "dry_run_result_id": result.result_id,
            "dry_run_result_hash": result.result_hash,
            "adapter_id": invocation.adapter_id,
            "status": status.value,
            "evaluated_at": normalized_evaluated_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "evidence": _mapping_to_dict(
                frozen_evidence
            ),
        }

        gate_id = (
            "int022-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return RuntimeAdapterInvocationGateDecision(
            gate_id=gate_id,
            invocation_id=invocation.invocation_id,
            invocation_hash=invocation.invocation_hash,
            dry_run_receipt_id=receipt.receipt_id,
            dry_run_receipt_hash=receipt.receipt_hash,
            dry_run_result_id=result.result_id,
            dry_run_result_hash=result.result_hash,
            adapter_id=invocation.adapter_id,
            status=status,
            evaluated_at=normalized_evaluated_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            evidence=frozen_evidence,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_INVOCATION_SCHEMA",
        "SOURCE_DRY_RUN_SCHEMA",
        "RuntimeAdapterInvocationGateError",
        "RuntimeInvocationGateStatus",
        "RuntimeAdapterInvocationGateDecision",
        "canonical_json",
        "canonical_hash",
        "evaluate_runtime_adapter_invocation_gate",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError

    from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
        DryRunDecision,
        QSeriesDryRunRuntimeAdapter,
    )
    from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
        evaluate_execution_adapter_admission,
    )
    from qseries_v2.integration.qseries_execution_adapter_contract import (
        build_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_registry import (
        ExecutionAdapterRegistry,
        build_execution_adapter_registration,
        validate_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
        build_runtime_adapter_dispatch,
    )
    from qseries_v2.integration.qseries_runtime_adapter_interface import (
        RuntimeResultStatus,
        build_runtime_adapter_invocation,
    )
    from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
        ENGINE_ID,
        SCHEMA_VERSION,
        RuntimeAdapterInvocationGateError,
        RuntimeInvocationGateStatus,
        evaluate_runtime_adapter_invocation_gate,
    )


    def expect_gate_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except RuntimeAdapterInvocationGateError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected RuntimeAdapterInvocationGateError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-022",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-022",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-10T19:00:00-05:00"
            ),
        }


    def make_invocation(
        *,
        market_id: str = "KXTEST-INT022",
        invocation_expires_at: str = (
            "2026-07-10T19:08:00-05:00"
        ),
    ):
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
            market_id=market_id,
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.46",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int022"
            ),
            created_at=(
                "2026-07-10T19:00:01-05:00"
            ),
            expires_at=(
                "2026-07-10T19:10:00-05:00"
            ),
            rationale=(
                "Build INT-022 invocation gate test chain."
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
                    "2026-07-10T19:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-10T19:00:00-05:00"
                ),
                registration_reason=(
                    "INT-022 test registration."
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
                "2026-07-10T19:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T19:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T19:00:04-05:00"
            ),
            expires_at=(
                "2026-07-10T19:09:00-05:00"
            ),
        )

        return build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T19:00:05-05:00"
            ),
            expires_at=invocation_expires_at,
            invocation_context={
                "environment": "test",
                "adapter_called": False,
                "network_access_enabled": False,
            },
        )


    def make_dry_run_response(
        invocation,
        *,
        adapter_id: str = "adapter.kalshi.execution",
        simulated_at: str = (
            "2026-07-10T19:00:06-05:00"
        ),
    ):
        adapter = QSeriesDryRunRuntimeAdapter(
            adapter_id=adapter_id,
            adapter_version="1.0.0-dry-run",
        )

        return adapter.simulate(
            invocation=invocation,
            simulated_at=simulated_at,
            simulation_context={
                "environment": "test",
                "network_access_enabled": False,
            },
        )


    def test_eligible_gate_decision() -> None:
        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation
        )

        decision = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
            evidence={
                "environment": "test",
                "execution_adapter_connected": False,
                "network_access_enabled": False,
            },
        )

        assert decision.schema_version == SCHEMA_VERSION
        assert decision.engine_id == ENGINE_ID
        assert (
            decision.status
            is RuntimeInvocationGateStatus.ELIGIBLE
        )
        assert decision.reason_codes == (
            "runtime_invocation_eligible",
        )
        assert (
            decision.invocation_id
            == invocation.invocation_id
        )
        assert (
            decision.invocation_hash
            == invocation.invocation_hash
        )
        assert (
            decision.dry_run_receipt_id
            == dry_run_response.receipt.receipt_id
        )
        assert (
            decision.dry_run_receipt_hash
            == dry_run_response.receipt.receipt_hash
        )
        assert (
            decision.dry_run_result_id
            == dry_run_response.result.result_id
        )
        assert (
            decision.dry_run_result_hash
            == dry_run_response.result.result_hash
        )
        assert (
            decision.adapter_id
            == invocation.adapter_id
        )
        assert decision.read_only is True
        assert decision.execution_allowed is False
        assert (
            decision.execution_adapter_required
            is True
        )
        assert decision.adapter_invoked is False
        assert decision.exchange_called is False
        assert decision.live_order_submitted is False
        assert decision.funds_moved is False
        assert decision.portfolio_mutated is False
        assert len(decision.gate_hash) == 64


    def test_determinism() -> None:
        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation
        )

        first = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
            evidence={
                "network_access_enabled": False,
                "environment": "test",
            },
        )

        second = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
            evidence={
                "environment": "test",
                "network_access_enabled": False,
            },
        )

        assert first.gate_id == second.gate_id
        assert first.gate_hash == second.gate_hash
        assert first.to_dict() == second.to_dict()
        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation
        )

        decision = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
        )

        try:
            decision.status = (
                RuntimeInvocationGateStatus.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "gate decision must be immutable"
            )

        try:
            decision.checks[
                "invocation_ready"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "gate checks must be immutable"
            )


    def test_blocked_dry_run_evidence() -> None:
        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation,
            adapter_id="adapter.other.execution",
        )

        assert (
            dry_run_response.receipt.decision
            is DryRunDecision.BLOCKED
        )
        assert (
            dry_run_response.result.status
            is RuntimeResultStatus.REJECTED
        )

        decision = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
        )

        assert (
            decision.status
            is RuntimeInvocationGateStatus.BLOCKED
        )
        assert (
            "dry_run_not_simulated"
            in decision.reason_codes
        )
        assert (
            "dry_run_result_invalid"
            in decision.reason_codes
        )
        assert (
            "adapter_identity_mismatch"
            in decision.reason_codes
        )
        assert decision.execution_allowed is False


    def test_expired_invocation_blocked() -> None:
        invocation = make_invocation(
            invocation_expires_at=(
                "2026-07-10T19:00:07-05:00"
            )
        )

        dry_run_response = make_dry_run_response(
            invocation,
            simulated_at=(
                "2026-07-10T19:00:06-05:00"
            ),
        )

        decision = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:08-05:00"
            ),
        )

        assert (
            decision.status
            is RuntimeInvocationGateStatus.BLOCKED
        )
        assert (
            "invocation_expired"
            in decision.reason_codes
        )
        assert decision.adapter_invoked is False
        assert decision.live_order_submitted is False


    def test_timestamp_required() -> None:
        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation
        )

        expect_gate_error(
            lambda: evaluate_runtime_adapter_invocation_gate(
                invocation=invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-10T19:00:07"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_eligible_gate_decision()
        test_determinism()
        test_immutability()
        test_blocked_dry_run_evidence()
        test_expired_invocation_blocked()
        test_timestamp_required()

        invocation = make_invocation()

        dry_run_response = make_dry_run_response(
            invocation
        )

        decision = evaluate_runtime_adapter_invocation_gate(
            invocation=invocation,
            dry_run_response=dry_run_response,
            evaluated_at=(
                "2026-07-10T19:00:07-05:00"
            ),
            evidence={
                "environment": "test",
                "execution_adapter_connected": False,
                "network_access_enabled": False,
                "adapter_invoked": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "gate_status": decision.status.value,
            "adapter_id": decision.adapter_id,
            "reason_codes": list(
                decision.reason_codes
            ),
            "read_only": decision.read_only,
            "execution_allowed": (
                decision.execution_allowed
            ),
            "execution_adapter_required": (
                decision.execution_adapter_required
            ),
            "adapter_invoked": (
                decision.adapter_invoked
            ),
            "exchange_called": (
                decision.exchange_called
            ),
            "live_order_submitted": (
                decision.live_order_submitted
            ),
            "funds_moved": (
                decision.funds_moved
            ),
            "portfolio_mutated": (
                decision.portfolio_mutated
            ),
        }

        print(
            "[PASS] INT-022 Q Series "
            "Runtime Adapter Invocation Gate"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-022 Q Series Runtime Adapter Invocation Gate
    from .qseries_runtime_adapter_invocation_gate import (
        RuntimeAdapterInvocationGateDecision,
        RuntimeAdapterInvocationGateError,
        RuntimeInvocationGateStatus,
        evaluate_runtime_adapter_invocation_gate,
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
        "# INT-022 Q Series "
        "Runtime Adapter Invocation Gate"
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
    print(" INT-022 INSTALLER")
    print(" Q Series Runtime Adapter Invocation Gate")
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
    print("[DONE] INT-022 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_022_qseries_runtime_adapter_invocation_gate.py"
    )


if __name__ == "__main__":
    main()