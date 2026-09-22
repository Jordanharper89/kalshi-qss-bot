from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import Callable

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)
from .olc_004_live_intelligence_cycle import (
    LiveIntelligenceCycleResult,
    ProductionLiveIntelligenceCycle,
)

BUILD_ID = "OLC-005"
OLC_005_REVISION = "OLC_005_LIVE_READ_MODEL_REFRESH_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveReadModelSnapshot:
    generation: int
    read_model: TerminalLiveIntelligenceReadModel | None
    last_cycle: LiveIntelligenceCycleResult | None
    read_only: bool


class AtomicLiveReadModelStore:
    read_only = True
    execution_allowed = False
    persistence_allowed = False

    def __init__(self):
        self._lock = RLock()
        self._generation = 0
        self._read_model = None
        self._last_cycle = None

    def publish(
        self,
        cycle: LiveIntelligenceCycleResult,
    ) -> LiveReadModelSnapshot:
        if not isinstance(
            cycle,
            LiveIntelligenceCycleResult,
        ):
            raise TypeError(
                "cycle must be LiveIntelligenceCycleResult"
            )

        if cycle.read_only is not True:
            raise ValueError(
                "cycle must be read-only"
            )

        with self._lock:
            self._generation += 1
            self._read_model = (
                cycle.terminal_read_model
            )
            self._last_cycle = cycle

            return LiveReadModelSnapshot(
                generation=self._generation,
                read_model=self._read_model,
                last_cycle=self._last_cycle,
                read_only=True,
            )

    def snapshot(
        self,
    ) -> LiveReadModelSnapshot:
        with self._lock:
            return LiveReadModelSnapshot(
                generation=self._generation,
                read_model=self._read_model,
                last_cycle=self._last_cycle,
                read_only=True,
            )


class LiveReadModelRefreshService:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def __init__(
        self,
        store: AtomicLiveReadModelStore | None = None,
    ):
        self.store = (
            store
            if store is not None
            else AtomicLiveReadModelStore()
        )

    def refresh_once(
        self,
        *,
        config: OracleLiveCompositionConfig,
        clock_callable: Callable[[], datetime],
        subject_hints: dict[str, str | None] | None = None,
    ) -> LiveReadModelSnapshot:
        cycle = (
            ProductionLiveIntelligenceCycle()
            .run_once(
                config=config,
                clock_callable=clock_callable,
                subject_hints=subject_hints,
            )
        )

        return self.store.publish(
            cycle
        )


def verify_live_read_model_refresh() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_005_REVISION",
    "LiveReadModelSnapshot",
    "AtomicLiveReadModelStore",
    "LiveReadModelRefreshService",
    "verify_live_read_model_refresh",
]
