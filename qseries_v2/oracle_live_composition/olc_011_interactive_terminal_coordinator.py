from __future__ import annotations

import importlib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
    build_live_composition_config,
)
from .olc_007_continuous_live_refresh import (
    ContinuousLiveReadModelRefreshWorker,
)
from .olc_010_exact_ask_descriptor_binding import (
    build_live_display_query,
)

BUILD_ID = "OLC-011"
OLC_011_REVISION = "OLC_011_INTERACTIVE_TERMINAL_COORDINATOR_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False

TERMINAL_MODULE_NAME = "run_oracle_open_intelligence_terminal"
TERMINAL_SYMBOL_NAME = "run_interactive"
INJECTION_SYMBOL_NAME = "display_query"


@dataclass(frozen=True, slots=True)
class InteractiveTerminalCompositionStatus:
    refresh_running: bool
    generation: int
    terminal_module_name: str
    terminal_symbol_name: str
    injection_symbol_name: str
    overlay_active: bool
    read_only: bool
    execution_allowed: bool


@contextmanager
def live_display_query_overlay(
    *,
    store,
):
    terminal_module = importlib.import_module(
        TERMINAL_MODULE_NAME
    )

    original_display_query = getattr(
        terminal_module,
        INJECTION_SYMBOL_NAME,
        None,
    )

    if not callable(
        original_display_query
    ):
        raise RuntimeError(
            "verified display_query boundary is missing"
        )

    live_display_query = build_live_display_query(
        store=store,
        original_display_query=original_display_query,
    )

    setattr(
        terminal_module,
        INJECTION_SYMBOL_NAME,
        live_display_query,
    )

    try:
        yield live_display_query
    finally:
        setattr(
            terminal_module,
            INJECTION_SYMBOL_NAME,
            original_display_query,
        )


class InteractiveTerminalCompositionCoordinator:
    read_only = True
    execution_allowed = False
    order_placement_allowed = False
    publication_allowed = False
    persistence_allowed = False
    source_mutation_allowed = False

    def __init__(
        self,
        *,
        config: OracleLiveCompositionConfig | None = None,
        clock_callable: Callable[[], datetime] | None = None,
        subject_hints: dict[str, str | None] | None = None,
    ):
        self.config = (
            config
            if config is not None
            else build_live_composition_config()
        )

        self.clock_callable = (
            clock_callable
            if clock_callable is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )

        self.subject_hints = (
            subject_hints
            if subject_hints is not None
            else {
                "coinbase": "BTC",
                "kalshi": None,
            }
        )

        self.worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=self.config,
                clock_callable=self.clock_callable,
                subject_hints=self.subject_hints,
            )
        )

    def prime(self):
        return self.worker.refresh_once()

    def status(
        self,
        *,
        overlay_active: bool = False,
    ) -> InteractiveTerminalCompositionStatus:
        worker_status = self.worker.status()

        return InteractiveTerminalCompositionStatus(
            refresh_running=worker_status.running,
            generation=worker_status.generation,
            terminal_module_name=TERMINAL_MODULE_NAME,
            terminal_symbol_name=TERMINAL_SYMBOL_NAME,
            injection_symbol_name=INJECTION_SYMBOL_NAME,
            overlay_active=overlay_active,
            read_only=True,
            execution_allowed=False,
        )

    def run_interactive(self):
        terminal_module = importlib.import_module(
            TERMINAL_MODULE_NAME
        )

        terminal_callable = getattr(
            terminal_module,
            TERMINAL_SYMBOL_NAME,
            None,
        )

        if not callable(
            terminal_callable
        ):
            raise RuntimeError(
                "verified interactive terminal callable missing"
            )

        # Prime first so the first /ask already has a snapshot.
        self.prime()

        # Keep the snapshot fresh while the terminal remains open.
        self.worker.start()

        try:
            with live_display_query_overlay(
                store=self.worker.store,
            ):
                return terminal_callable()
        finally:
            self.worker.stop()


def verify_interactive_terminal_coordinator() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert TERMINAL_MODULE_NAME == "run_oracle_open_intelligence_terminal"
    assert TERMINAL_SYMBOL_NAME == "run_interactive"
    assert INJECTION_SYMBOL_NAME == "display_query"
    return True


__all__ = [
    "BUILD_ID",
    "OLC_011_REVISION",
    "InteractiveTerminalCompositionStatus",
    "live_display_query_overlay",
    "InteractiveTerminalCompositionCoordinator",
    "verify_interactive_terminal_coordinator",
]
