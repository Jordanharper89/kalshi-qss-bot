"""OLA-063 Production Live Shadow Persistent Service Activation."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


SCHEMA_VERSION = "OLA-063"
ENGINE_ID = "OLA-063"


class OracleProductionLiveShadowPersistentServiceActivationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLiveShadowPersistentServiceActivationRecord:
    schema_version: str
    engine_id: str
    exact_production_graph_required: bool
    ola062_controlled_execution_boundary_present: bool
    existing_service_runner_required: bool
    service_start_callable_resolved: bool
    service_start_invoked: bool
    single_activation_enforced: bool
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


class OracleProductionLiveShadowPersistentServiceActivator:
    read_only = True
    execution_allowed = False

    _RUNNER_KEYS = (
        "service_runner",
        "production_service_runner",
        "shadow_service_runner",
        "oracle_live_acquisition_service_runner",
    )

    _START_METHODS = (
        "run",
        "start",
        "run_service",
        "start_service",
        "serve",
    )

    def __init__(self) -> None:
        self._lock = Lock()
        self._activated_graph_ids: set[int] = set()

    def _resolve_runner(self, graph: dict[str, Any]) -> Any:
        for key in self._RUNNER_KEYS:
            runner = graph.get(key)
            if runner is not None:
                return runner

        for value in graph.values():
            if (
                getattr(value, "read_only", None) is True
                and getattr(value, "execution_allowed", None) is False
                and any(callable(getattr(value, name, None)) for name in self._START_METHODS)
            ):
                return value

        raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
            "Unable to resolve the existing read-only service runner"
        )

    def activate(
        self,
        *,
        production_graph: dict[str, Any],
        start_kwargs: dict[str, Any] | None = None,
    ) -> tuple[OracleProductionLiveShadowPersistentServiceActivationRecord, Any]:
        if not isinstance(production_graph, dict):
            raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                "OLA-063 requires the exact OLA-030 production graph mapping"
            )

        required_keys = (
            "production_controlled_launch_package_assembler",
            "production_controlled_launch_package_consumer",
            "production_controlled_launch_permit_executor",
        )

        missing = [key for key in required_keys if key not in production_graph]
        if missing:
            raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                "Frozen launch-control boundary missing: " + ", ".join(missing)
            )

        graph_identity = id(production_graph)

        with self._lock:
            if graph_identity in self._activated_graph_ids:
                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                    "This exact production graph was already activated"
                )

            runner = self._resolve_runner(production_graph)

            if getattr(runner, "read_only", None) is not True:
                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                    "Service runner is not read-only"
                )

            if getattr(runner, "execution_allowed", None) is not False:
                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                    "Service runner exposes execution permission"
                )

            start_callable = None
            for name in self._START_METHODS:
                candidate = getattr(runner, name, None)
                if callable(candidate):
                    start_callable = candidate
                    break

            if start_callable is None:
                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(
                    "Existing service runner has no supported public start method"
                )

            self._activated_graph_ids.add(graph_identity)

        try:
            result = start_callable(**dict(start_kwargs or {}))
        except Exception:
            with self._lock:
                self._activated_graph_ids.discard(graph_identity)
            raise

        record = OracleProductionLiveShadowPersistentServiceActivationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            exact_production_graph_required=True,
            ola062_controlled_execution_boundary_present=True,
            existing_service_runner_required=True,
            service_start_callable_resolved=True,
            service_start_invoked=True,
            single_activation_enforced=True,
        )

        return record, result


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OracleProductionLiveShadowPersistentServiceActivationBlocked",
    "OracleProductionLiveShadowPersistentServiceActivationRecord",
    "OracleProductionLiveShadowPersistentServiceActivator",
]
