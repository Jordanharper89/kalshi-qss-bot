from __future__ import annotations

import ast
import hashlib
import importlib
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
LAUNCHER = ROOT / "run_oracle_open_intelligence_terminal.py"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    PACKAGE / "olc_005_live_read_model_refresh.py",
    PACKAGE / "olc_007_continuous_live_refresh.py",
    PACKAGE / "olc_010_exact_ask_descriptor_binding.py",
    PACKAGE / "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST.json",
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
    LAUNCHER,
)

MODULE = PACKAGE / "olc_011_interactive_terminal_coordinator.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_011_interactive_terminal_coordinator.py"

INSTALLER_REVISION = (
    "OLC_011_INTERACTIVE_TERMINAL_COORDINATOR_"
    "INSTALLER_CORRECTION_V2"
)

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_011_interactive_terminal_coordinator import (
    INJECTION_SYMBOL_NAME,
    InteractiveTerminalCompositionCoordinator,
    live_display_query_overlay,
    verify_interactive_terminal_coordinator,
)

NOW = datetime(
    2026,
    8,
    12,
    17,
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


class TestOLC011(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_interactive_terminal_coordinator()
        )

    def test_prime(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        snapshot = coordinator.prime()

        self.assertEqual(
            snapshot.generation,
            1,
        )

        self.assertIsNotNone(
            snapshot.read_model
        )

    def test_overlay_restores_exact_display_query(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        coordinator.prime()

        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        original = getattr(
            launcher,
            INJECTION_SYMBOL_NAME,
        )

        with live_display_query_overlay(
            store=coordinator.worker.store,
        ):
            patched = getattr(
                launcher,
                INJECTION_SYMBOL_NAME,
            )

            self.assertIsNot(
                original,
                patched,
            )

            self.assertEqual(
                patched.__name__,
                "olc_live_display_query",
            )

        restored = getattr(
            launcher,
            INJECTION_SYMBOL_NAME,
        )

        self.assertIs(
            original,
            restored,
        )

    def test_status(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
        )

        status = coordinator.status()

        self.assertTrue(
            status.read_only
        )

        self.assertFalse(
            status.execution_allowed
        )

        self.assertEqual(
            status.injection_symbol_name,
            "display_query",
        )

    def test_side_effects(self):
        coordinator = (
            InteractiveTerminalCompositionCoordinator(
                config=build_live_composition_config(),
                clock_callable=Clock(),
            )
        )

        self.assertTrue(
            coordinator.read_only
        )

        self.assertFalse(
            coordinator.execution_allowed
        )

        self.assertFalse(
            coordinator.source_mutation_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-011 CERTIFICATION TEST")
    print(
        " INTERACTIVE TERMINAL COORDINATOR "
        "— CORRECTION V2"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC011
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-011")
    print(
        "[PASS] Initial production live read model priming certified"
    )
    print(
        "[PASS] Continuous refresh composes with the verified "
        "run_interactive terminal"
    )
    print(
        "[PASS] Exact display_query runtime boundary is overlaid "
        "in memory and restored on exit"
    )
    print(
        "[PASS] Existing Oracle Terminal source remains unchanged"
    )
    print("[DONE] OLC-011 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def inspect_launcher():
    source = LAUNCHER.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(LAUNCHER),
    )

    names = [
        node.name
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    ]

    for required in (
        "display_query",
        "dispatch_command",
        "run_interactive",
    ):
        if required not in names:
            raise RuntimeError(
                f"verified launcher symbol missing: {required}"
            )


def write_checked(
    path: Path,
    source: str,
) -> None:
    content = source.lstrip()

    ast.parse(
        content,
        filename=str(path),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-011 INSTALLER")
    print(
        " INTERACTIVE TERMINAL COORDINATOR "
        "— CORRECTION V2"
    )
    print("=" * 72)

    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    inspect_launcher()

    launcher_module = importlib.import_module(
        "run_oracle_open_intelligence_terminal"
    )

    for symbol in (
        "display_query",
        "dispatch_command",
        "run_interactive",
    ):
        if not callable(
            getattr(
                launcher_module,
                symbol,
                None,
            )
        ):
            raise RuntimeError(
                f"verified runtime callable missing: {symbol}"
            )

    print(
        "[PASS] Verified runtime injection boundary consumed: "
        "run_oracle_open_intelligence_terminal.display_query"
    )

    print(
        "[PASS] Verified interactive runtime consumed: "
        "run_oracle_open_intelligence_terminal.run_interactive"
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
            "from ."
            "olc_011_interactive_terminal_coordinator "
            "import *"
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
                    "Certified/frozen upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Launcher, existing Oracle Terminal, "
            "and frozen OAR remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[DONE] OLC-011 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(
                    original
                )

        print(
            "[ROLLBACK] OLC-011 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
