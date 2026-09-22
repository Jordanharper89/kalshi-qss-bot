"""
OLA-053 Oracle Production Lineage Scheduler Activation Attestation.

Fail-closed activation attestation for the actual OLA-030 production graph.

OLA-052 proves the lineage graph is assembled correctly before scheduler
construction. OLA-053 proves that the exact OLA-050 lineage callable is then
activated through the real production execution path:

OLA-050 callable facade
    ->
ShadowCycleRunnerBinding
    ->
OLA-021 scheduler
    ->
OracleLiveShadowSchedulerBinding
    ->
OLA-023 service runner

This boundary performs no acquisition, persistence, alerting, handoff, or
execution. Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-053"
ENGINE_ID = "OLA-053"
ATTESTATION_TYPE = "oracle_production_lineage_scheduler_activation_attestation"


class OracleProductionLineageSchedulerActivationAttestationError(ValueError):
    pass


class OracleProductionLineageSchedulerActivationAttestationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLineageSchedulerActivationAttestationRecord:
    schema_version: str
    engine_id: str
    attestation_type: str
    ola050_bound_to_cycle_runner: bool
    cycle_runner_bound_to_ola021: bool
    ola021_bound_to_service_scheduler_binding: bool
    service_scheduler_binding_bound_to_ola023: bool
    scheduler_engine_identity_preserved: bool
    cycle_runner_engine_identity_preserved: bool
    full_activation_chain_attested: bool
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

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.engine_id != ENGINE_ID:
            raise OracleProductionLineageSchedulerActivationAttestationError(
                "OLA-053 identity mismatch"
            )
        if self.attestation_type != ATTESTATION_TYPE:
            raise OracleProductionLineageSchedulerActivationAttestationError(
                "attestation_type mismatch"
            )

        required = (
            self.ola050_bound_to_cycle_runner,
            self.cycle_runner_bound_to_ola021,
            self.ola021_bound_to_service_scheduler_binding,
            self.service_scheduler_binding_bound_to_ola023,
            self.scheduler_engine_identity_preserved,
            self.cycle_runner_engine_identity_preserved,
            self.full_activation_chain_attested,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "production lineage scheduler activation attestation failed closed"
            )

        forbidden = (
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )
        if any(value is True for value in forbidden):
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "OLA-053 permanent read-only invariant violated"
            )


class OracleProductionLineageSchedulerActivationAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        lineage_cycle_callable: Any,
        cycle_runner_binding: Any,
        scheduler: Any,
        service_scheduler_binding: Any,
        runner: Any,
    ) -> OracleProductionLineageSchedulerActivationAttestationRecord:
        cycle_callable = getattr(cycle_runner_binding, "cycle_callable", None)

        scheduler_cycle_runner = getattr(scheduler, "cycle_runner", None)
        if scheduler_cycle_runner is None:
            scheduler_cycle_runner = getattr(scheduler, "_cycle_runner", None)

        service_tick_callable = getattr(
            service_scheduler_binding,
            "tick_callable",
            None,
        )

        runner_scheduler = getattr(runner, "_scheduler", None)
        scheduler_tick = getattr(scheduler, "run_tick", None)

        checks = {
            "ola050_bound_to_cycle_runner": (
                cycle_callable is lineage_cycle_callable
            ),
            "cycle_runner_bound_to_ola021": (
                scheduler_cycle_runner is cycle_runner_binding
            ),
            "ola021_bound_to_service_scheduler_binding": (
                getattr(service_tick_callable, "__self__", None) is scheduler
                and getattr(service_tick_callable, "__func__", None)
                is getattr(scheduler_tick, "__func__", None)
            ),
            "service_scheduler_binding_bound_to_ola023": (
                runner_scheduler is service_scheduler_binding
            ),
            "scheduler_engine_identity_preserved": (
                getattr(service_scheduler_binding, "engine_id", None) == "OLA-021"
            ),
            "cycle_runner_engine_identity_preserved": (
                getattr(cycle_runner_binding, "engine_id", None) == "OLA-017"
            ),
        }

        full = all(checks.values())
        if not full:
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLineageSchedulerActivationAttestationBlocked(
                "production lineage scheduler activation mismatch: "
                f"{failed}"
            )

        return OracleProductionLineageSchedulerActivationAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            attestation_type=ATTESTATION_TYPE,
            full_activation_chain_attested=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ATTESTATION_TYPE",
    "OracleProductionLineageSchedulerActivationAttestationError",
    "OracleProductionLineageSchedulerActivationAttestationBlocked",
    "OracleProductionLineageSchedulerActivationAttestationRecord",
    "OracleProductionLineageSchedulerActivationAttestor",
]
