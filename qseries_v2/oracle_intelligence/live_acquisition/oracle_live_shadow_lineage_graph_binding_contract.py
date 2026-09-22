"""
OLA-048
Oracle Live Shadow Lineage Graph Binding Contract

Final canonical graph-binding boundary before OLA-030 production integration.

Purpose:
- accept the existing production persistence router
- accept the existing OLA-030 production scheduler cycle callable
- create one OLA-047 shared production composition
- expose the OLA-042 staged persistence router as the exact router that must be
  injected into both OracleLiveReadOnlyAcquisitionRuntime and OLA-017
- expose the OLA-046 scheduler adapter as the exact callable that must be
  injected into ShadowCycleRunnerBinding
- prove both exposed bindings share one OLA-044 lineage production state
- preserve the original production persistence router and scheduler callable
  by exact object identity

This contract performs graph binding only.
It does not acquire data, persist observations, advance a scheduler tick,
interpret intelligence, score signals, alert, hand off to Q Series,
authorize trading, place orders, move funds, or mutate portfolios.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .oracle_persisted_cohort_staging_router import (
    OraclePersistedCohortStagingRouter,
)
from .oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)
from .oracle_scheduler_lineage_production_composition import (
    OracleSchedulerLineageProductionComposition,
)


SCHEMA_VERSION = "OLA-048"
ENGINE_ID = "OLA-048"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class LiveShadowLineageGraphBindingContractError(ValueError):
    """Raised when OLA-048 graph binding input is malformed."""


class LiveShadowLineageGraphBindingInvariantError(RuntimeError):
    """Raised when permanent OLA-048 invariants are violated."""


@dataclass(frozen=True, slots=True)
class LiveShadowLineageGraphBindingRecord:
    schema_version: str
    engine_id: str
    persistence_router_binding_role: str
    scheduler_cycle_binding_role: str
    production_persistence_router_preserved: bool
    production_scheduler_callable_preserved: bool
    staged_persistence_router_shared: bool
    scheduler_adapter_shared: bool
    shared_production_wiring_identity: bool
    shared_lineage_state_identity: bool
    runtime_and_ola017_same_router_required: bool
    shadow_cycle_runner_uses_scheduler_adapter_required: bool
    scheduler_kwargs_unchanged: bool
    scheduler_results_unchanged: bool
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
            raise LiveShadowLineageGraphBindingInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise LiveShadowLineageGraphBindingInvariantError(
                "engine identity invariant violated"
            )

        if self.persistence_router_binding_role != (
            "runtime_and_ola017_shared_router"
        ):
            raise LiveShadowLineageGraphBindingInvariantError(
                "persistence router binding role invariant violated"
            )

        if self.scheduler_cycle_binding_role != (
            "shadow_cycle_runner_cycle_callable"
        ):
            raise LiveShadowLineageGraphBindingInvariantError(
                "scheduler cycle binding role invariant violated"
            )

        required = (
            self.production_persistence_router_preserved,
            self.production_scheduler_callable_preserved,
            self.staged_persistence_router_shared,
            self.scheduler_adapter_shared,
            self.shared_production_wiring_identity,
            self.shared_lineage_state_identity,
            self.runtime_and_ola017_same_router_required,
            self.shadow_cycle_runner_uses_scheduler_adapter_required,
            self.scheduler_kwargs_unchanged,
            self.scheduler_results_unchanged,
        )

        if required != (
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            True,
        ):
            raise LiveShadowLineageGraphBindingInvariantError(
                "OLA-048 graph binding invariant violated"
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
            raise LiveShadowLineageGraphBindingInvariantError(
                "OLA-048 read-only authority invariants violated"
            )


class OracleLiveShadowLineageGraphBindingContract:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        production_persistence_router: Any,
        production_scheduler_cycle_callable: Callable[..., Any],
    ) -> None:
        route_batch = getattr(
            production_persistence_router,
            "route_batch",
            None,
        )

        if not callable(route_batch):
            raise LiveShadowLineageGraphBindingContractError(
                "production_persistence_router must expose callable route_batch"
            )

        if not callable(
            production_scheduler_cycle_callable
        ):
            raise LiveShadowLineageGraphBindingContractError(
                "production_scheduler_cycle_callable must be callable"
            )

        self._production_persistence_router = (
            production_persistence_router
        )
        self._production_scheduler_cycle_callable = (
            production_scheduler_cycle_callable
        )

        self._composition = (
            OracleSchedulerLineageProductionComposition(
                production_persistence_router=(
                    production_persistence_router
                ),
                scheduler_cycle_callable=(
                    production_scheduler_cycle_callable
                ),
            )
        )

        self._record = LiveShadowLineageGraphBindingRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            persistence_router_binding_role=(
                "runtime_and_ola017_shared_router"
            ),
            scheduler_cycle_binding_role=(
                "shadow_cycle_runner_cycle_callable"
            ),
            production_persistence_router_preserved=(
                self._composition
                .production_persistence_router
                is production_persistence_router
            ),
            production_scheduler_callable_preserved=(
                self._composition
                .scheduler_cycle_callable
                is production_scheduler_cycle_callable
            ),
            staged_persistence_router_shared=(
                self.runtime_persistence_router
                is self.ola017_persistence_router
                is self._composition
                .staged_persistence_router
            ),
            scheduler_adapter_shared=(
                self.shadow_cycle_runner_callable
                is self._composition.scheduler_adapter
            ),
            shared_production_wiring_identity=(
                self._composition
                .completion_bridge
                .production_wiring
                is self._composition.production_wiring
            ),
            shared_lineage_state_identity=(
                self._composition
                .scheduler_adapter
                .lineage_completion_bridge
                .production_wiring
                is self._composition.production_wiring
            ),
            runtime_and_ola017_same_router_required=True,
            shadow_cycle_runner_uses_scheduler_adapter_required=True,
            scheduler_kwargs_unchanged=True,
            scheduler_results_unchanged=True,
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

        self._record.assert_invariants()

    @property
    def production_persistence_router(self) -> Any:
        return self._production_persistence_router

    @property
    def production_scheduler_cycle_callable(
        self,
    ) -> Callable[..., Any]:
        return self._production_scheduler_cycle_callable

    @property
    def composition(
        self,
    ) -> OracleSchedulerLineageProductionComposition:
        return self._composition

    @property
    def runtime_persistence_router(
        self,
    ) -> OraclePersistedCohortStagingRouter:
        return self._composition.staged_persistence_router

    @property
    def ola017_persistence_router(
        self,
    ) -> OraclePersistedCohortStagingRouter:
        return self._composition.staged_persistence_router

    @property
    def shadow_cycle_runner_callable(
        self,
    ) -> OracleSchedulerLineageProductionAdapter:
        return self._composition.scheduler_adapter

    @property
    def record(
        self,
    ) -> LiveShadowLineageGraphBindingRecord:
        return self._record
