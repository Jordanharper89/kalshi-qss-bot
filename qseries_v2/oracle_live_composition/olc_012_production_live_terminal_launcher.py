from __future__ import annotations

from dataclasses import dataclass

from .olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from .olc_011_interactive_terminal_coordinator import (
    InteractiveTerminalCompositionCoordinator,
)

BUILD_ID = "OLC-012"
OLC_012_REVISION = "OLC_012_PRODUCTION_LIVE_TERMINAL_LAUNCHER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ProductionLiveTerminalLaunchConfig:
    tick_interval_seconds: int
    coinbase_subject_hint: str | None
    kalshi_subject_hint: str | None
    read_only: bool
    execution_allowed: bool


def build_production_live_terminal_launch_config(
    *,
    tick_interval_seconds: int = 5,
    coinbase_subject_hint: str | None = "BTC",
    kalshi_subject_hint: str | None = None,
) -> ProductionLiveTerminalLaunchConfig:
    if not isinstance(
        tick_interval_seconds,
        int,
    ):
        raise TypeError(
            "tick_interval_seconds must be int"
        )

    if tick_interval_seconds < 1:
        raise ValueError(
            "tick_interval_seconds must be positive"
        )

    return ProductionLiveTerminalLaunchConfig(
        tick_interval_seconds=(
            tick_interval_seconds
        ),
        coinbase_subject_hint=(
            coinbase_subject_hint
        ),
        kalshi_subject_hint=(
            kalshi_subject_hint
        ),
        read_only=True,
        execution_allowed=False,
    )


def build_production_live_terminal_coordinator(
    *,
    launch_config: ProductionLiveTerminalLaunchConfig | None = None,
) -> InteractiveTerminalCompositionCoordinator:
    launch_config = (
        launch_config
        if launch_config is not None
        else build_production_live_terminal_launch_config()
    )

    config = build_live_composition_config(
        tick_interval_seconds=(
            launch_config.tick_interval_seconds
        ),
    )

    return InteractiveTerminalCompositionCoordinator(
        config=config,
        subject_hints={
            "coinbase": (
                launch_config.coinbase_subject_hint
            ),
            "kalshi": (
                launch_config.kalshi_subject_hint
            ),
        },
    )


def run_production_live_terminal(
    *,
    launch_config: ProductionLiveTerminalLaunchConfig | None = None,
):
    coordinator = (
        build_production_live_terminal_coordinator(
            launch_config=launch_config,
        )
    )

    return coordinator.run_interactive()


def verify_production_live_terminal_launcher() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_012_REVISION",
    "ProductionLiveTerminalLaunchConfig",
    "build_production_live_terminal_launch_config",
    "build_production_live_terminal_coordinator",
    "run_production_live_terminal",
    "verify_production_live_terminal_launcher",
]
