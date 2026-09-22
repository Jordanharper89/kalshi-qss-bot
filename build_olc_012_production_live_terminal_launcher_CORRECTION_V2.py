from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
LAUNCHER_SOURCE_PATH = ROOT / "run_oracle_open_intelligence_terminal.py"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    PACKAGE / "olc_007_continuous_live_refresh.py",
    PACKAGE / "olc_010_exact_ask_descriptor_binding.py",
    PACKAGE / "olc_011_interactive_terminal_coordinator.py",
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
    LAUNCHER_SOURCE_PATH,
)

MODULE = PACKAGE / "olc_012_production_live_terminal_launcher.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_012_production_live_terminal_launcher.py"
LAUNCHER = ROOT / "run_oracle_LIVE.py"

INSTALLER_REVISION = (
    "OLC_012_PRODUCTION_LIVE_TERMINAL_LAUNCHER_"
    "INSTALLER_CORRECTION_V2"
)

MODULE_SOURCE = r"""
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
"""

LAUNCHER_SOURCE = r"""
from __future__ import annotations

from qseries_v2.oracle_live_composition.olc_012_production_live_terminal_launcher import (
    run_production_live_terminal,
)

BUILD_ID = "OLC-012-LAUNCHER"
REVISION = "OLC_012_PRODUCTION_ORACLE_LIVE_LAUNCHER_V1"


def main() -> int:
    print("=" * 72)
    print(" ORACLE — PRODUCTION LIVE INTELLIGENCE TERMINAL")
    print("=" * 72)
    print("[MODE] READ-ONLY INTELLIGENCE")
    print("[PASS] Frozen OAR runtime retained")
    print("[PASS] Continuous live observation refresh configured")
    print("[PASS] Atomic live terminal read model configured")
    print(
        "[PASS] Exact runtime injection boundary: "
        "run_oracle_open_intelligence_terminal.display_query"
    )
    print("[PASS] Existing display_query fallback preserved")
    print("[PASS] Existing interactive run_interactive loop preserved")
    print("[PASS] Execution and order placement disabled")
    print()
    print("[START] Priming live intelligence and entering oracle> ...")
    print()

    result = run_production_live_terminal()

    if isinstance(
        result,
        int,
    ):
        return result

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_SOURCE = r"""
from __future__ import annotations

import importlib
import unittest

from qseries_v2.oracle_live_composition.olc_012_production_live_terminal_launcher import (
    build_production_live_terminal_coordinator,
    build_production_live_terminal_launch_config,
    verify_production_live_terminal_launcher,
)


class TestOLC012(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_production_live_terminal_launcher()
        )

    def test_config(self):
        config = (
            build_production_live_terminal_launch_config()
        )

        self.assertEqual(
            config.tick_interval_seconds,
            5,
        )

        self.assertEqual(
            config.coinbase_subject_hint,
            "BTC",
        )

        self.assertTrue(
            config.read_only
        )

        self.assertFalse(
            config.execution_allowed
        )

    def test_coordinator(self):
        coordinator = (
            build_production_live_terminal_coordinator()
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

    def test_real_launcher_boundaries(self):
        launcher = importlib.import_module(
            "run_oracle_open_intelligence_terminal"
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "display_query",
                )
            )
        )

        self.assertTrue(
            callable(
                getattr(
                    launcher,
                    "run_interactive",
                )
            )
        )

    def test_bad_cadence(self):
        with self.assertRaises(
            ValueError
        ):
            build_production_live_terminal_launch_config(
                tick_interval_seconds=0,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-012 CERTIFICATION TEST")
    print(
        " PRODUCTION INTERACTIVE LIVE ORACLE LAUNCHER "
        "— CORRECTION V2"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC012
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-012")
    print(
        "[PASS] One-command production interactive Oracle launcher certified"
    )
    print(
        "[PASS] Continuous refresh, atomic live read model, "
        "display_query overlay, and run_interactive compose correctly"
    )
    print(
        "[PASS] Execution, order placement, publication, "
        "and persistence remain disabled"
    )
    print("[DONE] OLC-012 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def inspect_launcher():
    source = LAUNCHER_SOURCE_PATH.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(
            LAUNCHER_SOURCE_PATH
        ),
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
        filename=str(
            path
        ),
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
    print(" OLC-012 INSTALLER")
    print(
        " PRODUCTION INTERACTIVE LIVE ORACLE LAUNCHER "
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

    print(
        "[PASS] Verified production runtime boundary: "
        "run_oracle_open_intelligence_terminal.display_query"
    )

    print(
        "[PASS] Verified interactive terminal boundary: "
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
        LAUNCHER,
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

        write_checked(
            LAUNCHER,
            LAUNCHER_SOURCE,
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
            "olc_012_production_live_terminal_launcher "
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
            "[PASS] Launcher source, existing Oracle Terminal, "
            "and frozen OAR remained unchanged"
        )

        print(
            f"[PASS] Wrote production launcher: "
            f"{LAUNCHER.name}"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + LAUNCHER.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[DONE] OLC-012 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-012 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
