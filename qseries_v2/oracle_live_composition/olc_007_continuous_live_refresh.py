from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Event, Thread
from typing import Callable

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)
from .olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
    LiveReadModelRefreshService,
    LiveReadModelSnapshot,
)

BUILD_ID = "OLC-007"
OLC_007_REVISION = "OLC_007_CONTINUOUS_LIVE_REFRESH_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ContinuousLiveRefreshStatus:
    running: bool
    generation: int
    last_error: str | None
    read_only: bool
    execution_allowed: bool


class ContinuousLiveReadModelRefreshWorker:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False
    order_placement_allowed = False

    def __init__(
        self,
        *,
        config: OracleLiveCompositionConfig,
        clock_callable: Callable[[], datetime],
        subject_hints: dict[str, str | None] | None = None,
        store: AtomicLiveReadModelStore | None = None,
        wait_callable: Callable[[float], None] | None = None,
    ):
        if not isinstance(
            config,
            OracleLiveCompositionConfig,
        ):
            raise TypeError(
                "config must be OracleLiveCompositionConfig"
            )

        if not callable(clock_callable):
            raise TypeError(
                "clock_callable must be callable"
            )

        self.config = config
        self.clock_callable = clock_callable
        self.subject_hints = subject_hints
        self.store = (
            store
            if store is not None
            else AtomicLiveReadModelStore()
        )
        self.refresh_service = (
            LiveReadModelRefreshService(
                self.store
            )
        )
        self.wait_callable = wait_callable
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_error: str | None = None

    def refresh_once(
        self,
    ) -> LiveReadModelSnapshot:
        try:
            snapshot = (
                self.refresh_service
                .refresh_once(
                    config=self.config,
                    clock_callable=self.clock_callable,
                    subject_hints=self.subject_hints,
                )
            )
            self._last_error = None
            return snapshot
        except Exception as exc:
            self._last_error = (
                f"{type(exc).__name__}: {exc}"
            )
            raise

    def _wait(
        self,
        seconds: float,
    ) -> None:
        if self.wait_callable is not None:
            self.wait_callable(seconds)
        else:
            self._stop_event.wait(seconds)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.refresh_once()
            except Exception:
                pass

            if self._stop_event.is_set():
                break

            self._wait(
                float(
                    self.config.tick_interval_seconds
                )
            )

    def start(self) -> None:
        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            raise RuntimeError(
                "continuous live refresh already running"
            )

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run_loop,
            name="oracle-live-read-refresh",
            daemon=True,
        )

        self._thread.start()

    def stop(
        self,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=timeout_seconds
            )

    def snapshot(
        self,
    ) -> LiveReadModelSnapshot:
        return self.store.snapshot()

    def status(
        self,
    ) -> ContinuousLiveRefreshStatus:
        running = bool(
            self._thread is not None
            and self._thread.is_alive()
        )

        snapshot = self.store.snapshot()

        return ContinuousLiveRefreshStatus(
            running=running,
            generation=snapshot.generation,
            last_error=self._last_error,
            read_only=True,
            execution_allowed=False,
        )


def verify_continuous_live_refresh() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_007_REVISION",
    "ContinuousLiveRefreshStatus",
    "ContinuousLiveReadModelRefreshWorker",
    "verify_continuous_live_refresh",
]
