"""
OLA-046
Oracle Scheduler Lineage Production Adapter

Typed production adapter around the existing OLA-030 scheduler cycle callable.

Purpose:
- preserve the existing OLA-030 scheduler callable contract
- preserve scheduler kwargs exactly
- invoke the existing scheduler-cycle callable exactly once
- delegate OLA-017 cycle completion and lineage advancement through OLA-045
- preserve the existing projected scheduler result object unchanged
- retain OLA-045 lineage completion evidence out-of-band for audit/tests

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from .oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
    SchedulerCycleLineageCompletionBridgeContractError,
    SchedulerCycleLineageCompletionBridgeInvariantError,
    SchedulerCycleLineageCompletionBridgeReceipt,
)


SCHEMA_VERSION = "OLA-046"
ENGINE_ID = "OLA-046"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class SchedulerLineageProductionAdapterContractError(ValueError):
    pass


class SchedulerLineageProductionAdapterInvariantError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SchedulerLineageProductionAdapterReceipt:
    schema_version: str
    engine_id: str
    scheduler_callable_invocation_count: int
    scheduler_kwargs_preserved: bool
    scheduler_result_preserved: bool
    lineage_completion_receipt: SchedulerCycleLineageCompletionBridgeReceipt | None
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
            raise SchedulerLineageProductionAdapterInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise SchedulerLineageProductionAdapterInvariantError(
                "engine identity invariant violated"
            )
        if self.scheduler_callable_invocation_count != 1:
            raise SchedulerLineageProductionAdapterInvariantError(
                "scheduler callable must be invoked exactly once"
            )
        if self.scheduler_kwargs_preserved is not True:
            raise SchedulerLineageProductionAdapterInvariantError(
                "scheduler kwargs preservation invariant violated"
            )
        if self.scheduler_result_preserved is not True:
            raise SchedulerLineageProductionAdapterInvariantError(
                "scheduler result preservation invariant violated"
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
            raise SchedulerLineageProductionAdapterInvariantError(
                "OLA-046 read-only authority invariants violated"
            )


class OracleSchedulerLineageProductionAdapter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        scheduler_cycle_callable: Callable[..., Any],
        lineage_completion_bridge: OracleSchedulerCycleLineageCompletionBridge,
    ) -> None:
        if not callable(scheduler_cycle_callable):
            raise SchedulerLineageProductionAdapterContractError(
                "scheduler_cycle_callable must be callable"
            )

        if not isinstance(
            lineage_completion_bridge,
            OracleSchedulerCycleLineageCompletionBridge,
        ):
            raise SchedulerLineageProductionAdapterContractError(
                "lineage_completion_bridge must be an OLA-045 bridge"
            )

        self._scheduler_cycle_callable = scheduler_cycle_callable
        self._lineage_completion_bridge = lineage_completion_bridge
        self._last_receipt: SchedulerLineageProductionAdapterReceipt | None = None

    @property
    def scheduler_cycle_callable(self) -> Callable[..., Any]:
        return self._scheduler_cycle_callable

    @property
    def lineage_completion_bridge(self) -> OracleSchedulerCycleLineageCompletionBridge:
        return self._lineage_completion_bridge

    @property
    def last_receipt(self) -> SchedulerLineageProductionAdapterReceipt | None:
        return self._last_receipt

    def __call__(
        self,
        *,
        cycle_completed_at: datetime,
        cycle_kwargs: Mapping[str, Any],
    ) -> Any:
        if not isinstance(cycle_kwargs, Mapping):
            raise SchedulerLineageProductionAdapterContractError(
                "cycle_kwargs must be a mapping"
            )

        original_kwargs = dict(cycle_kwargs)
        invocation_count = 0
        result_box: dict[str, Any] = {}

        def cycle_runner_proxy(**kwargs: Any) -> Any:
            nonlocal invocation_count
            invocation_count += 1

            if kwargs != original_kwargs:
                raise SchedulerLineageProductionAdapterInvariantError(
                    "OLA-045 changed scheduler cycle kwargs"
                )

            result = self._scheduler_cycle_callable(**kwargs)
            result_box["result"] = result
            return result

        try:
            returned_result = self._lineage_completion_bridge.run_cycle(
                cycle_runner=cycle_runner_proxy,
                cycle_completed_at=cycle_completed_at,
                cycle_kwargs=original_kwargs,
            )
        except SchedulerCycleLineageCompletionBridgeContractError as exc:
            raise SchedulerLineageProductionAdapterContractError(
                f"OLA-045 lineage completion bridge rejected cycle: {exc}"
            ) from exc
        except SchedulerCycleLineageCompletionBridgeInvariantError as exc:
            raise SchedulerLineageProductionAdapterInvariantError(
                f"OLA-045 lineage completion invariant failed: {exc}"
            ) from exc

        if invocation_count != 1:
            raise SchedulerLineageProductionAdapterInvariantError(
                "scheduler cycle callable invocation count diverged"
            )

        if returned_result is not result_box.get("result"):
            raise SchedulerLineageProductionAdapterInvariantError(
                "scheduler result object was not preserved"
            )

        receipt = SchedulerLineageProductionAdapterReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            scheduler_callable_invocation_count=invocation_count,
            scheduler_kwargs_preserved=True,
            scheduler_result_preserved=True,
            lineage_completion_receipt=self._lineage_completion_bridge.last_receipt,
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
        return returned_result
