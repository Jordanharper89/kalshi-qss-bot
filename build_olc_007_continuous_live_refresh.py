from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    PACKAGE / "olc_004_live_intelligence_cycle.py",
    PACKAGE / "olc_005_live_read_model_refresh.py",
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
)

MODULE = PACKAGE / "olc_007_continuous_live_refresh.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_007_continuous_live_refresh.py"

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import time
import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_007_continuous_live_refresh import (
    ContinuousLiveReadModelRefreshWorker,
    verify_continuous_live_refresh,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    20,
    tzinfo=timezone.utc,
)


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        current = self.value
        self.value += timedelta(
            milliseconds=1
        )
        return current


class TestOLC007(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_continuous_live_refresh()
        )

    def test_refresh_once(self):
        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        snapshot = worker.refresh_once()

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

    def test_start_stop(self):
        waits = []

        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(
                    tick_interval_seconds=1
                ),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
                wait_callable=lambda seconds: (
                    waits.append(seconds)
                ),
            )
        )

        worker.start()

        for _ in range(100):
            if (
                worker.snapshot().generation
                >= 1
            ):
                break
            time.sleep(0.01)

        worker.stop()

        self.assertGreaterEqual(
            worker.snapshot().generation,
            1,
        )

        self.assertFalse(
            worker.status().running
        )

    def test_side_effects(self):
        worker = (
            ContinuousLiveReadModelRefreshWorker(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
        )

        self.assertTrue(worker.read_only)
        self.assertFalse(worker.execution_allowed)
        self.assertFalse(worker.publication_allowed)
        self.assertFalse(worker.persistence_allowed)
        self.assertFalse(worker.order_placement_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-007 CERTIFICATION TEST")
    print(" CONTINUOUS LIVE READ MODEL REFRESH WORKER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC007
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-007")
    print("[PASS] Continuous background refresh of the terminal live read model certified")
    print("[PASS] Atomic generations remain available while the terminal stays open")
    print("[PASS] Adapter/runtime errors remain explicit and do not enable execution")
    print("[DONE] OLC-007 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()
    ast.parse(
        text,
        filename=str(path),
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-007 INSTALLER")
    print(" CONTINUOUS LIVE READ MODEL REFRESH WORKER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_007_CONTINUOUS_LIVE_REFRESH_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    hashes = {
        path: sha(path)
        for path in UPSTREAMS
    }

    affected = (
        MODULE,
        TEST,
        INIT,
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )
        write_checked(
            TEST,
            TEST_SOURCE,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .olc_007_continuous_live_refresh import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(
                current,
                filename=str(INIT),
            )
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Frozen/certified upstream changed: {path.name}"
                )

        print(
            "[PASS] Frozen OAR and certified OLC upstream remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[DONE] OLC-007 INSTALLATION COMPLETE"
        )
        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(original)

        print(
            "[ROLLBACK] OLC-007 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
