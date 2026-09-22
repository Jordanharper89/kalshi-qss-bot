"""
OLA-047
Oracle Scheduler Lineage Production Composition

Single canonical composition surface for production lineage wiring.

Purpose:
- accept the existing production persistence router
- accept the existing OLA-030 scheduler cycle callable
- build one shared OLA-044 production wiring contract
- expose the OLA-042 staged persistence router for injection into both the
  live acquisition runtime and OLA-017
- build OLA-045 completion bridge on the same shared wiring state
- build OLA-046 scheduler lineage production adapter around the existing
  OLA-030 scheduler cycle callable
- preserve one shared lineage state across repeated scheduler cycles

This module performs composition only.
It does not alter scheduler kwargs, scheduler result projection, persistence
semantics, intelligence interpretation, scoring, alerts, Q Series handoff,
authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)
from .oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
)
from .oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)


SCHEMA_VERSION = "OLA-047"
ENGINE_ID = "OLA-047"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class SchedulerLineageProductionCompositionContractError(ValueError):
    """Raised when OLA-047 composition input is malformed."""


class SchedulerLineageProductionCompositionInvariantError(RuntimeError):
    """Raised when permanent OLA-047 invariants are violated."""


@dataclass(frozen=True, slots=True)
class SchedulerLineageProductionCompositionReceipt:
    schema_version: str
    engine_id: str
    production_persistence_router_preserved: bool
    scheduler_cycle_callable_preserved: bool
    staged_router_shared_with_production_wiring: bool
    completion_bridge_shared_with_production_wiring: bool
    scheduler_adapter_shared_with_completion_bridge: bool
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
            raise SchedulerLineageProductionCompositionInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise SchedulerLineageProductionCompositionInvariantError(
                "engine identity invariant violated"
            )

        required = (
            self.production_persistence_router_preserved,
            self.scheduler_cycle_callable_preserved,
            self.staged_router_shared_with_production_wiring,
            self.completion_bridge_shared_with_production_wiring,
            self.scheduler_adapter_shared_with_completion_bridge,
        )

        if required != (
            True,
            True,
            True,
            True,
            True,
        ):
            raise SchedulerLineageProductionCompositionInvariantError(
                "OLA-047 shared production composition invariant violated"
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
            raise SchedulerLineageProductionCompositionInvariantError(
                "OLA-047 read-only authority invariants violated"
            )


class OracleSchedulerLineageProductionComposition:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        production_persistence_router: Any,
        scheduler_cycle_callable: Callable[..., Any],
    ) -> None:
        route_batch = getattr(
            production_persistence_router,
            "route_batch",
            None,
        )

        if not callable(route_batch):
            raise SchedulerLineageProductionCompositionContractError(
                "production_persistence_router must expose callable route_batch"
            )

        if not callable(scheduler_cycle_callable):
            raise SchedulerLineageProductionCompositionContractError(
                "scheduler_cycle_callable must be callable"
            )

        self._production_persistence_router = (
            production_persistence_router
        )
        self._scheduler_cycle_callable = (
            scheduler_cycle_callable
        )

        self._production_wiring = (
            OraclePersistedCohortLineageProductionWiringContract(
                production_persistence_router=(
                    production_persistence_router
                )
            )
        )

        self._completion_bridge = (
            OracleSchedulerCycleLineageCompletionBridge(
                production_wiring=self._production_wiring
            )
        )

        self._scheduler_adapter = (
            OracleSchedulerLineageProductionAdapter(
                scheduler_cycle_callable=(
                    scheduler_cycle_callable
                ),
                lineage_completion_bridge=(
                    self._completion_bridge
                ),
            )
        )

        self._receipt = (
            SchedulerLineageProductionCompositionReceipt(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                production_persistence_router_preserved=(
                    self._production_wiring
                    .production_persistence_router
                    is production_persistence_router
                ),
                scheduler_cycle_callable_preserved=(
                    self._scheduler_adapter
                    .scheduler_cycle_callable
                    is scheduler_cycle_callable
                ),
                staged_router_shared_with_production_wiring=(
                    self.staged_persistence_router
                    is self._production_wiring
                    .staged_persistence_router
                ),
                completion_bridge_shared_with_production_wiring=(
                    self._completion_bridge.production_wiring
                    is self._production_wiring
                ),
                scheduler_adapter_shared_with_completion_bridge=(
                    self._scheduler_adapter
                    .lineage_completion_bridge
                    is self._completion_bridge
                ),
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

        self._receipt.assert_invariants()

    @property
    def production_persistence_router(self) -> Any:
        return self._production_persistence_router

    @property
    def scheduler_cycle_callable(
        self,
    ) -> Callable[..., Any]:
        return self._scheduler_cycle_callable

    @property
    def production_wiring(
        self,
    ) -> OraclePersistedCohortLineageProductionWiringContract:
        return self._production_wiring

    @property
    def staged_persistence_router(self):
        return self._production_wiring.staged_persistence_router

    @property
    def completion_bridge(
        self,
    ) -> OracleSchedulerCycleLineageCompletionBridge:
        return self._completion_bridge

    @property
    def scheduler_adapter(
        self,
    ) -> OracleSchedulerLineageProductionAdapter:
        return self._scheduler_adapter

    @property
    def receipt(
        self,
    ) -> SchedulerLineageProductionCompositionReceipt:
        return self._receipt
