from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_dry_run_runtime_adapter.py"
)

TEST_PATH = (
    ROOT
    / "test_int_021_qseries_dry_run_runtime_adapter.py"
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
    INT-021 — Q Series Dry-Run Runtime Adapter.

    This module provides the first concrete implementation of the INT-020
    runtime adapter protocol.

    The adapter is intentionally non-live. It validates a READY invocation,
    creates a deterministic simulation receipt, and returns an immutable
    NOT_INVOKED runtime result.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and execution control.
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

    from .qseries_runtime_adapter_interface import (
        RuntimeAdapterInvocation,
        RuntimeAdapterResult,
        RuntimeExecutionAdapterProtocol,
        RuntimeInvocationStatus,
        RuntimeResultStatus,
    )


    SCHEMA_VERSION = "INT-021"
    ENGINE_ID = "INT-021"
    SOURCE_INVOCATION_SCHEMA = "INT-020"


    class DryRunRuntimeAdapterError(ValueError):
        """Raised when the INT-021 dry-run adapter contract is invalid."""


    class DryRunDecision(str, Enum):
        SIMULATED = "simulated"
        BLOCKED = "blocked"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise DryRunRuntimeAdapterError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise DryRunRuntimeAdapterError(
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
            raise DryRunRuntimeAdapterError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise DryRunRuntimeAdapterError(
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
                raise DryRunRuntimeAdapterError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise DryRunRuntimeAdapterError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise DryRunRuntimeAdapterError(
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
            raise DryRunRuntimeAdapterError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise DryRunRuntimeAdapterError(
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


    @dataclass(frozen=True, slots=True)
    class DryRunSimulationReceipt:
        """
        Immutable receipt describing the INT-021 dry-run simulation.

        The receipt is evidence that the runtime invocation was evaluated
        without calling a live adapter.
        """

        receipt_id: str
        invocation_id: str
        invocation_hash: str
        adapter_id: str
        decision: DryRunDecision
        simulated_at: str
        checks: Mapping[str, Any]
        simulation_details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        network_access_enabled: bool = False
        adapter_called: bool = False
        exchange_called: bool = False
        live_order_submitted: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        receipt_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "receipt_id",
                _require_non_empty_string(
                    self.receipt_id,
                    "receipt_id",
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
                "adapter_id",
                _require_non_empty_string(
                    self.adapter_id,
                    "adapter_id",
                ).lower(),
            )

            if not isinstance(
                self.decision,
                DryRunDecision,
            ):
                object.__setattr__(
                    self,
                    "decision",
                    DryRunDecision(
                        str(self.decision).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "simulated_at",
                _normalize_timestamp(
                    self.simulated_at,
                    "simulated_at",
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
                "simulation_details",
                _freeze_mapping(
                    self.simulation_details,
                    "simulation_details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise DryRunRuntimeAdapterError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise DryRunRuntimeAdapterError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise DryRunRuntimeAdapterError(
                    "INT-021 receipts must be read_only"
                )

            forbidden_true_fields = {
                "network_access_enabled": self.network_access_enabled,
                "adapter_called": self.adapter_called,
                "exchange_called": self.exchange_called,
                "live_order_submitted": self.live_order_submitted,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": self.portfolio_mutated,
            }

            for field_name, field_value in forbidden_true_fields.items():
                if field_value is not False:
                    raise DryRunRuntimeAdapterError(
                        f"{field_name} must remain false"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.receipt_hash:
                supplied_hash = _require_non_empty_string(
                    self.receipt_hash,
                    "receipt_hash",
                )

                if supplied_hash != calculated_hash:
                    raise DryRunRuntimeAdapterError(
                        "receipt_hash does not match receipt contents"
                    )

            object.__setattr__(
                self,
                "receipt_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "receipt_id": self.receipt_id,
                "invocation_id": self.invocation_id,
                "invocation_hash": self.invocation_hash,
                "adapter_id": self.adapter_id,
                "decision": self.decision.value,
                "simulated_at": self.simulated_at,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "simulation_details": _mapping_to_dict(
                    self.simulation_details
                ),
                "read_only": self.read_only,
                "network_access_enabled": (
                    self.network_access_enabled
                ),
                "adapter_called": self.adapter_called,
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
            payload["receipt_hash"] = self.receipt_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    @dataclass(frozen=True, slots=True)
    class DryRunAdapterResponse:
        """Combined immutable response from the dry-run adapter."""

        receipt: DryRunSimulationReceipt
        result: RuntimeAdapterResult

        def __post_init__(self) -> None:
            if not isinstance(
                self.receipt,
                DryRunSimulationReceipt,
            ):
                raise DryRunRuntimeAdapterError(
                    "receipt must be a DryRunSimulationReceipt"
                )

            if not isinstance(
                self.result,
                RuntimeAdapterResult,
            ):
                raise DryRunRuntimeAdapterError(
                    "result must be a RuntimeAdapterResult"
                )

            if (
                self.receipt.invocation_id
                != self.result.invocation_id
            ):
                raise DryRunRuntimeAdapterError(
                    "receipt and result invocation_id values must match"
                )

            if (
                self.receipt.invocation_hash
                != self.result.invocation_hash
            ):
                raise DryRunRuntimeAdapterError(
                    "receipt and result invocation_hash values must match"
                )

            if (
                self.receipt.adapter_id
                != self.result.adapter_id
            ):
                raise DryRunRuntimeAdapterError(
                    "receipt and result adapter_id values must match"
                )


    class QSeriesDryRunRuntimeAdapter(
        RuntimeExecutionAdapterProtocol
    ):
        """
        Deterministic non-live implementation of the INT-020 protocol.

        This class never performs network I/O and never executes an order.
        """

        __slots__ = (
            "adapter_id",
            "_adapter_version",
        )

        def __init__(
            self,
            *,
            adapter_id: str,
            adapter_version: str,
        ) -> None:
            self.adapter_id = _require_non_empty_string(
                adapter_id,
                "adapter_id",
            ).lower()

            self._adapter_version = _require_non_empty_string(
                adapter_version,
                "adapter_version",
            )

        @property
        def adapter_version(self) -> str:
            return self._adapter_version

        def simulate(
            self,
            *,
            invocation: RuntimeAdapterInvocation,
            simulated_at: str,
            simulation_context: Mapping[str, Any] | None = None,
        ) -> DryRunAdapterResponse:
            """
            Evaluate an INT-020 invocation and return a dry-run receipt/result.

            No adapter call, exchange call, or execution occurs.
            """

            if not isinstance(
                invocation,
                RuntimeAdapterInvocation,
            ):
                raise DryRunRuntimeAdapterError(
                    "invocation must be a RuntimeAdapterInvocation"
                )

            if invocation.schema_version != SOURCE_INVOCATION_SCHEMA:
                raise DryRunRuntimeAdapterError(
                    "invocation.schema_version must be INT-020"
                )

            normalized_simulated_at = _normalize_timestamp(
                simulated_at,
                "simulated_at",
            )

            checks = {
                "invocation_ready": (
                    invocation.status
                    is RuntimeInvocationStatus.READY
                ),
                "adapter_id_matches": (
                    invocation.adapter_id
                    == self.adapter_id
                ),
                "invocation_read_only": (
                    invocation.read_only is True
                ),
                "execution_disabled": (
                    invocation.execution_allowed is False
                ),
                "adapter_call_required": (
                    invocation.adapter_call_required is True
                ),
                "adapter_not_previously_called": (
                    invocation.adapter_called is False
                ),
                "invocation_hash_present": bool(
                    invocation.invocation_hash
                ),
                "invocation_not_expired": (
                    datetime.fromisoformat(
                        normalized_simulated_at
                    )
                    <= datetime.fromisoformat(
                        invocation.expires_at
                    )
                ),
            }

            decision = (
                DryRunDecision.SIMULATED
                if all(checks.values())
                else DryRunDecision.BLOCKED
            )

            frozen_context = _freeze_mapping(
                simulation_context,
                "simulation_context",
            )

            simulation_details = {
                "adapter_version": self.adapter_version,
                "simulation_context": _mapping_to_dict(
                    frozen_context
                ),
                "network_access_enabled": False,
                "adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            }

            identity_payload = {
                "schema_version": SCHEMA_VERSION,
                "invocation_id": invocation.invocation_id,
                "invocation_hash": invocation.invocation_hash,
                "adapter_id": self.adapter_id,
                "decision": decision.value,
                "simulated_at": normalized_simulated_at,
                "checks": checks,
                "simulation_details": simulation_details,
            }

            receipt_id = (
                "int021-"
                f"{canonical_hash(identity_payload)[:32]}"
            )

            receipt = DryRunSimulationReceipt(
                receipt_id=receipt_id,
                invocation_id=invocation.invocation_id,
                invocation_hash=invocation.invocation_hash,
                adapter_id=self.adapter_id,
                decision=decision,
                simulated_at=normalized_simulated_at,
                checks=checks,
                simulation_details=simulation_details,
            )

            if decision is DryRunDecision.SIMULATED:
                result_status = RuntimeResultStatus.NOT_INVOKED
                reason_codes = (
                    "dry_run_simulation_completed",
                )
                explanation = (
                    "The INT-020 invocation was processed by the INT-021 "
                    "dry-run adapter. No runtime network adapter was called, "
                    "no exchange request was sent, and no execution occurred."
                )
            else:
                result_status = RuntimeResultStatus.REJECTED
                reason_codes = tuple(
                    sorted(
                        key
                        for key, passed in checks.items()
                        if not passed
                    )
                )
                explanation = (
                    "The INT-020 invocation failed one or more INT-021 "
                    "dry-run adapter checks. The simulation was blocked and "
                    "no execution occurred."
                )

            result_identity = {
                "schema_version": SOURCE_INVOCATION_SCHEMA,
                "invocation_id": invocation.invocation_id,
                "invocation_hash": invocation.invocation_hash,
                "adapter_id": self.adapter_id,
                "status": result_status.value,
                "completed_at": normalized_simulated_at,
                "reason_codes": list(reason_codes),
                "receipt_id": receipt.receipt_id,
                "receipt_hash": receipt.receipt_hash,
            }

            result_id = (
                "int021-result-"
                f"{canonical_hash(result_identity)[:32]}"
            )

            result = RuntimeAdapterResult(
                result_id=result_id,
                invocation_id=invocation.invocation_id,
                invocation_hash=invocation.invocation_hash,
                adapter_id=self.adapter_id,
                status=result_status,
                completed_at=normalized_simulated_at,
                adapter_reference=None,
                reason_codes=reason_codes,
                explanation=explanation,
                details={
                    "dry_run_receipt_id": receipt.receipt_id,
                    "dry_run_receipt_hash": receipt.receipt_hash,
                    "decision": receipt.decision.value,
                    "network_access_enabled": False,
                    "adapter_called": False,
                    "exchange_called": False,
                    "live_order_submitted": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
                read_only=True,
                live_order_submitted=False,
                funds_moved=False,
                portfolio_mutated=False,
            )

            return DryRunAdapterResponse(
                receipt=receipt,
                result=result,
            )

        def invoke(
            self,
            invocation: RuntimeAdapterInvocation,
        ) -> RuntimeAdapterResult:
            """
            Protocol method intentionally disabled for deterministic safety.

            Call simulate() with a caller-supplied timestamp instead.
            """

            raise DryRunRuntimeAdapterError(
                "invoke() is disabled because INT-021 requires a "
                "caller-supplied simulated_at timestamp; use simulate()"
            )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_INVOCATION_SCHEMA",
        "DryRunRuntimeAdapterError",
        "DryRunDecision",
        "DryRunSimulationReceipt",
        "DryRunAdapterResponse",
        "QSeriesDryRunRuntimeAdapter",
        "canonical_json",
        "canonical_hash",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError

    from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
        ENGINE_ID,
        SCHEMA_VERSION,
        DryRunDecision,
        DryRunRuntimeAdapterError,
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


    def expect_dry_run_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except DryRunRuntimeAdapterError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected DryRunRuntimeAdapterError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-021",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-021",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-10T18:00:00-05:00"
            ),
        }


    def make_invocation(
        *,
        adapter_id: str = "adapter.kalshi.execution",
        market_id: str = "KXTEST-INT021",
        invocation_expires_at: str = (
            "2026-07-10T18:08:00-05:00"
        ),
    ):
        request = build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=adapter_id,
            account_reference="account-test",
            market_id=market_id,
            action="buy",
            order_type="limit",
            quantity="3",
            limit_price="0.45",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id="client-order-int021",
            created_at=(
                "2026-07-10T18:00:01-05:00"
            ),
            expires_at=(
                "2026-07-10T18:10:00-05:00"
            ),
            rationale=(
                "Build INT-021 dry-run adapter test chain."
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
                    "2026-07-10T18:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-10T18:00:00-05:00"
                ),
                registration_reason=(
                    "INT-021 test registration."
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
                "2026-07-10T18:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T18:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-10T18:00:04-05:00"
            ),
            expires_at=(
                "2026-07-10T18:09:00-05:00"
            ),
        )

        return build_runtime_adapter_invocation(
            dispatch=dispatch,
            prepared_at=(
                "2026-07-10T18:00:05-05:00"
            ),
            expires_at=invocation_expires_at,
            invocation_context={
                "environment": "test",
                "adapter_called": False,
                "network_access_enabled": False,
            },
        )


    def make_adapter(
        *,
        adapter_id: str = "adapter.kalshi.execution",
    ) -> QSeriesDryRunRuntimeAdapter:
        return QSeriesDryRunRuntimeAdapter(
            adapter_id=adapter_id,
            adapter_version="1.0.0-dry-run",
        )


    def test_successful_dry_run() -> None:
        invocation = make_invocation()
        adapter = make_adapter()

        response = adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
            simulation_context={
                "scenario": "unit-test",
                "network_access_enabled": False,
            },
        )

        receipt = response.receipt
        result = response.result

        assert receipt.schema_version == SCHEMA_VERSION
        assert receipt.engine_id == ENGINE_ID
        assert receipt.decision is DryRunDecision.SIMULATED
        assert (
            receipt.invocation_id
            == invocation.invocation_id
        )
        assert (
            receipt.invocation_hash
            == invocation.invocation_hash
        )
        assert receipt.adapter_id == invocation.adapter_id
        assert receipt.read_only is True
        assert receipt.network_access_enabled is False
        assert receipt.adapter_called is False
        assert receipt.exchange_called is False
        assert receipt.live_order_submitted is False
        assert receipt.funds_moved is False
        assert receipt.portfolio_mutated is False
        assert len(receipt.receipt_hash) == 64

        assert (
            result.status
            is RuntimeResultStatus.NOT_INVOKED
        )
        assert (
            result.invocation_id
            == invocation.invocation_id
        )
        assert result.adapter_reference is None
        assert result.read_only is True
        assert result.live_order_submitted is False
        assert result.funds_moved is False
        assert result.portfolio_mutated is False
        assert (
            result.details["dry_run_receipt_id"]
            == receipt.receipt_id
        )
        assert (
            result.details["dry_run_receipt_hash"]
            == receipt.receipt_hash
        )


    def test_determinism() -> None:
        invocation = make_invocation()
        adapter = make_adapter()

        first = adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
            simulation_context={
                "network_access_enabled": False,
                "scenario": "deterministic",
            },
        )

        second = adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
            simulation_context={
                "scenario": "deterministic",
                "network_access_enabled": False,
            },
        )

        assert (
            first.receipt.receipt_id
            == second.receipt.receipt_id
        )
        assert (
            first.receipt.receipt_hash
            == second.receipt.receipt_hash
        )
        assert (
            first.receipt.to_dict()
            == second.receipt.to_dict()
        )
        assert (
            first.result.result_id
            == second.result.result_id
        )
        assert (
            first.result.result_hash
            == second.result.result_hash
        )
        assert (
            first.result.to_dict()
            == second.result.to_dict()
        )


    def test_immutability() -> None:
        invocation = make_invocation()

        response = make_adapter().simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
        )

        try:
            response.receipt.decision = (
                DryRunDecision.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "dry-run receipt must be immutable"
            )

        try:
            response.receipt.checks[
                "invocation_ready"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "dry-run receipt checks must be immutable"
            )


    def test_adapter_identity_mismatch_blocked() -> None:
        invocation = make_invocation()

        adapter = make_adapter(
            adapter_id="adapter.other.execution"
        )

        response = adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
        )

        assert (
            response.receipt.decision
            is DryRunDecision.BLOCKED
        )
        assert (
            response.receipt.checks[
                "adapter_id_matches"
            ]
            is False
        )
        assert (
            response.result.status
            is RuntimeResultStatus.REJECTED
        )
        assert (
            "adapter_id_matches"
            in response.result.reason_codes
        )
        assert (
            response.result.live_order_submitted
            is False
        )


    def test_expired_invocation_blocked() -> None:
        invocation = make_invocation(
            invocation_expires_at=(
                "2026-07-10T18:00:06-05:00"
            )
        )

        response = make_adapter().simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:07-05:00"
            ),
        )

        assert (
            response.receipt.decision
            is DryRunDecision.BLOCKED
        )
        assert (
            response.receipt.checks[
                "invocation_not_expired"
            ]
            is False
        )
        assert (
            response.result.status
            is RuntimeResultStatus.REJECTED
        )
        assert (
            "invocation_not_expired"
            in response.result.reason_codes
        )
        assert (
            response.result.live_order_submitted
            is False
        )
        assert response.result.funds_moved is False
        assert response.result.portfolio_mutated is False


    def test_protocol_invoke_disabled() -> None:
        invocation = make_invocation()
        adapter = make_adapter()

        expect_dry_run_error(
            lambda: adapter.invoke(invocation),
            "caller-supplied simulated_at",
        )


    def test_timestamp_required() -> None:
        invocation = make_invocation()
        adapter = make_adapter()

        expect_dry_run_error(
            lambda: adapter.simulate(
                invocation=invocation,
                simulated_at=(
                    "2026-07-10T18:00:06"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_successful_dry_run()
        test_determinism()
        test_immutability()
        test_adapter_identity_mismatch_blocked()
        test_expired_invocation_blocked()
        test_protocol_invoke_disabled()
        test_timestamp_required()

        invocation = make_invocation()
        adapter = make_adapter()

        response = adapter.simulate(
            invocation=invocation,
            simulated_at=(
                "2026-07-10T18:00:06-05:00"
            ),
            simulation_context={
                "environment": "test",
                "scenario": "summary",
                "network_access_enabled": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "decision": (
                response.receipt.decision.value
            ),
            "result_status": (
                response.result.status.value
            ),
            "adapter_id": (
                response.receipt.adapter_id
            ),
            "read_only": (
                response.receipt.read_only
            ),
            "network_access_enabled": (
                response.receipt.network_access_enabled
            ),
            "adapter_called": (
                response.receipt.adapter_called
            ),
            "exchange_called": (
                response.receipt.exchange_called
            ),
            "live_order_submitted": (
                response.receipt.live_order_submitted
            ),
            "funds_moved": (
                response.receipt.funds_moved
            ),
            "portfolio_mutated": (
                response.receipt.portfolio_mutated
            ),
        }

        print(
            "[PASS] INT-021 Q Series "
            "Dry-Run Runtime Adapter"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-021 Q Series Dry-Run Runtime Adapter
    from .qseries_dry_run_runtime_adapter import (
        DryRunAdapterResponse,
        DryRunDecision,
        DryRunRuntimeAdapterError,
        DryRunSimulationReceipt,
        QSeriesDryRunRuntimeAdapter,
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
        "# INT-021 Q Series "
        "Dry-Run Runtime Adapter"
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
    print(" INT-021 INSTALLER")
    print(" Q Series Dry-Run Runtime Adapter")
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
    print("[DONE] INT-021 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_021_qseries_dry_run_runtime_adapter.py"
    )


if __name__ == "__main__":
    main()