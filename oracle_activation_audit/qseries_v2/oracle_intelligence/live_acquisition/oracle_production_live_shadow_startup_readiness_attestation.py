
"""
OLA-054 Production Live Shadow Startup Readiness Attestation.

Fail-closed startup authorization boundary for the actual OLA-030 production
graph. This record does not start the service. It only proves that the
already-attested production lineage graph, scheduler activation chain,
OLA-022 bootstrap record, and OLA-023 runner agree on a permanently read-only
live-shadow startup boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-054"
ENGINE_ID = "OLA-054"
ATTESTATION_TYPE = "oracle_production_live_shadow_startup_readiness_attestation"


class OracleProductionLiveShadowStartupReadinessAttestationError(ValueError):
    pass


class OracleProductionLiveShadowStartupReadinessAttestationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowStartupReadinessAttestationRecord:
    schema_version: str
    engine_id: str
    attestation_type: str
    graph_assembly_attested: bool
    scheduler_activation_attested: bool
    bootstrap_ready: bool
    bootstrap_service_start_allowed: bool
    bootstrap_not_started: bool
    runner_bootstrap_identity_preserved: bool
    runner_read_only: bool
    startup_ready: bool
    service_started: bool = False
    process_created: bool = False
    thread_created: bool = False
    loop_started: bool = False
    acquisition_invoked: bool = False
    scheduler_tick_invoked: bool = False
    shadow_cycle_invoked: bool = False
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
            raise OracleProductionLiveShadowStartupReadinessAttestationError(
                "OLA-054 identity mismatch"
            )
        if self.attestation_type != ATTESTATION_TYPE:
            raise OracleProductionLiveShadowStartupReadinessAttestationError(
                "attestation_type mismatch"
            )

        required = (
            self.graph_assembly_attested,
            self.scheduler_activation_attested,
            self.bootstrap_ready,
            self.bootstrap_service_start_allowed,
            self.bootstrap_not_started,
            self.runner_bootstrap_identity_preserved,
            self.runner_read_only,
            self.startup_ready,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "production live-shadow startup readiness failed closed"
            )

        forbidden = (
            self.service_started,
            self.process_created,
            self.thread_created,
            self.loop_started,
            self.acquisition_invoked,
            self.scheduler_tick_invoked,
            self.shadow_cycle_invoked,
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
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "OLA-054 startup attestation observed forbidden activity"
            )


class OracleProductionLiveShadowStartupReadinessAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        lineage_graph_attestation: Any,
        lineage_scheduler_activation_attestation: Any,
        service_bootstrap: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowStartupReadinessAttestationRecord:
        runner_bootstrap = getattr(runner, "_bootstrap_record", None)

        checks = {
            "graph_assembly_attested": (
                getattr(
                    lineage_graph_attestation,
                    "full_graph_attested",
                    getattr(
                        lineage_graph_attestation,
                        "actual_ola030_graph_attested",
                        False,
                    ),
                )
                is True
            ),
            "scheduler_activation_attested": (
                getattr(
                    lineage_scheduler_activation_attestation,
                    "full_activation_chain_attested",
                    False,
                )
                is True
            ),
            "bootstrap_ready": (
                getattr(service_bootstrap, "bootstrap_status", None) == "ready"
            ),
            "bootstrap_service_start_allowed": (
                getattr(service_bootstrap, "service_start_allowed", None) is True
            ),
            "bootstrap_not_started": all(
                getattr(service_bootstrap, field, None) is False
                for field in (
                    "service_started",
                    "process_created",
                    "thread_created",
                    "loop_started",
                    "acquisition_invoked",
                    "scheduler_tick_invoked",
                    "shadow_cycle_invoked",
                )
            ),
            "runner_bootstrap_identity_preserved": (
                runner_bootstrap is service_bootstrap
            ),
            "runner_read_only": (
                getattr(runner, "read_only", None) is True
                and getattr(runner, "execution_allowed", None) is False
            ),
        }

        if not all(checks.values()):
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLiveShadowStartupReadinessAttestationBlocked(
                "production live-shadow startup readiness mismatch: "
                f"{failed}"
            )

        return OracleProductionLiveShadowStartupReadinessAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            attestation_type=ATTESTATION_TYPE,
            startup_ready=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ATTESTATION_TYPE",
    "OracleProductionLiveShadowStartupReadinessAttestationError",
    "OracleProductionLiveShadowStartupReadinessAttestationBlocked",
    "OracleProductionLiveShadowStartupReadinessAttestationRecord",
    "OracleProductionLiveShadowStartupReadinessAttestor",
]
