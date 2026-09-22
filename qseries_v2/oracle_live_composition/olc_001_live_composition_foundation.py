from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-001"
OLC_001_REVISION = "OLC_001_LIVE_COMPOSITION_FOUNDATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
PUBLICATION_ALLOWED = False
PORTFOLIO_MUTATION_ALLOWED = False

STATE_IDLE = "idle"
STATE_READY = "ready"
STATE_ACTIVE = "active"
STATE_STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class OracleLiveCompositionConfig:
    composition_id: str
    runtime_id: str
    terminal_id: str
    tick_interval_seconds: int
    legacy_terminal_fallback: bool
    read_only: bool
    execution_allowed: bool


@dataclass(frozen=True, slots=True)
class OracleLiveCompositionState:
    composition_id: str
    state: str
    live_runtime_ready: bool
    terminal_ready: bool
    read_model_ready: bool
    read_only: bool
    execution_allowed: bool


def build_live_composition_config(
    *,
    composition_id: str = "oracle.live.composition.v1",
    runtime_id: str = "oracle.live.observation.production",
    terminal_id: str = "oracle.terminal.live.read.v1",
    tick_interval_seconds: int = 5,
    legacy_terminal_fallback: bool = True,
) -> OracleLiveCompositionConfig:
    composition_id = str(composition_id).strip()
    runtime_id = str(runtime_id).strip()
    terminal_id = str(terminal_id).strip()

    if not composition_id:
        raise ValueError("composition_id must not be empty")

    if not runtime_id:
        raise ValueError("runtime_id must not be empty")

    if not terminal_id:
        raise ValueError("terminal_id must not be empty")

    if not isinstance(tick_interval_seconds, int):
        raise TypeError("tick_interval_seconds must be int")

    if tick_interval_seconds < 1:
        raise ValueError("tick_interval_seconds must be positive")

    if legacy_terminal_fallback is not True:
        raise ValueError(
            "legacy terminal fallback must remain enabled"
        )

    return OracleLiveCompositionConfig(
        composition_id=composition_id,
        runtime_id=runtime_id,
        terminal_id=terminal_id,
        tick_interval_seconds=tick_interval_seconds,
        legacy_terminal_fallback=True,
        read_only=True,
        execution_allowed=False,
    )


def initial_live_composition_state(
    config: OracleLiveCompositionConfig,
) -> OracleLiveCompositionState:
    if not isinstance(
        config,
        OracleLiveCompositionConfig,
    ):
        raise TypeError(
            "config must be OracleLiveCompositionConfig"
        )

    return OracleLiveCompositionState(
        composition_id=config.composition_id,
        state=STATE_IDLE,
        live_runtime_ready=False,
        terminal_ready=False,
        read_model_ready=False,
        read_only=True,
        execution_allowed=False,
    )


def verify_live_composition_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PORTFOLIO_MUTATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_001_REVISION",
    "STATE_IDLE",
    "STATE_READY",
    "STATE_ACTIVE",
    "STATE_STOPPED",
    "OracleLiveCompositionConfig",
    "OracleLiveCompositionState",
    "build_live_composition_config",
    "initial_live_composition_state",
    "verify_live_composition_foundation",
]
