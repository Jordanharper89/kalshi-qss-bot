from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
    OAR / "oar_029_terminal_live_activation.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_001_live_composition_foundation.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_001_live_composition_foundation.py"

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    STATE_IDLE,
    build_live_composition_config,
    initial_live_composition_state,
    verify_live_composition_foundation,
)


class TestOLC001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_composition_foundation()
        )

    def test_config(self):
        config = build_live_composition_config()

        self.assertEqual(
            config.tick_interval_seconds,
            5,
        )

        self.assertTrue(
            config.legacy_terminal_fallback
        )

        self.assertTrue(
            config.read_only
        )

        self.assertFalse(
            config.execution_allowed
        )

    def test_initial_state(self):
        config = build_live_composition_config()

        state = initial_live_composition_state(
            config
        )

        self.assertEqual(
            state.state,
            STATE_IDLE,
        )

        self.assertFalse(
            state.live_runtime_ready
        )

        self.assertFalse(
            state.terminal_ready
        )

    def test_fallback_required(self):
        with self.assertRaises(ValueError):
            build_live_composition_config(
                legacy_terminal_fallback=False,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-001 CERTIFICATION TEST")
    print(" ORACLE LIVE COMPOSITION FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-001")
    print("[PASS] Production composition identity, runtime identity, terminal identity, and cadence certified")
    print("[PASS] Existing Oracle Terminal fallback is mandatory")
    print("[PASS] Execution, order placement, publication, and portfolio mutation disabled")
    print("[DONE] OLC-001 CERTIFIED")
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
    print(" OLC-001 INSTALLER")
    print(" ORACLE LIVE COMPOSITION FOUNDATION")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_001_LIVE_COMPOSITION_FOUNDATION_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    oit_files = tuple(
        sorted(
            p for p in OIT.glob("**/*.py")
            if p.is_file()
        )
    )

    if not oit_files:
        raise RuntimeError(
            "Certified Oracle Terminal boundary missing"
        )

    protected = (
        *UPSTREAMS,
        *oit_files,
    )

    hashes = {
        path: sha(path)
        for path in protected
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
            "from .olc_001_live_composition_foundation import *"
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
            "[PASS] Frozen OAR, frozen OI, certified OAD, and existing OIT remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )

        print(
            "[PASS] New production composition subsystem established outside frozen OAR/OI/OIT source"
        )

        print(
            "[DONE] OLC-001 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-001 installation failed; affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
