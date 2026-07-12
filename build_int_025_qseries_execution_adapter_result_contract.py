from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_execution_adapter_result_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_025_qseries_execution_adapter_result_contract.py"
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
    INT-025 — Q Series Execution Adapter Result Contract.

    This module defines the canonical result envelope that a future concrete
    execution-capable adapter must return after receiving an INT-023 execution
    adapter invocation.

    INT-025 does not invoke an adapter and does not execute an order.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and execution control.
    * Adapter results must reference a canonical INT-023 invocation.
    * Result records are immutable.
    * All timestamps are caller supplied.
    * All records are deterministic, replayable, auditable, and explainable.
    * All hashing uses canonical JSON and never repr().
    * This module performs no network, exchange, fund, or portfolio mutation.
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
    )


    SCHEMA_VERSION = "INT-025"
    ENGINE_ID = "INT-025"
    SOURCE_INVOCATION_SCHEMA = "INT-023"


    class ExecutionAdapterResultContractError(ValueError):
        """Raised when an INT-025 execution-adapter result is invalid."""


    class ExecutionAdapterResultStatus(str, Enum):
        NOT_CALLED = "not_called"
        REJECTED = "rejected"
        FAILED = "failed"
        SUBMISSION_ACCEPTED = "submission_accepted"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ExecutionAdapterResultContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ExecutionAdapterResultContractError(
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
            raise ExecutionAdapterResultContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ExecutionAdapterResultContractError(
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
                raise ExecutionAdapterResultContractError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise ExecutionAdapterResultContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise ExecutionAdapterResultContractError(
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
            raise ExecutionAdapterResultContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise ExecutionAdapterResultContractError(
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
            raise ExecutionAdapterResultContractError(
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
            raise ExecutionAdapterResultContractError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class ExecutionAdapterResult:
        """
        Immutable canonical result returned by an execution-capable adapter.

        SUBMISSION_ACCEPTED means only that a concrete adapter reports that a
        venue accepted a submission request. It does not represent a fill,
        position mutation, settlement, or portfolio state change.
        """

        result_id: str
        execution_invocation_id: str
        execution_invocation_hash: str
        adapter_id: str
        status: ExecutionAdapterResultStatus
        completed_at: str
        adapter_reference: str | None
        venue_reference: str | None
        reason_codes: tuple[str, ...]
        explanation: str
        adapter_details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_result_record: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        result_hash: str = ""

        def __post_init__(self) -> None:
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
                ExecutionAdapterResultStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    ExecutionAdapterResultStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "completed_at",
                _normalize_timestamp(
                    self.completed_at,
                    "completed_at",
                ),
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
                "adapter_details",
                _freeze_mapping(
                    self.adapter_details,
                    "adapter_details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise ExecutionAdapterResultContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise ExecutionAdapterResultContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise ExecutionAdapterResultContractError(
                    "INT-025 result records must be read_only"
                )

            if self.execution_result_record is not True:
                raise ExecutionAdapterResultContractError(
                    "INT-025 must identify an execution result record"
                )

            if self.fill_confirmed is not False:
                raise ExecutionAdapterResultContractError(
                    "INT-025 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise ExecutionAdapterResultContractError(
                    "INT-025 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise ExecutionAdapterResultContractError(
                    "INT-025 cannot report portfolio mutation"
                )

            if (
                self.status
                is ExecutionAdapterResultStatus.NOT_CALLED
            ):
                if self.adapter_reference is not None:
                    raise ExecutionAdapterResultContractError(
                        "not_called results must not contain "
                        "adapter_reference"
                    )

                if self.venue_reference is not None:
                    raise ExecutionAdapterResultContractError(
                        "not_called results must not contain "
                        "venue_reference"
                    )

            if (
                self.status
                in {
                    ExecutionAdapterResultStatus.REJECTED,
                    ExecutionAdapterResultStatus.FAILED,
                }
                and self.venue_reference is not None
            ):
                raise ExecutionAdapterResultContractError(
                    "rejected or failed results must not contain "
                    "venue_reference"
                )

            if (
                self.status
                is ExecutionAdapterResultStatus.SUBMISSION_ACCEPTED
            ):
                if self.adapter_reference is None:
                    raise ExecutionAdapterResultContractError(
                        "submission_accepted results require "
                        "adapter_reference"
                    )

                if self.venue_reference is None:
                    raise ExecutionAdapterResultContractError(
                        "submission_accepted results require "
                        "venue_reference"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.result_hash:
                supplied_hash = _require_non_empty_string(
                    self.result_hash,
                    "result_hash",
                )

                if supplied_hash != calculated_hash:
                    raise ExecutionAdapterResultContractError(
                        "result_hash does not match result contents"
                    )

            object.__setattr__(
                self,
                "result_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "result_id": self.result_id,
                "execution_invocation_id": (
                    self.execution_invocation_id
                ),
                "execution_invocation_hash": (
                    self.execution_invocation_hash
                ),
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "completed_at": self.completed_at,
                "adapter_reference": (
                    self.adapter_reference
                ),
                "venue_reference": (
                    self.venue_reference
                ),
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "adapter_details": _mapping_to_dict(
                    self.adapter_details
                ),
                "read_only": self.read_only,
                "execution_result_record": (
                    self.execution_result_record
                ),
                "fill_confirmed": self.fill_confirmed,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["result_hash"] = self.result_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def _validate_invocation(
        invocation: ExecutionAdapterInvocation,
    ) -> None:
        if not isinstance(
            invocation,
            ExecutionAdapterInvocation,
        ):
            raise ExecutionAdapterResultContractError(
                "invocation must be an ExecutionAdapterInvocation"
            )

        if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
            raise ExecutionAdapterResultContractError(
                "invocation.schema_version must be INT-023"
            )


    def build_execution_adapter_result(
        *,
        invocation: ExecutionAdapterInvocation,
        status: ExecutionAdapterResultStatus | str,
        completed_at: str,
        adapter_reference: str | None,
        venue_reference: str | None,
        reason_codes: tuple[str, ...],
        explanation: str,
        adapter_details: Mapping[str, Any] | None = None,
    ) -> ExecutionAdapterResult:
        """
        Build a canonical execution-adapter result.

        This function records caller-supplied adapter outcome evidence only.
        It invokes no adapter and performs no execution.
        """

        _validate_invocation(invocation)

        normalized_status = (
            status
            if isinstance(
                status,
                ExecutionAdapterResultStatus,
            )
            else ExecutionAdapterResultStatus(
                str(status).strip().lower()
            )
        )

        normalized_completed_at = _normalize_timestamp(
            completed_at,
            "completed_at",
        )

        normalized_adapter_reference = (
            _normalize_optional_string(
                adapter_reference,
                "adapter_reference",
            )
        )

        normalized_venue_reference = (
            _normalize_optional_string(
                venue_reference,
                "venue_reference",
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
            adapter_details,
            "adapter_details",
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
            "status": normalized_status.value,
            "completed_at": normalized_completed_at,
            "adapter_reference": (
                normalized_adapter_reference
            ),
            "venue_reference": (
                normalized_venue_reference
            ),
            "reason_codes": list(
                normalized_reason_codes
            ),
            "explanation": normalized_explanation,
            "adapter_details": _mapping_to_dict(
                frozen_details
            ),
        }

        result_id = (
            "int025-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return ExecutionAdapterResult(
            result_id=result_id,
            execution_invocation_id=(
                invocation.execution_invocation_id
            ),
            execution_invocation_hash=(
                invocation.invocation_hash
            ),
            adapter_id=invocation.adapter_id,
            status=normalized_status,
            completed_at=normalized_completed_at,
            adapter_reference=(
                normalized_adapter_reference
            ),
            venue_reference=(
                normalized_venue_reference
            ),
            reason_codes=(
                normalized_reason_codes
            ),
            explanation=normalized_explanation,
            adapter_details=frozen_details,
            fill_confirmed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


    def build_not_called_execution_result(
        *,
        invocation: ExecutionAdapterInvocation,
        completed_at: str,
        reason_code: str,
        explanation: str,
        adapter_details: Mapping[str, Any] | None = None,
    ) -> ExecutionAdapterResult:
        """
        Build deterministic evidence proving no execution adapter was called.
        """

        return build_execution_adapter_result(
            invocation=invocation,
            status=ExecutionAdapterResultStatus.NOT_CALLED,
            completed_at=completed_at,
            adapter_reference=None,
            venue_reference=None,
            reason_codes=(
                _require_non_empty_string(
                    reason_code,
                    "reason_code",
                ).lower(),
            ),
            explanation=explanation,
            adapter_details=adapter_details,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_INVOCATION_SCHEMA",
        "ExecutionAdapterResultContractError",
        "ExecutionAdapterResultStatus",
        "ExecutionAdapterResult",
        "canonical_json",
        "canonical_hash",
        "build_execution_adapter_result",
        "build_not_called_execution_result",
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
        ENGINE_ID,
        SCHEMA_VERSION,
        ExecutionAdapterResultContractError,
        ExecutionAdapterResultStatus,
        build_execution_adapter_result,
        build_not_called_execution_result,
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


    def expect_result_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except ExecutionAdapterResultContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected ExecutionAdapterResultContractError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-025",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-025",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-10T23:00:00-05:00"
            ),
        }


    def make_execution_invocation():
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
            market_id="KXTEST-INT025",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.49",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int025"
            ),
            created_at=(
                "2026-07-10T23:00:01-05:00"
            ),
            expires_at=(
                "2026-07-10T23:10:00-05:00"
            ),
            rationale=(
                "Build INT-025 result contract test chain."
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
                    "2026-07-10T23:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-10T23:00:00-05:00"
                ),
                registration_reason=(
                    "INT-025 test registration."
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
                "2026-07-10T23:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T23:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T23:00:04-05:00"
            ),
            expires_at=(
                "2026-07-10T23:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-10T23:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-10T23:08:00-05:00"
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
                "2026-07-10T23:00:06-05:00"
            ),
        )

        gate_decision = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-10T23:00:07-05:00"
                ),
            )
        )

        return build_execution_adapter_invocation(
            runtime_invocation=runtime_invocation,
            gate_decision=gate_decision,
            prepared_at=(
                "2026-07-10T23:00:08-05:00"
            ),
            expires_at=(
                "2026-07-10T23:07:00-05:00"
            ),
        )


    def test_not_called_result() -> None:
        invocation = make_execution_invocation()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            reason_code=(
                "result_contract_only"
            ),
            explanation=(
                "INT-025 validated the adapter result contract "
                "without calling an execution adapter."
            ),
            adapter_details={
                "environment": "test",
                "execution_adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
            },
        )

        assert result.schema_version == SCHEMA_VERSION
        assert result.engine_id == ENGINE_ID

        assert (
            result.status
            is ExecutionAdapterResultStatus.NOT_CALLED
        )

        assert result.reason_codes == (
            "result_contract_only",
        )

        assert (
            result.execution_invocation_id
            == invocation.execution_invocation_id
        )

        assert (
            result.execution_invocation_hash
            == invocation.invocation_hash
        )

        assert (
            result.adapter_id
            == invocation.adapter_id
        )

        assert result.adapter_reference is None
        assert result.venue_reference is None
        assert result.read_only is True

        assert (
            result.execution_result_record
            is True
        )

        assert result.fill_confirmed is False
        assert result.funds_moved is False
        assert result.portfolio_mutated is False

        assert len(result.result_hash) == 64


    def test_submission_accepted_contract() -> None:
        invocation = make_execution_invocation()

        result = build_execution_adapter_result(
            invocation=invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            adapter_reference=(
                "adapter-ref-025"
            ),
            venue_reference=(
                "venue-ref-025"
            ),
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

        assert (
            result.status
            is ExecutionAdapterResultStatus.SUBMISSION_ACCEPTED
        )

        assert (
            result.adapter_reference
            == "adapter-ref-025"
        )

        assert (
            result.venue_reference
            == "venue-ref-025"
        )

        assert result.fill_confirmed is False
        assert result.funds_moved is False
        assert result.portfolio_mutated is False


    def test_determinism() -> None:
        invocation = make_execution_invocation()

        first = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            reason_code=(
                "result_contract_only"
            ),
            explanation=(
                "Deterministic INT-025 result."
            ),
            adapter_details={
                "exchange_called": False,
                "execution_adapter_called": False,
            },
        )

        second = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            reason_code=(
                "result_contract_only"
            ),
            explanation=(
                "Deterministic INT-025 result."
            ),
            adapter_details={
                "execution_adapter_called": False,
                "exchange_called": False,
            },
        )

        assert first.result_id == second.result_id
        assert first.result_hash == second.result_hash
        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        invocation = make_execution_invocation()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            reason_code="not_called",
            explanation=(
                "Immutability test result."
            ),
            adapter_details={
                "exchange_called": False,
            },
        )

        try:
            result.status = (
                ExecutionAdapterResultStatus.FAILED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "execution adapter result must be immutable"
            )

        try:
            result.adapter_details[
                "exchange_called"
            ] = True
        except TypeError:
            pass
        else:
            raise AssertionError(
                "adapter details must be immutable"
            )


    def test_accepted_requires_references() -> None:
        invocation = make_execution_invocation()

        expect_result_error(
            lambda: build_execution_adapter_result(
                invocation=invocation,
                status="submission_accepted",
                completed_at=(
                    "2026-07-10T23:00:09-05:00"
                ),
                adapter_reference=None,
                venue_reference=None,
                reason_codes=(
                    "accepted",
                ),
                explanation=(
                    "Invalid accepted result."
                ),
            ),
            "require adapter_reference",
        )


    def test_not_called_rejects_references() -> None:
        invocation = make_execution_invocation()

        expect_result_error(
            lambda: build_execution_adapter_result(
                invocation=invocation,
                status="not_called",
                completed_at=(
                    "2026-07-10T23:00:09-05:00"
                ),
                adapter_reference=(
                    "adapter-ref-invalid"
                ),
                venue_reference=None,
                reason_codes=(
                    "not_called",
                ),
                explanation=(
                    "Invalid not-called result."
                ),
            ),
            "must not contain adapter_reference",
        )


    def test_timestamp_required() -> None:
        invocation = make_execution_invocation()

        expect_result_error(
            lambda: build_not_called_execution_result(
                invocation=invocation,
                completed_at=(
                    "2026-07-10T23:00:09"
                ),
                reason_code="not_called",
                explanation=(
                    "Timestamp validation test."
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_not_called_result()
        test_submission_accepted_contract()
        test_determinism()
        test_immutability()
        test_accepted_requires_references()
        test_not_called_rejects_references()
        test_timestamp_required()

        invocation = make_execution_invocation()

        result = build_not_called_execution_result(
            invocation=invocation,
            completed_at=(
                "2026-07-10T23:00:09-05:00"
            ),
            reason_code=(
                "result_contract_only"
            ),
            explanation=(
                "Execution adapter result contract validated "
                "without adapter invocation."
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

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "result_status": result.status.value,
            "adapter_id": result.adapter_id,
            "reason_codes": list(
                result.reason_codes
            ),
            "read_only": result.read_only,
            "execution_result_record": (
                result.execution_result_record
            ),
            "fill_confirmed": (
                result.fill_confirmed
            ),
            "funds_moved": result.funds_moved,
            "portfolio_mutated": (
                result.portfolio_mutated
            ),
            "execution_adapter_called": False,
            "exchange_called": False,
            "live_order_submitted": False,
        }

        print(
            "[PASS] INT-025 Q Series "
            "Execution Adapter Result Contract"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-025 Q Series Execution Adapter Result Contract
    from .qseries_execution_adapter_result_contract import (
        ExecutionAdapterResult,
        ExecutionAdapterResultContractError,
        ExecutionAdapterResultStatus,
        build_execution_adapter_result,
        build_not_called_execution_result,
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
        "# INT-025 Q Series "
        "Execution Adapter Result Contract"
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
    print(" INT-025 INSTALLER")
    print(" Q Series Execution Adapter Result Contract")
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
    print("[DONE] INT-025 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_025_qseries_execution_adapter_result_contract.py"
    )


if __name__ == "__main__":
    main()