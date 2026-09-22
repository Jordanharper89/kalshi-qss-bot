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
    OAR / "oar_022_terminal_live_intelligence_read_model.py",
    OAR / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_005_live_read_model_refresh.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_005_live_read_model_refresh.py"

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
    LiveReadModelRefreshService,
    verify_live_read_model_refresh,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    10,
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


class TestOLC005(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_read_model_refresh()
        )

    def test_empty_store(self):
        store = AtomicLiveReadModelStore()
        snapshot = store.snapshot()

        self.assertEqual(
            snapshot.generation,
            0,
        )

        self.assertIsNone(
            snapshot.read_model
        )

    def test_refresh(self):
        service = (
            LiveReadModelRefreshService()
        )

        snapshot = service.refresh_once(
            config=build_live_composition_config(),
            clock_callable=Clock(),
            subject_hints={
                "coinbase": "BTC",
                "kalshi": None,
            },
        )

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

        self.assertTrue(
            snapshot.read_model.read_only
        )

    def test_side_effects(self):
        service = LiveReadModelRefreshService()

        self.assertTrue(service.read_only)
        self.assertFalse(service.execution_allowed)
        self.assertFalse(service.publication_allowed)
        self.assertFalse(service.persistence_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-005 CERTIFICATION TEST")
    print(" ATOMIC LIVE READ MODEL REFRESH SERVICE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC005
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-005")
    print("[PASS] Production live intelligence cycles atomically refresh one in-memory terminal read model")
    print("[PASS] Terminal readers receive generation-stable snapshots")
    print("[PASS] No persistence, publication, or execution introduced")
    print("[DONE] OLC-005 CERTIFIED")
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
    print(" OLC-005 INSTALLER")
    print(" ATOMIC LIVE READ MODEL REFRESH SERVICE")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_005_LIVE_READ_MODEL_REFRESH_INSTALLER_V1"
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
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .olc_005_live_read_model_refresh import *"
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
            "[PASS] Frozen OAR and certified OLC-004 remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[DONE] OLC-005 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-005 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
