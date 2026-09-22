from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

BUILD_ID = "OAR-001"
OAR_001_REVISION = "OAR_001_LIVE_OBSERVATION_RUNTIME_FOUNDATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

RUNTIME_STATUS_IDLE = "idle"
RUNTIME_STATUS_RUNNING = "running"
RUNTIME_STATUS_STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class LiveObservationRuntimeConfig:
    runtime_id: str
    tick_interval_seconds: int
    max_adapter_failures: int
    read_only: bool
    execution_allowed: bool


@dataclass(frozen=True, slots=True)
class LiveObservationRuntimeState:
    runtime_id: str
    status: str
    iteration_number: int
    consecutive_failures: int
    stop_requested: bool
    read_only: bool
    execution_allowed: bool


def build_runtime_config(
    *,
    runtime_id: str,
    tick_interval_seconds: int = 5,
    max_adapter_failures: int = 3,
) -> LiveObservationRuntimeConfig:
    runtime_id_value = str(runtime_id).strip()

    if not runtime_id_value:
        raise ValueError("runtime_id must not be empty")

    if not isinstance(tick_interval_seconds, int):
        raise TypeError("tick_interval_seconds must be int")

    if tick_interval_seconds < 1:
        raise ValueError(
            "tick_interval_seconds must be greater than zero"
        )

    if not isinstance(max_adapter_failures, int):
        raise TypeError("max_adapter_failures must be int")

    if max_adapter_failures < 1:
        raise ValueError(
            "max_adapter_failures must be greater than zero"
        )

    return LiveObservationRuntimeConfig(
        runtime_id=runtime_id_value,
        tick_interval_seconds=tick_interval_seconds,
        max_adapter_failures=max_adapter_failures,
        read_only=True,
        execution_allowed=False,
    )


def initial_runtime_state(
    config: LiveObservationRuntimeConfig,
) -> LiveObservationRuntimeState:
    if not isinstance(config, LiveObservationRuntimeConfig):
        raise TypeError(
            "config must be LiveObservationRuntimeConfig"
        )

    return LiveObservationRuntimeState(
        runtime_id=config.runtime_id,
        status=RUNTIME_STATUS_IDLE,
        iteration_number=0,
        consecutive_failures=0,
        stop_requested=False,
        read_only=True,
        execution_allowed=False,
    )


def verify_live_observation_runtime_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_001_REVISION",
    "RUNTIME_STATUS_IDLE",
    "RUNTIME_STATUS_RUNNING",
    "RUNTIME_STATUS_STOPPED",
    "LiveObservationRuntimeConfig",
    "LiveObservationRuntimeState",
    "build_runtime_config",
    "initial_runtime_state",
    "verify_live_observation_runtime_foundation",
]
