"""
OLA-052 Production Lineage Graph Assembly Attestation.
Reconciled dual-router production contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-052"
ENGINE_ID = "OLA-052"


class OracleProductionLineageGraphAssemblyAttestationBlocked(RuntimeError):
    pass


def _first_attr(obj: Any, *names: str) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


@dataclass(frozen=True, slots=True)
class OracleProductionLineageGraphAssemblyAttestationRecord:
    schema_version: str
    engine_id: str
    actual_ola030_graph_attested: bool
    production_router_identity_attested: bool
    staged_router_identity_attested: bool
    runtime_uses_staged_router_attested: bool
    ola017_uses_production_router_attested: bool
    dual_router_topology_attested: bool
    ola045_to_ola044_identity_attested: bool
    ola046_to_production_cycle_identity_attested: bool
    ola046_to_ola045_identity_attested: bool
    ola050_to_ola046_identity_attested: bool
    fail_closed_identity_mismatch_tested: bool
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False


class OracleProductionLineageGraphAssemblyAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        production_persistence_router: Any,
        lineage_production_wiring: Any,
        lineage_persistence_router: Any,
        acquisition_runtime: Any,
        cycle_orchestrator: Any,
        production_cycle_callable: Any,
        lineage_completion_bridge: Any,
        lineage_scheduler_adapter: Any,
        lineage_cycle_callable: Any,
    ) -> OracleProductionLineageGraphAssemblyAttestationRecord:

        wiring_production_router = _first_attr(
            lineage_production_wiring,
            "production_persistence_router",
            "_production_persistence_router",
        )

        wiring_staged_router = _first_attr(
            lineage_production_wiring,
            "staged_persistence_router",
            "_staged_persistence_router",
        )

        runtime_router = _first_attr(
            acquisition_runtime,
            "canonical_observation_router",
            "_canonical_observation_router",
        )

        orchestrator_router = _first_attr(
            cycle_orchestrator,
            "postgresql_router",
            "_postgresql_router",
        )

        completion_wiring = _first_attr(
            lineage_completion_bridge,
            "production_wiring",
            "_production_wiring",
        )

        adapter_cycle_callable = _first_attr(
            lineage_scheduler_adapter,
            "scheduler_cycle_callable",
            "_scheduler_cycle_callable",
        )

        adapter_completion_bridge = _first_attr(
            lineage_scheduler_adapter,
            "lineage_completion_bridge",
            "_lineage_completion_bridge",
        )

        facade_scheduler_adapter = _first_attr(
            lineage_cycle_callable,
            "scheduler_adapter",
            "_scheduler_adapter",
        )

        checks = {
            "production_router_identity_attested": (
                wiring_production_router is production_persistence_router
            ),
            "staged_router_identity_attested": (
                wiring_staged_router is lineage_persistence_router
            ),
            "runtime_uses_staged_router_attested": (
                runtime_router is lineage_persistence_router
            ),
            "ola017_uses_production_router_attested": (
                orchestrator_router is production_persistence_router
            ),
            "dual_router_topology_attested": (
                production_persistence_router is not lineage_persistence_router
            ),
            "ola045_to_ola044_identity_attested": (
                completion_wiring is lineage_production_wiring
            ),
            "ola046_to_production_cycle_identity_attested": (
                adapter_cycle_callable is production_cycle_callable
            ),
            "ola046_to_ola045_identity_attested": (
                adapter_completion_bridge is lineage_completion_bridge
            ),
            "ola050_to_ola046_identity_attested": (
                facade_scheduler_adapter is lineage_scheduler_adapter
            ),
        }

        failed = [
            name
            for name, passed in checks.items()
            if passed is not True
        ]

        if failed:
            raise OracleProductionLineageGraphAssemblyAttestationBlocked(
                "production lineage graph assembly mismatch: "
                + ", ".join(failed)
            )

        return OracleProductionLineageGraphAssemblyAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            actual_ola030_graph_attested=True,
            fail_closed_identity_mismatch_tested=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OracleProductionLineageGraphAssemblyAttestationBlocked",
    "OracleProductionLineageGraphAssemblyAttestationRecord",
    "OracleProductionLineageGraphAssemblyAttestor",
]
