"""
OLA-055 Production Live Shadow Start Authorization.

Fail-closed authorization object for the actual OLA-030 production graph.

OLA-054 proves the fully assembled and activated production lineage graph is
ready to start while still untouched. OLA-055 converts that attested readiness
into an explicit, immutable start authorization record that may be consumed by
a later controlled launcher.

This module does not start a process, create a thread, enter a loop, invoke
acquisition, tick the scheduler, run a shadow cycle, emit alerts, hand off to
Q Series, authorize trading, place orders, move funds, or mutate a portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "OLA-055"
ENGINE_ID = "OLA-055"
AUTHORIZATION_TYPE = "oracle_production_live_shadow_start_authorization"


class OracleProductionLiveShadowStartAuthorizationError(ValueError):
    pass


class OracleProductionLiveShadowStartAuthorizationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowStartAuthorizationRecord:
    schema_version: str
    engine_id: str
    authorization_type: str
    startup_readiness_attested: bool
    startup_ready: bool
    bootstrap_service_start_allowed: bool
    runner_identity_preserved: bool
    start_authorized: bool
    authorization_consumed: bool = False
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
            raise OracleProductionLiveShadowStartAuthorizationError(
                "OLA-055 identity mismatch"
            )
        if self.authorization_type != AUTHORIZATION_TYPE:
            raise OracleProductionLiveShadowStartAuthorizationError(
                "authorization_type mismatch"
            )

        required = (
            self.startup_readiness_attested,
            self.startup_ready,
            self.bootstrap_service_start_allowed,
            self.runner_identity_preserved,
            self.start_authorized,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization failed closed"
            )

        forbidden = (
            self.authorization_consumed,
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
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "OLA-055 observed forbidden activity before authorization use"
            )


class OracleProductionLiveShadowStartAuthorizer:
    read_only = True
    execution_allowed = False

    def authorize(
        self,
        *,
        startup_readiness_attestation: Any,
        service_bootstrap: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowStartAuthorizationRecord:
        runner_bootstrap = getattr(runner, "_bootstrap_record", None)

        checks = {
            "startup_readiness_attested": (
                getattr(
                    startup_readiness_attestation,
                    "startup_ready",
                    False,
                )
                is True
            ),
            "startup_ready": (
                getattr(
                    startup_readiness_attestation,
                    "startup_ready",
                    False,
                )
                is True
            ),
            "bootstrap_service_start_allowed": (
                getattr(service_bootstrap, "service_start_allowed", None) is True
            ),
            "runner_identity_preserved": (
                runner_bootstrap is service_bootstrap
            ),
        }

        if not all(checks.values()):
            failed = ", ".join(
                name for name, passed in checks.items() if not passed
            )
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization mismatch: "
                f"{failed}"
            )

        forbidden_bootstrap_activity = any(
            getattr(service_bootstrap, field, None) is True
            for field in (
                "service_started",
                "process_created",
                "thread_created",
                "loop_started",
                "acquisition_invoked",
                "scheduler_tick_invoked",
                "shadow_cycle_invoked",
            )
        )
        if forbidden_bootstrap_activity:
            raise OracleProductionLiveShadowStartAuthorizationBlocked(
                "production live-shadow start authorization requires "
                "an untouched pre-start bootstrap"
            )

        return OracleProductionLiveShadowStartAuthorizationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            authorization_type=AUTHORIZATION_TYPE,
            start_authorized=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "AUTHORIZATION_TYPE",
    "OracleProductionLiveShadowStartAuthorizationError",
    "OracleProductionLiveShadowStartAuthorizationBlocked",
    "OracleProductionLiveShadowStartAuthorizationRecord",
    "OracleProductionLiveShadowStartAuthorizer",
]
