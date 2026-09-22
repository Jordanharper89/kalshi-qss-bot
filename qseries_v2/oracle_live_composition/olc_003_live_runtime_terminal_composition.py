from __future__ import annotations

from dataclasses import dataclass

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)

BUILD_ID = "OLC-003"
OLC_003_REVISION = "OLC_003_LIVE_RUNTIME_TERMINAL_COMPOSITION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveRuntimeTerminalCompositionPlan:
    composition_id: str
    runtime_id: str
    terminal_id: str
    terminal_module_name: str
    terminal_symbol_name: str
    stages: tuple[str, ...]
    legacy_terminal_fallback: bool
    continuous_runtime_required: bool
    live_read_model_required: bool
    interactive_terminal_required: bool
    read_only: bool
    execution_allowed: bool


class LiveRuntimeTerminalCompositionPlanner:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    order_placement_allowed = False

    def build(
        self,
        *,
        config: OracleLiveCompositionConfig,
        terminal_module_name: str,
        terminal_symbol_name: str,
    ) -> LiveRuntimeTerminalCompositionPlan:
        if not isinstance(
            config,
            OracleLiveCompositionConfig,
        ):
            raise TypeError(
                "config must be OracleLiveCompositionConfig"
            )

        terminal_module_name = str(
            terminal_module_name
        ).strip()

        terminal_symbol_name = str(
            terminal_symbol_name
        ).strip()

        if not terminal_module_name:
            raise ValueError(
                "terminal_module_name must not be empty"
            )

        if not terminal_symbol_name:
            raise ValueError(
                "terminal_symbol_name must not be empty"
            )

        stages = (
            "build_default_adapter_bundle",
            "start_production_live_observation_runtime",
            "materialize_canonical_live_observations",
            "admit_live_observations",
            "build_live_intelligence_pipeline",
            "build_terminal_live_read_model",
            "activate_read_only_live_query_path",
            "enter_existing_interactive_oracle_terminal",
        )

        return LiveRuntimeTerminalCompositionPlan(
            composition_id=config.composition_id,
            runtime_id=config.runtime_id,
            terminal_id=config.terminal_id,
            terminal_module_name=terminal_module_name,
            terminal_symbol_name=terminal_symbol_name,
            stages=stages,
            legacy_terminal_fallback=(
                config.legacy_terminal_fallback
            ),
            continuous_runtime_required=True,
            live_read_model_required=True,
            interactive_terminal_required=True,
            read_only=True,
            execution_allowed=False,
        )


def verify_live_runtime_terminal_composition() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_003_REVISION",
    "LiveRuntimeTerminalCompositionPlan",
    "LiveRuntimeTerminalCompositionPlanner",
    "verify_live_runtime_terminal_composition",
]
