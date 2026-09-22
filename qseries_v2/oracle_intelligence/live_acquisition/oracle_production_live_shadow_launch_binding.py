
"""
OLA-057 Production Live Shadow Launch Binding.

Fail-closed binding between an OLA-056 single-use launch token and the exact
OLA-023 production live-shadow runner instance exposed by the actual OLA-030
graph.

This module does not invoke the runner. It only proves that an eligible
single-use token is bound to the exact read-only production runner.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "OLA-057"
ENGINE_ID = "OLA-057"
BINDING_TYPE = "oracle_production_live_shadow_launch_binding"


class OracleProductionLiveShadowLaunchBindingError(ValueError):
    pass


class OracleProductionLiveShadowLaunchBindingBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowLaunchBindingRecord:
    schema_version: str
    engine_id: str
    binding_type: str

    launch_token_schema_version: str
    launch_token_engine_id: str
    launch_token_identity: int
    runner_identity: int

    token_valid: bool
    token_not_invoked: bool
    runner_identity_bound: bool
    launch_binding_ready: bool

    launch_invoked: bool = False
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
        if self.schema_version != SCHEMA_VERSION:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 schema_version mismatch"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 engine_id mismatch"
            )

        if self.binding_type != BINDING_TYPE:
            raise OracleProductionLiveShadowLaunchBindingError(
                "OLA-057 binding_type mismatch"
            )

        required = (
            self.token_valid,
            self.token_not_invoked,
            self.runner_identity_bound,
            self.launch_binding_ready,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 launch binding failed closed"
            )

        forbidden = (
            self.launch_invoked,
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
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 observed forbidden activity"
            )


class OracleProductionLiveShadowLaunchBinder:
    read_only = True
    execution_allowed = False

    def bind(
        self,
        *,
        launch_token: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowLaunchBindingRecord:

        token_checks = (
            getattr(
                launch_token,
                "schema_version",
                None,
            )
            == "OLA-056",

            getattr(
                launch_token,
                "engine_id",
                None,
            )
            == "OLA-056",

            getattr(
                launch_token,
                "authorization_consumed",
                None,
            )
            is True,

            getattr(
                launch_token,
                "launch_token_issued",
                None,
            )
            is True,

            getattr(
                launch_token,
                "launch_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "service_started",
                None,
            )
            is False,

            getattr(
                launch_token,
                "loop_started",
                None,
            )
            is False,

            getattr(
                launch_token,
                "acquisition_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "scheduler_tick_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "shadow_cycle_invoked",
                None,
            )
            is False,

            getattr(
                launch_token,
                "read_only",
                None,
            )
            is True,

            getattr(
                launch_token,
                "execution_allowed",
                None,
            )
            is False,
        )

        if not all(token_checks):
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-056 launch token is not eligible "
                "for OLA-057 binding"
            )

        if runner is None:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 requires the exact production runner"
            )

        if getattr(
            runner,
            "read_only",
            None,
        ) is not True:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 runner is not read-only"
            )

        if getattr(
            runner,
            "execution_allowed",
            None,
        ) is not False:
            raise OracleProductionLiveShadowLaunchBindingBlocked(
                "OLA-057 runner execution invariant violated"
            )

        return OracleProductionLiveShadowLaunchBindingRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            binding_type=BINDING_TYPE,

            launch_token_schema_version=(
                launch_token.schema_version
            ),

            launch_token_engine_id=(
                launch_token.engine_id
            ),

            launch_token_identity=id(
                launch_token
            ),

            runner_identity=id(
                runner
            ),

            token_valid=True,
            token_not_invoked=True,
            runner_identity_bound=True,
            launch_binding_ready=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "BINDING_TYPE",
    "OracleProductionLiveShadowLaunchBindingError",
    "OracleProductionLiveShadowLaunchBindingBlocked",
    "OracleProductionLiveShadowLaunchBindingRecord",
    "OracleProductionLiveShadowLaunchBinder",
]
