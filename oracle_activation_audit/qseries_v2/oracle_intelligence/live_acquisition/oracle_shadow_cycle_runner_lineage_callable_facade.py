"""
OLA-050
Oracle Shadow Cycle Runner Lineage Callable Facade

Exact callable-shape adapter between OLA-021 ShadowCycleRunnerBinding and the
OLA-046 scheduler lineage production adapter.

Critical production contract:

ShadowCycleRunnerBinding invokes:
    cycle_callable(**canonical_cycle_kwargs)

OLA-046 invokes:
    adapter(
        cycle_completed_at=<typed datetime>,
        cycle_kwargs=<full canonical kwargs mapping>,
    )

OLA-050 owns that exact callable-shape translation.

Purpose:
- accept arbitrary scheduler cycle kwargs exactly as ShadowCycleRunnerBinding
  supplies them
- require cycle_completed_at in the incoming kwargs
- rehydrate cycle_completed_at from canonical ISO-8601 string or accept an
  already-aware datetime
- pass the COMPLETE original kwargs mapping unchanged into OLA-046
- preserve the existing OLA-030 projected cycle result object unchanged
- expose OLA-046 out-of-band lineage receipt without changing scheduler result

No scheduler kwargs mutation.
No scheduler result projection mutation.
No acquisition.
No persistence.
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
from typing import Any

from .oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
    SchedulerLineageProductionAdapterContractError,
    SchedulerLineageProductionAdapterInvariantError,
    SchedulerLineageProductionAdapterReceipt,
)


SCHEMA_VERSION = "OLA-050"
ENGINE_ID = "OLA-050"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class ShadowCycleRunnerLineageCallableFacadeContractError(ValueError):
    """Raised when OLA-050 callable input is malformed."""


class ShadowCycleRunnerLineageCallableFacadeInvariantError(RuntimeError):
    """Raised when permanent OLA-050 invariants are violated."""


def _rehydrate_cycle_completed_at(
    value: Any,
) -> datetime:
    if isinstance(value, datetime):
        candidate = value
    elif isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                "cycle_completed_at must not be empty"
            )

        try:
            candidate = datetime.fromisoformat(
                normalized
            )
        except ValueError as exc:
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                "cycle_completed_at must be canonical ISO-8601"
            ) from exc
    else:
        raise ShadowCycleRunnerLineageCallableFacadeContractError(
            "cycle_completed_at must be datetime or canonical ISO-8601 string"
        )

    if (
        candidate.tzinfo is None
        or candidate.utcoffset() is None
    ):
        raise ShadowCycleRunnerLineageCallableFacadeContractError(
            "cycle_completed_at must be timezone-aware"
        )

    return candidate.astimezone(
        timezone.utc
    )


@dataclass(frozen=True, slots=True)
class ShadowCycleRunnerLineageCallableFacadeReceipt:
    schema_version: str
    engine_id: str
    incoming_kwarg_count: int
    cycle_completed_at_present: bool
    cycle_completed_at_rehydrated: bool
    full_kwargs_forwarded_unchanged: bool
    scheduler_result_preserved: bool
    adapter_receipt: SchedulerLineageProductionAdapterReceipt
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
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "engine identity invariant violated"
            )

        if self.incoming_kwarg_count <= 0:
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "incoming kwarg count must be positive"
            )

        required = (
            self.cycle_completed_at_present,
            self.cycle_completed_at_rehydrated,
            self.full_kwargs_forwarded_unchanged,
            self.scheduler_result_preserved,
        )

        if required != (
            True,
            True,
            True,
            True,
        ):
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "OLA-050 callable facade invariant violated"
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
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "OLA-050 read-only authority invariants violated"
            )


class OracleShadowCycleRunnerLineageCallableFacade:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        scheduler_adapter: OracleSchedulerLineageProductionAdapter,
    ) -> None:
        if not isinstance(
            scheduler_adapter,
            OracleSchedulerLineageProductionAdapter,
        ):
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                "scheduler_adapter must be an OLA-046 adapter"
            )

        self._scheduler_adapter = (
            scheduler_adapter
        )
        self._last_receipt: (
            ShadowCycleRunnerLineageCallableFacadeReceipt | None
        ) = None

    @property
    def scheduler_adapter(
        self,
    ) -> OracleSchedulerLineageProductionAdapter:
        return self._scheduler_adapter

    @property
    def last_receipt(
        self,
    ) -> ShadowCycleRunnerLineageCallableFacadeReceipt | None:
        return self._last_receipt

    def __call__(
        self,
        **cycle_kwargs: Any,
    ) -> Any:
        if not cycle_kwargs:
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                "cycle kwargs must not be empty"
            )

        if "cycle_completed_at" not in cycle_kwargs:
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                "cycle_completed_at is required"
            )

        original_kwargs = dict(
            cycle_kwargs
        )

        completed_at = (
            _rehydrate_cycle_completed_at(
                original_kwargs[
                    "cycle_completed_at"
                ]
            )
        )

        try:
            result = self._scheduler_adapter(
                cycle_completed_at=completed_at,
                cycle_kwargs=original_kwargs,
            )
        except SchedulerLineageProductionAdapterContractError as exc:
            raise ShadowCycleRunnerLineageCallableFacadeContractError(
                f"OLA-046 adapter rejected scheduler cycle: {exc}"
            ) from exc
        except SchedulerLineageProductionAdapterInvariantError as exc:
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                f"OLA-046 adapter invariant failed: {exc}"
            ) from exc

        adapter_receipt = (
            self._scheduler_adapter.last_receipt
        )

        if adapter_receipt is None:
            raise ShadowCycleRunnerLineageCallableFacadeInvariantError(
                "OLA-046 completed without adapter receipt"
            )

        receipt = (
            ShadowCycleRunnerLineageCallableFacadeReceipt(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                incoming_kwarg_count=len(
                    original_kwargs
                ),
                cycle_completed_at_present=True,
                cycle_completed_at_rehydrated=True,
                full_kwargs_forwarded_unchanged=True,
                scheduler_result_preserved=True,
                adapter_receipt=adapter_receipt,
                read_only=READ_ONLY,
                execution_allowed=EXECUTION_ALLOWED,
                execution_adapter_resolved=(
                    EXECUTION_ADAPTER_RESOLVED
                ),
                execution_adapter_invoked=(
                    EXECUTION_ADAPTER_INVOKED
                ),
                trade_authorization_allowed=(
                    TRADE_AUTHORIZATION_ALLOWED
                ),
                order_placement_allowed=(
                    ORDER_PLACEMENT_ALLOWED
                ),
                funds_moved=FUNDS_MOVED,
                portfolio_mutated=PORTFOLIO_MUTATED,
            )
        )

        receipt.assert_invariants()
        self._last_receipt = receipt

        return result
