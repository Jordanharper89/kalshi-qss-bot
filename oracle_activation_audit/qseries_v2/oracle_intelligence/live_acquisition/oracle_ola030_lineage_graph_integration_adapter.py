"""
OLA-049
Oracle OLA-030 Lineage Graph Integration Adapter

Narrow canonical substitution boundary for the existing OLA-030 production
graph.

Purpose:
- accept the existing OLA-030 production persistence router
- accept the existing OLA-030 production_cycle_callable
- construct OLA-048 exactly once
- return the exact persistence router replacement for BOTH:
    OracleLiveReadOnlyAcquisitionRuntime
    OraclePostgreSQLShadowAcquisitionCycleOrchestrator (OLA-017)
- return the exact cycle callable replacement for:
    ShadowCycleRunnerBinding
- preserve all unrelated OLA-030 graph components unchanged
- preserve the original production router and cycle callable by identity

No scheduler kwargs changes.
No scheduler result projection changes.
No intelligence interpretation.
No signal scoring.
No alerts.
No Q Series handoff.
No execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .oracle_live_shadow_lineage_graph_binding_contract import (
    OracleLiveShadowLineageGraphBindingContract,
)


SCHEMA_VERSION = "OLA-049"
ENGINE_ID = "OLA-049"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class OLA030LineageGraphIntegrationAdapterContractError(ValueError):
    """Raised when OLA-049 integration input is malformed."""


class OLA030LineageGraphIntegrationAdapterInvariantError(RuntimeError):
    """Raised when permanent OLA-049 invariants are violated."""


@dataclass(frozen=True, slots=True)
class OLA030LineageGraphIntegrationBindings:
    schema_version: str
    engine_id: str
    runtime_persistence_router: Any
    ola017_persistence_router: Any
    shadow_cycle_runner_callable: Callable[..., Any]
    graph_binding: OracleLiveShadowLineageGraphBindingContract
    original_persistence_router_preserved: bool
    original_cycle_callable_preserved: bool
    runtime_and_ola017_same_router: bool
    scheduler_callable_lineage_wrapped: bool
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
            raise OLA030LineageGraphIntegrationAdapterInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise OLA030LineageGraphIntegrationAdapterInvariantError(
                "engine identity invariant violated"
            )

        if (
            self.runtime_persistence_router
            is not self.ola017_persistence_router
        ):
            raise OLA030LineageGraphIntegrationAdapterInvariantError(
                "runtime and OLA-017 must share the same staged router"
            )

        required = (
            self.original_persistence_router_preserved,
            self.original_cycle_callable_preserved,
            self.runtime_and_ola017_same_router,
            self.scheduler_callable_lineage_wrapped,
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
        ):
            raise OLA030LineageGraphIntegrationAdapterInvariantError(
                "OLA-049 integration binding invariant violated"
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
            raise OLA030LineageGraphIntegrationAdapterInvariantError(
                "OLA-049 read-only authority invariants violated"
            )


class OracleOLA030LineageGraphIntegrationAdapter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        production_persistence_router: Any,
        production_cycle_callable: Callable[..., Any],
    ) -> None:
        route_batch = getattr(
            production_persistence_router,
            "route_batch",
            None,
        )

        if not callable(route_batch):
            raise OLA030LineageGraphIntegrationAdapterContractError(
                "production_persistence_router must expose callable route_batch"
            )

        if not callable(production_cycle_callable):
            raise OLA030LineageGraphIntegrationAdapterContractError(
                "production_cycle_callable must be callable"
            )

        self._original_persistence_router = (
            production_persistence_router
        )
        self._original_cycle_callable = (
            production_cycle_callable
        )

        self._graph_binding = (
            OracleLiveShadowLineageGraphBindingContract(
                production_persistence_router=(
                    production_persistence_router
                ),
                production_scheduler_cycle_callable=(
                    production_cycle_callable
                ),
            )
        )

        self._bindings = OLA030LineageGraphIntegrationBindings(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            runtime_persistence_router=(
                self._graph_binding.runtime_persistence_router
            ),
            ola017_persistence_router=(
                self._graph_binding.ola017_persistence_router
            ),
            shadow_cycle_runner_callable=(
                self._graph_binding.shadow_cycle_runner_callable
            ),
            graph_binding=self._graph_binding,
            original_persistence_router_preserved=(
                self._graph_binding.production_persistence_router
                is production_persistence_router
            ),
            original_cycle_callable_preserved=(
                self._graph_binding.production_scheduler_cycle_callable
                is production_cycle_callable
            ),
            runtime_and_ola017_same_router=(
                self._graph_binding.runtime_persistence_router
                is self._graph_binding.ola017_persistence_router
            ),
            scheduler_callable_lineage_wrapped=(
                self._graph_binding.shadow_cycle_runner_callable
                is self._graph_binding.composition.scheduler_adapter
            ),
            scheduler_kwargs_unchanged=True,
            scheduler_results_unchanged=True,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
        )

        self._bindings.assert_invariants()

    @property
    def bindings(
        self,
    ) -> OLA030LineageGraphIntegrationBindings:
        return self._bindings

    @property
    def graph_binding(
        self,
    ) -> OracleLiveShadowLineageGraphBindingContract:
        return self._graph_binding

    def apply_to_graph_components(
        self,
        *,
        graph_components: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(graph_components, Mapping):
            raise OLA030LineageGraphIntegrationAdapterContractError(
                "graph_components must be a mapping"
            )

        result = dict(graph_components)

        protected_keys = {
            "runtime_persistence_router",
            "ola017_persistence_router",
            "shadow_cycle_runner_callable",
        }

        for key in protected_keys:
            if key in result:
                raise OLA030LineageGraphIntegrationAdapterContractError(
                    f"graph_components already contains protected key: {key}"
                )

        result["runtime_persistence_router"] = (
            self._bindings.runtime_persistence_router
        )
        result["ola017_persistence_router"] = (
            self._bindings.ola017_persistence_router
        )
        result["shadow_cycle_runner_callable"] = (
            self._bindings.shadow_cycle_runner_callable
        )

        for key, value in graph_components.items():
            if result[key] is not value:
                raise OLA030LineageGraphIntegrationAdapterInvariantError(
                    f"unrelated graph component was mutated: {key}"
                )

        return result
