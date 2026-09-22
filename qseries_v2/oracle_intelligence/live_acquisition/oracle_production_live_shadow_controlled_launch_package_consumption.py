"""
OLA-061 Production Live Shadow Controlled Launch Package Consumption.

Consumes an OLA-060 controlled launch package exactly once and issues a
single-use invocation permit.

This module does not invoke the OLA-058 controlled invoker, does not invoke the
bound runner method, and does not start any process, thread, or background
loop.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


SCHEMA_VERSION = "OLA-061"
ENGINE_ID = "OLA-061"
PERMIT_TYPE = "oracle_production_live_shadow_single_use_invocation_permit"


class OracleProductionLiveShadowControlledLaunchPackageConsumptionError(
    ValueError
):
    pass


class OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowSingleUseInvocationPermit:
    schema_version: str
    engine_id: str
    permit_type: str

    source_package_schema_version: str
    source_package_engine_id: str
    source_package_identity: int

    launch_token_identity: int
    launch_binding_identity: int
    callable_binding_identity: int
    controlled_invoker_identity: int
    runner_identity: int

    package_consumed: bool
    invocation_permit_issued: bool

    invocation_permit_consumed: bool = False
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
            raise (
                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(
                    "OLA-061 schema_version mismatch"
                )
            )

        if self.engine_id != ENGINE_ID:
            raise (
                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(
                    "OLA-061 engine_id mismatch"
                )
            )

        if self.permit_type != PERMIT_TYPE:
            raise (
                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(
                    "OLA-061 permit_type mismatch"
                )
            )

        required = (
            self.package_consumed,
            self.invocation_permit_issued,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise (
                OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(
                    "OLA-061 permit issuance failed closed"
                )
            )

        forbidden = (
            self.invocation_permit_consumed,
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
            raise (
                OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(
                    "OLA-061 observed forbidden activity"
                )
            )


class OracleProductionLiveShadowControlledLaunchPackageConsumer:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._consumed_package_identities: set[int] = set()

    def consume(
        self,
        *,
        launch_package: Any,
    ) -> OracleProductionLiveShadowSingleUseInvocationPermit:
        with self._lock:
            package_identity = id(
                launch_package
            )

            if (
                package_identity
                in self._consumed_package_identities
            ):
                raise (
                    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(
                        "OLA-060 launch package already consumed"
                    )
                )

            record = getattr(
                launch_package,
                "record",
                None,
            )

            checks = (
                getattr(
                    record,
                    "schema_version",
                    None,
                )
                == "OLA-060",

                getattr(
                    record,
                    "engine_id",
                    None,
                )
                == "OLA-060",

                getattr(
                    record,
                    "controlled_launch_package_ready",
                    None,
                )
                is True,

                getattr(
                    record,
                    "launch_invoked",
                    None,
                )
                is False,

                getattr(
                    record,
                    "callable_invoked",
                    None,
                )
                is False,

                getattr(
                    record,
                    "read_only",
                    None,
                )
                is True,

                getattr(
                    record,
                    "execution_allowed",
                    None,
                )
                is False,
            )

            if not all(checks):
                raise (
                    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(
                        "OLA-060 launch package is not eligible "
                        "for OLA-061 consumption"
                    )
                )

            self._consumed_package_identities.add(
                package_identity
            )

            return (
                OracleProductionLiveShadowSingleUseInvocationPermit(
                    schema_version=SCHEMA_VERSION,
                    engine_id=ENGINE_ID,
                    permit_type=PERMIT_TYPE,

                    source_package_schema_version=(
                        record.schema_version
                    ),

                    source_package_engine_id=(
                        record.engine_id
                    ),

                    source_package_identity=(
                        package_identity
                    ),

                    launch_token_identity=(
                        record.launch_token_identity
                    ),

                    launch_binding_identity=(
                        record.launch_binding_identity
                    ),

                    callable_binding_identity=(
                        record.callable_binding_identity
                    ),

                    controlled_invoker_identity=(
                        record.controlled_invoker_identity
                    ),

                    runner_identity=(
                        record.runner_identity
                    ),

                    package_consumed=True,

                    invocation_permit_issued=True,
                )
            )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PERMIT_TYPE",
    "OracleProductionLiveShadowControlledLaunchPackageConsumptionError",
    "OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked",
    "OracleProductionLiveShadowSingleUseInvocationPermit",
    "OracleProductionLiveShadowControlledLaunchPackageConsumer",
]
