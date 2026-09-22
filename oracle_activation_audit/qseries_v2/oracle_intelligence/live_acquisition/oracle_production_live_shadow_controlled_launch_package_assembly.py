"""
OLA-060 Production Live Shadow Controlled Launch Package Assembly.

Assembles the already-validated production launch components into one
immutable, auditable package:

OLA-056 single-use launch token
    -> OLA-057 exact runner launch binding
    -> OLA-059 exact runner bound-method binding
    -> OLA-058 controlled synchronous invoker

OLA-060 performs no invocation. It only verifies cross-component identity
consistency and produces a package that a later launch boundary may consume.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "OLA-060"
ENGINE_ID = "OLA-060"
PACKAGE_TYPE = "oracle_production_live_shadow_controlled_launch_package"


class OracleProductionLiveShadowControlledLaunchPackageError(ValueError):
    pass


class OracleProductionLiveShadowControlledLaunchPackageBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowControlledLaunchPackageRecord:
    schema_version: str
    engine_id: str
    package_type: str

    launch_token_identity: int
    launch_binding_identity: int
    callable_binding_identity: int
    controlled_invoker_identity: int
    runner_identity: int

    launch_token_valid: bool
    launch_binding_valid: bool
    callable_binding_valid: bool
    controlled_invoker_valid: bool

    token_to_launch_binding_identity_preserved: bool
    launch_binding_to_callable_binding_identity_preserved: bool
    callable_binding_to_runner_identity_preserved: bool

    controlled_launch_package_ready: bool

    launch_invoked: bool = False
    callable_invoked: bool = False

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
            raise OracleProductionLiveShadowControlledLaunchPackageError(
                "OLA-060 schema_version mismatch"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleProductionLiveShadowControlledLaunchPackageError(
                "OLA-060 engine_id mismatch"
            )

        if self.package_type != PACKAGE_TYPE:
            raise OracleProductionLiveShadowControlledLaunchPackageError(
                "OLA-060 package_type mismatch"
            )

        required = (
            self.launch_token_valid,
            self.launch_binding_valid,
            self.callable_binding_valid,
            self.controlled_invoker_valid,
            self.token_to_launch_binding_identity_preserved,
            self.launch_binding_to_callable_binding_identity_preserved,
            self.callable_binding_to_runner_identity_preserved,
            self.controlled_launch_package_ready,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(
                "OLA-060 launch package failed closed"
            )

        forbidden = (
            self.launch_invoked,
            self.callable_invoked,
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
            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(
                "OLA-060 observed forbidden activity"
            )


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowControlledLaunchPackage:
    record: OracleProductionLiveShadowControlledLaunchPackageRecord
    launch_token: Any
    launch_binding: Any
    callable_binding: Any
    controlled_invoker: Any
    runner: Any


class OracleProductionLiveShadowControlledLaunchPackageAssembler:
    read_only = True
    execution_allowed = False

    def assemble(
        self,
        *,
        launch_token: Any,
        launch_binding: Any,
        callable_binding: Any,
        controlled_invoker: Any,
        runner: Any,
    ) -> OracleProductionLiveShadowControlledLaunchPackage:
        callable_record = getattr(
            callable_binding,
            "record",
            None,
        )

        checks = {
            "launch_token_valid": (
                getattr(launch_token, "schema_version", None) == "OLA-056"
                and getattr(launch_token, "engine_id", None) == "OLA-056"
                and getattr(
                    launch_token,
                    "authorization_consumed",
                    None,
                )
                is True
                and getattr(
                    launch_token,
                    "launch_token_issued",
                    None,
                )
                is True
                and getattr(
                    launch_token,
                    "launch_invoked",
                    None,
                )
                is False
                and getattr(
                    launch_token,
                    "read_only",
                    None,
                )
                is True
                and getattr(
                    launch_token,
                    "execution_allowed",
                    None,
                )
                is False
            ),

            "launch_binding_valid": (
                getattr(
                    launch_binding,
                    "schema_version",
                    None,
                )
                == "OLA-057"
                and getattr(
                    launch_binding,
                    "engine_id",
                    None,
                )
                == "OLA-057"
                and getattr(
                    launch_binding,
                    "launch_binding_ready",
                    None,
                )
                is True
                and getattr(
                    launch_binding,
                    "launch_invoked",
                    None,
                )
                is False
            ),

            "callable_binding_valid": (
                getattr(
                    callable_record,
                    "schema_version",
                    None,
                )
                == "OLA-059"
                and getattr(
                    callable_record,
                    "engine_id",
                    None,
                )
                == "OLA-059"
                and getattr(
                    callable_record,
                    "callable_binding_ready",
                    None,
                )
                is True
                and getattr(
                    callable_record,
                    "callable_invoked",
                    None,
                )
                is False
            ),

            "controlled_invoker_valid": (
                getattr(
                    controlled_invoker,
                    "read_only",
                    None,
                )
                is True
                and getattr(
                    controlled_invoker,
                    "execution_allowed",
                    None,
                )
                is False
            ),

            "token_to_launch_binding_identity_preserved": (
                getattr(
                    launch_binding,
                    "launch_token_identity",
                    None,
                )
                == id(launch_token)
            ),

            "launch_binding_to_callable_binding_identity_preserved": (
                getattr(
                    callable_record,
                    "source_launch_binding_identity",
                    None,
                )
                == id(launch_binding)
            ),

            "callable_binding_to_runner_identity_preserved": (
                getattr(
                    callable_record,
                    "runner_identity",
                    None,
                )
                == id(runner)
                and getattr(
                    launch_binding,
                    "runner_identity",
                    None,
                )
                == id(runner)
            ),
        }

        if not all(checks.values()):
            failed = ", ".join(
                name
                for name, passed in checks.items()
                if not passed
            )

            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(
                "OLA-060 launch package identity mismatch: "
                f"{failed}"
            )

        record = (
            OracleProductionLiveShadowControlledLaunchPackageRecord(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                package_type=PACKAGE_TYPE,

                launch_token_identity=id(
                    launch_token
                ),

                launch_binding_identity=id(
                    launch_binding
                ),

                callable_binding_identity=id(
                    callable_binding
                ),

                controlled_invoker_identity=id(
                    controlled_invoker
                ),

                runner_identity=id(
                    runner
                ),

                controlled_launch_package_ready=True,

                **checks,
            )
        )

        return (
            OracleProductionLiveShadowControlledLaunchPackage(
                record=record,
                launch_token=launch_token,
                launch_binding=launch_binding,
                callable_binding=callable_binding,
                controlled_invoker=controlled_invoker,
                runner=runner,
            )
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PACKAGE_TYPE",
    "OracleProductionLiveShadowControlledLaunchPackageError",
    "OracleProductionLiveShadowControlledLaunchPackageBlocked",
    "OracleProductionLiveShadowControlledLaunchPackageRecord",
    "OracleProductionLiveShadowControlledLaunchPackage",
    "OracleProductionLiveShadowControlledLaunchPackageAssembler",
]
