"""
OLA-045
Oracle Scheduler Cycle Lineage Completion Bridge

Canonical typed bridge between the OLA-030 scheduler cycle boundary and
OLA-044 persisted cohort lineage production wiring.

Purpose:
- invoke the existing OLA-017 cycle runner exactly once
- preserve the exact OLA-017 cycle result object
- require completed-cycle persistence evidence before lineage wiring
- derive acquisition_batch_id from the pending OLA-042 stage metadata
- require exactly one pending staged cohort for the completed cycle boundary
- invoke OLA-044 with the exact cycle_completed_at timestamp
- return the original OLA-017 result unchanged for existing OLA-030
  scheduler result projection
- retain the OLA-044 wiring receipt for audit and tests

This bridge does not alter OLA-021 scheduler kwargs.
It does not alter OLA-030 scheduler result projection.
It performs no acquisition or persistence itself.

No intelligence interpretation.
No signal scoring.
No alerts.
No Q Series handoff.
No execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
    PersistedCohortLineageProductionWiringContractError,
    PersistedCohortLineageProductionWiringInvariantError,
    PersistedCohortLineageProductionWiringReceipt,
)


SCHEMA_VERSION = "OLA-045"
ENGINE_ID = "OLA-045"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class SchedulerCycleLineageCompletionBridgeContractError(ValueError):
    """Raised when OLA-045 bridge input is malformed."""


class SchedulerCycleLineageCompletionBridgeInvariantError(RuntimeError):
    """Raised when permanent OLA-045 invariants are violated."""


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise SchedulerCycleLineageCompletionBridgeContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise SchedulerCycleLineageCompletionBridgeContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _cycle_payload(
    cycle_result: Any,
) -> dict[str, Any]:
    if hasattr(
        cycle_result,
        "to_canonical_dict",
    ):
        payload = cycle_result.to_canonical_dict()
    elif isinstance(cycle_result, Mapping):
        payload = cycle_result
    else:
        raise SchedulerCycleLineageCompletionBridgeContractError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if not isinstance(payload, Mapping):
        raise SchedulerCycleLineageCompletionBridgeContractError(
            "OLA-017 canonical cycle evidence must be a mapping"
        )

    return dict(payload)


@dataclass(frozen=True, slots=True)
class SchedulerCycleLineageCompletionBridgeReceipt:
    schema_version: str
    engine_id: str
    cycle_invocation_count: int
    cycle_result_preserved: bool
    lineage_completion_invoked: bool
    acquisition_batch_id: str | None
    lineage_wiring_receipt: (
        PersistedCohortLineageProductionWiringReceipt | None
    )
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "engine identity invariant violated"
            )

        if self.cycle_invocation_count != 1:
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-017 cycle must be invoked exactly once"
            )

        if self.cycle_result_preserved is not True:
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-017 cycle result preservation invariant violated"
            )

        if self.lineage_completion_invoked:
            if self.acquisition_batch_id is None:
                raise SchedulerCycleLineageCompletionBridgeInvariantError(
                    "lineage completion requires acquisition batch identity"
                )

            if self.lineage_wiring_receipt is None:
                raise SchedulerCycleLineageCompletionBridgeInvariantError(
                    "lineage completion requires OLA-044 receipt"
                )
        else:
            if self.lineage_wiring_receipt is not None:
                raise SchedulerCycleLineageCompletionBridgeInvariantError(
                    "non-completed cycle cannot carry lineage wiring receipt"
                )

        authority = (
            self.read_only,
            self.execution_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if authority != (
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ):
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-045 read-only authority invariants violated"
            )


class OracleSchedulerCycleLineageCompletionBridge:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        production_wiring: (
            OraclePersistedCohortLineageProductionWiringContract
        ),
    ) -> None:
        if not isinstance(
            production_wiring,
            OraclePersistedCohortLineageProductionWiringContract,
        ):
            raise SchedulerCycleLineageCompletionBridgeContractError(
                "production_wiring must be an OLA-044 production wiring contract"
            )

        self._production_wiring = production_wiring
        self._last_receipt: (
            SchedulerCycleLineageCompletionBridgeReceipt | None
        ) = None

    @property
    def production_wiring(
        self,
    ) -> OraclePersistedCohortLineageProductionWiringContract:
        return self._production_wiring

    @property
    def last_receipt(
        self,
    ) -> SchedulerCycleLineageCompletionBridgeReceipt | None:
        return self._last_receipt

    def run_cycle(
        self,
        *,
        cycle_runner: Callable[..., Any],
        cycle_completed_at: datetime,
        cycle_kwargs: Mapping[str, Any],
    ) -> Any:
        if not callable(cycle_runner):
            raise SchedulerCycleLineageCompletionBridgeContractError(
                "cycle_runner must be callable"
            )

        if not isinstance(cycle_kwargs, Mapping):
            raise SchedulerCycleLineageCompletionBridgeContractError(
                "cycle_kwargs must be a mapping"
            )

        completed_at = _require_utc_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )

        cycle_result = cycle_runner(
            **dict(cycle_kwargs)
        )

        cycle_payload_before = _cycle_payload(
            cycle_result
        )

        if (
            cycle_payload_before.get("schema_version")
            != "OLA-017"
            or cycle_payload_before.get("engine_id")
            != "OLA-017"
        ):
            raise SchedulerCycleLineageCompletionBridgeContractError(
                "cycle result must preserve OLA-017 identity"
            )

        cycle_status = cycle_payload_before.get(
            "cycle_status",
            cycle_payload_before.get("status"),
        )

        lineage_completion_invoked = False
        acquisition_batch_id: str | None = None
        lineage_wiring_receipt = None

        if cycle_status == "completed":
            (
                acquisition_batch_id
            ) = self._resolve_single_pending_batch_id()

            try:
                (
                    preserved_result,
                    lineage_wiring_receipt,
                ) = self._production_wiring.complete_persisted_cycle(
                    ola_017_cycle_result=cycle_result,
                    acquisition_batch_id=acquisition_batch_id,
                    cycle_completed_at=completed_at,
                )
            except PersistedCohortLineageProductionWiringContractError as exc:
                raise SchedulerCycleLineageCompletionBridgeContractError(
                    f"OLA-044 production wiring rejected completed cycle: {exc}"
                ) from exc
            except PersistedCohortLineageProductionWiringInvariantError as exc:
                raise SchedulerCycleLineageCompletionBridgeInvariantError(
                    f"OLA-044 production wiring invariant failed: {exc}"
                ) from exc

            if preserved_result is not cycle_result:
                raise SchedulerCycleLineageCompletionBridgeInvariantError(
                    "OLA-044 did not preserve exact OLA-017 result object"
                )

            lineage_completion_invoked = True

        cycle_payload_after = _cycle_payload(
            cycle_result
        )

        if cycle_payload_after != cycle_payload_before:
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-017 cycle result mutated across lineage completion bridge"
            )

        receipt = SchedulerCycleLineageCompletionBridgeReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            cycle_invocation_count=1,
            cycle_result_preserved=True,
            lineage_completion_invoked=lineage_completion_invoked,
            acquisition_batch_id=acquisition_batch_id,
            lineage_wiring_receipt=lineage_wiring_receipt,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
        )

        receipt.assert_invariants()
        self._last_receipt = receipt

        return cycle_result

    def _resolve_single_pending_batch_id(
        self,
    ) -> str:
        staging_router = (
            self._production_wiring.staged_persistence_router
        )

        pending = getattr(
            staging_router,
            "_pending",
            None,
        )

        if not isinstance(pending, dict):
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-042 pending stage registry is unavailable"
            )

        pending_batch_ids = tuple(
            pending.keys()
        )

        if len(pending_batch_ids) != 1:
            raise SchedulerCycleLineageCompletionBridgeContractError(
                "completed OLA-017 cycle requires exactly one pending OLA-042 staged cohort"
            )

        batch_id = pending_batch_ids[0]

        if not isinstance(batch_id, str) or not batch_id.strip():
            raise SchedulerCycleLineageCompletionBridgeInvariantError(
                "OLA-042 pending acquisition batch identity is malformed"
            )

        return batch_id.strip()
