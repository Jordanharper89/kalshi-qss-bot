"""
OLA-062 Production Live Shadow Controlled Launch Permit Execution.

Consumes an OLA-061 single-use invocation permit exactly once and delegates
one synchronous launch through the already-assembled OLA-060 package:

OLA-061 invocation permit
    + OLA-060 controlled launch package
    -> OLA-058 controlled invoker
    -> OLA-059 exact runner-bound launch callable

This module does not create a process, thread, or background loop. It does not
enable alerts, Q Series handoff, trade authorization, order placement, funds
movement, or portfolio mutation.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


SCHEMA_VERSION = "OLA-062"
ENGINE_ID = "OLA-062"
EXECUTION_TYPE = "oracle_production_live_shadow_controlled_launch_permit_execution"


class OracleProductionLiveShadowControlledLaunchPermitExecutionError(
    ValueError
):
    pass


class OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowControlledLaunchPermitExecutionRecord:
    schema_version: str
    engine_id: str
    execution_type: str

    invocation_permit_identity: int
    source_package_identity: int

    runner_identity: int
    controlled_invoker_identity: int
    callable_binding_identity: int

    invocation_permit_valid: bool
    package_identity_preserved: bool
    runner_identity_preserved: bool
    controlled_invoker_identity_preserved: bool
    callable_binding_identity_preserved: bool

    invocation_permit_consumed: bool
    controlled_invocation_completed: bool

    process_created: bool = False
    thread_created: bool = False
    background_loop_started: bool = False

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
            raise (
                OracleProductionLiveShadowControlledLaunchPermitExecutionError(
                    "OLA-062 schema_version mismatch"
                )
            )

        if self.engine_id != ENGINE_ID:
            raise (
                OracleProductionLiveShadowControlledLaunchPermitExecutionError(
                    "OLA-062 engine_id mismatch"
                )
            )

        if self.execution_type != EXECUTION_TYPE:
            raise (
                OracleProductionLiveShadowControlledLaunchPermitExecutionError(
                    "OLA-062 execution_type mismatch"
                )
            )

        required = (
            self.invocation_permit_valid,
            self.package_identity_preserved,
            self.runner_identity_preserved,
            self.controlled_invoker_identity_preserved,
            self.callable_binding_identity_preserved,
            self.invocation_permit_consumed,
            self.controlled_invocation_completed,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise (
                OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                    "OLA-062 execution record failed closed"
                )
            )

        forbidden = (
            self.process_created,
            self.thread_created,
            self.background_loop_started,
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
            raise (
                OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                    "OLA-062 observed forbidden activity"
                )
            )


class OracleProductionLiveShadowControlledLaunchPermitExecutor:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._consumed_permit_identities: set[int] = set()

    def execute(
        self,
        *,
        invocation_permit: Any,
        launch_package: Any,
    ) -> tuple[
        OracleProductionLiveShadowControlledLaunchPermitExecutionRecord,
        Any,
    ]:
        with self._lock:
            permit_identity = id(
                invocation_permit
            )

            if (
                permit_identity
                in self._consumed_permit_identities
            ):
                raise (
                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                        "OLA-061 invocation permit already consumed"
                    )
                )

            package_record = getattr(
                launch_package,
                "record",
                None,
            )

            callable_binding = getattr(
                launch_package,
                "callable_binding",
                None,
            )

            controlled_invoker = getattr(
                launch_package,
                "controlled_invoker",
                None,
            )

            runner = getattr(
                launch_package,
                "runner",
                None,
            )

            checks = {
                "invocation_permit_valid": (
                    getattr(
                        invocation_permit,
                        "schema_version",
                        None,
                    )
                    == "OLA-061"
                    and getattr(
                        invocation_permit,
                        "engine_id",
                        None,
                    )
                    == "OLA-061"
                    and getattr(
                        invocation_permit,
                        "package_consumed",
                        None,
                    )
                    is True
                    and getattr(
                        invocation_permit,
                        "invocation_permit_issued",
                        None,
                    )
                    is True
                    and getattr(
                        invocation_permit,
                        "invocation_permit_consumed",
                        None,
                    )
                    is False
                    and getattr(
                        invocation_permit,
                        "read_only",
                        None,
                    )
                    is True
                    and getattr(
                        invocation_permit,
                        "execution_allowed",
                        None,
                    )
                    is False
                ),

                "package_identity_preserved": (
                    getattr(
                        invocation_permit,
                        "source_package_identity",
                        None,
                    )
                    == id(
                        launch_package
                    )
                    and getattr(
                        package_record,
                        "schema_version",
                        None,
                    )
                    == "OLA-060"
                    and getattr(
                        package_record,
                        "engine_id",
                        None,
                    )
                    == "OLA-060"
                    and getattr(
                        package_record,
                        "controlled_launch_package_ready",
                        None,
                    )
                    is True
                ),

                "runner_identity_preserved": (
                    getattr(
                        invocation_permit,
                        "runner_identity",
                        None,
                    )
                    == id(
                        runner
                    )
                    and getattr(
                        package_record,
                        "runner_identity",
                        None,
                    )
                    == id(
                        runner
                    )
                ),

                "controlled_invoker_identity_preserved": (
                    getattr(
                        invocation_permit,
                        "controlled_invoker_identity",
                        None,
                    )
                    == id(
                        controlled_invoker
                    )
                    and getattr(
                        package_record,
                        "controlled_invoker_identity",
                        None,
                    )
                    == id(
                        controlled_invoker
                    )
                ),

                "callable_binding_identity_preserved": (
                    getattr(
                        invocation_permit,
                        "callable_binding_identity",
                        None,
                    )
                    == id(
                        callable_binding
                    )
                    and getattr(
                        package_record,
                        "callable_binding_identity",
                        None,
                    )
                    == id(
                        callable_binding
                    )
                ),
            }

            if not all(
                checks.values()
            ):
                failed = ", ".join(
                    name
                    for name, passed in checks.items()
                    if not passed
                )

                raise (
                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                        "OLA-062 permit/package identity mismatch: "
                        f"{failed}"
                    )
                )

            launch_callable = getattr(
                callable_binding,
                "launch_callable",
                None,
            )

            launch_binding = getattr(
                launch_package,
                "launch_binding",
                None,
            )

            if (
                not callable(
                    launch_callable
                )
                or controlled_invoker is None
                or runner is None
                or launch_binding is None
            ):
                raise (
                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                        "OLA-062 launch package is incomplete"
                    )
                )

            self._consumed_permit_identities.add(
                permit_identity
            )

            invocation_record, result = (
                controlled_invoker.invoke(
                    launch_binding=launch_binding,
                    runner=runner,
                    launch_callable=launch_callable,
                )
            )

            if (
                getattr(
                    invocation_record,
                    "schema_version",
                    None,
                )
                != "OLA-058"
                or getattr(
                    invocation_record,
                    "engine_id",
                    None,
                )
                != "OLA-058"
                or getattr(
                    invocation_record,
                    "invocation_completed",
                    None,
                )
                is not True
                or getattr(
                    invocation_record,
                    "read_only",
                    None,
                )
                is not True
                or getattr(
                    invocation_record,
                    "execution_allowed",
                    None,
                )
                is not False
            ):
                raise (
                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(
                        "OLA-058 controlled invocation result failed closed"
                    )
                )

            record = (
                OracleProductionLiveShadowControlledLaunchPermitExecutionRecord(
                    schema_version=SCHEMA_VERSION,
                    engine_id=ENGINE_ID,
                    execution_type=EXECUTION_TYPE,

                    invocation_permit_identity=(
                        permit_identity
                    ),

                    source_package_identity=id(
                        launch_package
                    ),

                    runner_identity=id(
                        runner
                    ),

                    controlled_invoker_identity=id(
                        controlled_invoker
                    ),

                    callable_binding_identity=id(
                        callable_binding
                    ),

                    invocation_permit_consumed=True,

                    controlled_invocation_completed=True,

                    **checks,
                )
            )

            return (
                record,
                result,
            )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "EXECUTION_TYPE",
    "OracleProductionLiveShadowControlledLaunchPermitExecutionError",
    "OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked",
    "OracleProductionLiveShadowControlledLaunchPermitExecutionRecord",
    "OracleProductionLiveShadowControlledLaunchPermitExecutor",
]
