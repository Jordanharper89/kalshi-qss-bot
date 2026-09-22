from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAR-001"
INSTALLER_REVISION = "OAR_001_LIVE_OBSERVATION_RUNTIME_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
    OI / "OI_FINAL_FREEZE_MANIFEST.json",
)

MODULE = PACKAGE / "oar_001_runtime_foundation.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oar_001_runtime_foundation.py"

MODULE_SOURCE = """
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

BUILD_ID = "OAR-001"
OAR_001_REVISION = "OAR_001_LIVE_OBSERVATION_RUNTIME_FOUNDATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

RUNTIME_STATUS_IDLE = "idle"
RUNTIME_STATUS_RUNNING = "running"
RUNTIME_STATUS_STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class LiveObservationRuntimeConfig:
    runtime_id: str
    tick_interval_seconds: int
    max_adapter_failures: int
    read_only: bool
    execution_allowed: bool


@dataclass(frozen=True, slots=True)
class LiveObservationRuntimeState:
    runtime_id: str
    status: str
    iteration_number: int
    consecutive_failures: int
    stop_requested: bool
    read_only: bool
    execution_allowed: bool


def build_runtime_config(
    *,
    runtime_id: str,
    tick_interval_seconds: int = 5,
    max_adapter_failures: int = 3,
) -> LiveObservationRuntimeConfig:
    runtime_id_value = str(runtime_id).strip()

    if not runtime_id_value:
        raise ValueError("runtime_id must not be empty")

    if not isinstance(tick_interval_seconds, int):
        raise TypeError("tick_interval_seconds must be int")

    if tick_interval_seconds < 1:
        raise ValueError(
            "tick_interval_seconds must be greater than zero"
        )

    if not isinstance(max_adapter_failures, int):
        raise TypeError("max_adapter_failures must be int")

    if max_adapter_failures < 1:
        raise ValueError(
            "max_adapter_failures must be greater than zero"
        )

    return LiveObservationRuntimeConfig(
        runtime_id=runtime_id_value,
        tick_interval_seconds=tick_interval_seconds,
        max_adapter_failures=max_adapter_failures,
        read_only=True,
        execution_allowed=False,
    )


def initial_runtime_state(
    config: LiveObservationRuntimeConfig,
) -> LiveObservationRuntimeState:
    if not isinstance(config, LiveObservationRuntimeConfig):
        raise TypeError(
            "config must be LiveObservationRuntimeConfig"
        )

    return LiveObservationRuntimeState(
        runtime_id=config.runtime_id,
        status=RUNTIME_STATUS_IDLE,
        iteration_number=0,
        consecutive_failures=0,
        stop_requested=False,
        read_only=True,
        execution_allowed=False,
    )


def verify_live_observation_runtime_foundation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_001_REVISION",
    "RUNTIME_STATUS_IDLE",
    "RUNTIME_STATUS_RUNNING",
    "RUNTIME_STATUS_STOPPED",
    "LiveObservationRuntimeConfig",
    "LiveObservationRuntimeState",
    "build_runtime_config",
    "initial_runtime_state",
    "verify_live_observation_runtime_foundation",
]
""".lstrip()

TEST_SOURCE = """
from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import (
    OAR_001_REVISION,
    RUNTIME_STATUS_IDLE,
    build_runtime_config,
    initial_runtime_state,
    verify_live_observation_runtime_foundation,
)


class TestOAR001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_observation_runtime_foundation()
        )

    def test_config(self):
        config = build_runtime_config(
            runtime_id="oracle.live.observation",
            tick_interval_seconds=5,
            max_adapter_failures=3,
        )
        self.assertTrue(config.read_only)
        self.assertFalse(config.execution_allowed)

    def test_initial_state(self):
        config = build_runtime_config(
            runtime_id="oracle.live.observation"
        )
        state = initial_runtime_state(config)
        self.assertEqual(state.status, RUNTIME_STATUS_IDLE)
        self.assertEqual(state.iteration_number, 0)

    def test_invalid_tick(self):
        with self.assertRaises(ValueError):
            build_runtime_config(
                runtime_id="runtime",
                tick_interval_seconds=0,
            )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-001 CERTIFICATION TEST")
    print(" UNIVERSAL LIVE OBSERVATION RUNTIME FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAR001
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-001")
    print(f"[PASS] Revision: {OAR_001_REVISION}")
    print("[PASS] Universal live-observation runtime config and state contracts certified")
    print("[PASS] Cadence, failure bounds, runtime identity, and lifecycle state are explicit")
    print("[PASS] Execution, order placement, funds movement, and portfolio mutation disabled")
    print("[DONE] OAR-001 CERTIFIED")
""".lstrip()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_checked(p: Path, source: str) -> None:
    ast.parse(source, filename=str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {p.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAR-001 INSTALLER")
    print(" UNIVERSAL LIVE OBSERVATION RUNTIME FOUNDATION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for upstream in UPSTREAMS:
        if not upstream.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {upstream}"
            )

    hashes = {p: sha(p) for p in UPSTREAMS}

    PACKAGE.mkdir(parents=True, exist_ok=True)

    affected = (MODULE, TEST, INIT)
    backups = {
        p: p.read_bytes() if p.exists() else None
        for p in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oar_001_runtime_foundation import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        for p, expected in hashes.items():
            if sha(p) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {p.name}"
                )

        print("[PASS] OAD-006 and frozen OI verified unchanged")
        print("[PASS] In-memory compilation verified")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Universal live runtime established outside frozen OI")
        print("[DONE] OAR-001 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for p, original in backups.items():
            if original is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(original)
        print("[ROLLBACK] OAR-001 installation failed; affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
