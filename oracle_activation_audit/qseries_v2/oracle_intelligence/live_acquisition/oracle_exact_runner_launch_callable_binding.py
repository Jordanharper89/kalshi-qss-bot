"""
OLA-059 Exact Runner Launch Callable Binding.

Fail-closed binding between the exact OLA-023 production runner instance and
the exact bound method that a later controlled launch invocation may call.

This closes the remaining OLA-058 gap where an arbitrary callable could be
supplied even when the runner identity itself was correct.

OLA-059 does not invoke the callable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SCHEMA_VERSION = "OLA-059"
ENGINE_ID = "OLA-059"
BINDING_TYPE = "oracle_exact_runner_launch_callable_binding"


class OracleExactRunnerLaunchCallableBindingError(ValueError):
    pass


class OracleExactRunnerLaunchCallableBindingBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExactRunnerLaunchCallableBindingRecord:
    schema_version: str
    engine_id: str
    binding_type: str
    source_launch_binding_schema_version: str
    source_launch_binding_engine_id: str
    source_launch_binding_identity: int
    runner_identity: int
    callable_owner_identity: int
    callable_function_identity: int
    launch_binding_valid: bool
    exact_runner_identity_preserved: bool
    callable_is_bound_method: bool
    callable_bound_to_exact_runner: bool
    callable_binding_ready: bool
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
            raise OracleExactRunnerLaunchCallableBindingError(
                "OLA-059 schema_version mismatch"
            )
        if self.engine_id != ENGINE_ID:
            raise OracleExactRunnerLaunchCallableBindingError(
                "OLA-059 engine_id mismatch"
            )
        if self.binding_type != BINDING_TYPE:
            raise OracleExactRunnerLaunchCallableBindingError(
                "OLA-059 binding_type mismatch"
            )

        required = (
            self.launch_binding_valid,
            self.exact_runner_identity_preserved,
            self.callable_is_bound_method,
            self.callable_bound_to_exact_runner,
            self.callable_binding_ready,
            self.read_only,
        )

        if not all(value is True for value in required):
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 callable binding failed closed"
            )

        forbidden = (
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
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 observed forbidden activity"
            )


@dataclass(frozen=True, slots=True)
class OracleExactRunnerLaunchCallableBinding:
    record: OracleExactRunnerLaunchCallableBindingRecord
    launch_callable: Callable[[], Any]


class OracleExactRunnerLaunchCallableBinder:
    read_only = True
    execution_allowed = False

    def bind(
        self,
        *,
        launch_binding: Any,
        runner: Any,
        launch_callable: Callable[[], Any],
    ) -> OracleExactRunnerLaunchCallableBinding:
        if (
            getattr(launch_binding, "schema_version", None) != "OLA-057"
            or getattr(launch_binding, "engine_id", None) != "OLA-057"
            or getattr(launch_binding, "launch_binding_ready", None) is not True
            or getattr(launch_binding, "launch_invoked", None) is not False
            or getattr(launch_binding, "runner_identity", None) != id(runner)
            or getattr(launch_binding, "read_only", None) is not True
            or getattr(launch_binding, "execution_allowed", None) is not False
        ):
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-057 launch binding is not eligible for OLA-059"
            )

        if (
            getattr(runner, "read_only", None) is not True
            or getattr(runner, "execution_allowed", None) is not False
        ):
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 runner invariants failed closed"
            )

        if not callable(launch_callable):
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 launch_callable is not callable"
            )

        callable_owner = getattr(launch_callable, "__self__", None)
        callable_function = getattr(launch_callable, "__func__", None)

        if callable_owner is None or callable_function is None:
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 requires a bound runner method"
            )

        if callable_owner is not runner:
            raise OracleExactRunnerLaunchCallableBindingBlocked(
                "OLA-059 callable is not bound to the exact runner"
            )

        record = OracleExactRunnerLaunchCallableBindingRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            binding_type=BINDING_TYPE,
            source_launch_binding_schema_version=launch_binding.schema_version,
            source_launch_binding_engine_id=launch_binding.engine_id,
            source_launch_binding_identity=id(launch_binding),
            runner_identity=id(runner),
            callable_owner_identity=id(callable_owner),
            callable_function_identity=id(callable_function),
            launch_binding_valid=True,
            exact_runner_identity_preserved=True,
            callable_is_bound_method=True,
            callable_bound_to_exact_runner=True,
            callable_binding_ready=True,
        )

        return OracleExactRunnerLaunchCallableBinding(
            record=record,
            launch_callable=launch_callable,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "BINDING_TYPE",
    "OracleExactRunnerLaunchCallableBindingError",
    "OracleExactRunnerLaunchCallableBindingBlocked",
    "OracleExactRunnerLaunchCallableBindingRecord",
    "OracleExactRunnerLaunchCallableBinding",
    "OracleExactRunnerLaunchCallableBinder",
]
