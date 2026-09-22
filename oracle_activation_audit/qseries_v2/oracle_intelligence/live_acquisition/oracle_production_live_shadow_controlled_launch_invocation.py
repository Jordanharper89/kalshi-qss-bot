"""
OLA-058 Production Live Shadow Controlled Launch Invocation.

Fail-closed invocation adapter requiring an OLA-057 launch binding and the
exact bound production runner identity before a synchronous launch call may be
delegated. This module does not create a process, thread, or background loop,
and it never enables alerts, Q Series handoff, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SCHEMA_VERSION = "OLA-058"
ENGINE_ID = "OLA-058"
INVOCATION_TYPE = "oracle_production_live_shadow_controlled_launch_invocation"


class OracleProductionLiveShadowControlledLaunchInvocationError(ValueError):
    pass


class OracleProductionLiveShadowControlledLaunchInvocationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowControlledLaunchInvocationRecord:
    schema_version: str
    engine_id: str
    invocation_type: str
    source_binding_schema_version: str
    source_binding_engine_id: str
    source_binding_identity: int
    runner_identity: int
    launch_binding_valid: bool
    exact_runner_identity_preserved: bool
    synchronous_invocation_allowed: bool
    invocation_completed: bool
    process_created: bool = False
    thread_created: bool = False
    background_loop_started: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    read_only: bool = True
    execution_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise OracleProductionLiveShadowControlledLaunchInvocationError(
                "OLA-058 schema_version mismatch"
            )
        if self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowControlledLaunchInvocationError(
                "OLA-058 engine_id mismatch"
            )
        if self.invocation_type != INVOCATION_TYPE:
            raise OracleProductionLiveShadowControlledLaunchInvocationError(
                "OLA-058 invocation_type mismatch"
            )

        required = (
            self.launch_binding_valid,
            self.exact_runner_identity_preserved,
            self.synchronous_invocation_allowed,
            self.invocation_completed,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(
                "OLA-058 invocation record failed closed"
            )

        forbidden = (
            self.process_created,
            self.thread_created,
            self.background_loop_started,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )
        if any(value is True for value in forbidden):
            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(
                "OLA-058 observed forbidden activity"
            )


class OracleProductionLiveShadowControlledLaunchInvoker:
    read_only = True
    execution_allowed = False

    def invoke(
        self,
        *,
        launch_binding: Any,
        runner: Any,
        launch_callable: Callable[[], Any],
    ) -> tuple[
        OracleProductionLiveShadowControlledLaunchInvocationRecord,
        Any,
    ]:
        checks = (
            getattr(launch_binding, "schema_version", None) == "OLA-057",
            getattr(launch_binding, "engine_id", None) == "OLA-057",
            getattr(launch_binding, "launch_binding_ready", None) is True,
            getattr(launch_binding, "launch_invoked", None) is False,
            getattr(launch_binding, "runner_identity", None) == id(runner),
            getattr(launch_binding, "read_only", None) is True,
            getattr(launch_binding, "execution_allowed", None) is False,
            getattr(runner, "read_only", None) is True,
            getattr(runner, "execution_allowed", None) is False,
            callable(launch_callable),
        )

        if not all(checks):
            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(
                "OLA-058 launch invocation eligibility failed closed"
            )

        result = launch_callable()

        record = OracleProductionLiveShadowControlledLaunchInvocationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            invocation_type=INVOCATION_TYPE,
            source_binding_schema_version=launch_binding.schema_version,
            source_binding_engine_id=launch_binding.engine_id,
            source_binding_identity=id(launch_binding),
            runner_identity=id(runner),
            launch_binding_valid=True,
            exact_runner_identity_preserved=True,
            synchronous_invocation_allowed=True,
            invocation_completed=True,
        )

        return record, result


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "INVOCATION_TYPE",
    "OracleProductionLiveShadowControlledLaunchInvocationError",
    "OracleProductionLiveShadowControlledLaunchInvocationBlocked",
    "OracleProductionLiveShadowControlledLaunchInvocationRecord",
    "OracleProductionLiveShadowControlledLaunchInvoker",
]
