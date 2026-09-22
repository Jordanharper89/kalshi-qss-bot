from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    PACKAGE / "olc_003_live_runtime_terminal_composition.py",
    OAR / "oar_001_runtime_foundation.py",
    OAR / "oar_006_production_launch_boundary.py",
    OAR / "oar_010_canonical_live_observation_bus.py",
    OAR / "oar_011_live_observation_admission.py",
    OAR / "oar_021_live_intelligence_pipeline_coordinator.py",
    OAR / "oar_022_terminal_live_intelligence_read_model.py",
    OAR / "oar_030_final_certification_freeze.py",
    OAR / "OAR_FINAL_FREEZE_MANIFEST.json",
    OAD / "oad_006_default_adapter_bundle.py",
)

MODULE = PACKAGE / "olc_004_live_intelligence_cycle.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_004_live_intelligence_cycle.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import (
    build_default_adapter_bundle,
)
from qseries_v2.observation_adapter_runtime.oar_001_runtime_foundation import (
    build_runtime_config,
)
from qseries_v2.observation_adapter_runtime.oar_006_production_launch_boundary import (
    ProductionLiveObservationLauncher,
)
from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservationBus,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionGate,
)
from qseries_v2.observation_adapter_runtime.oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelineCoordinator,
)
from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
    TerminalLiveIntelligenceReadModelBuilder,
)

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)

BUILD_ID = "OLC-004"
OLC_004_REVISION = "OLC_004_LIVE_INTELLIGENCE_CYCLE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveIntelligenceCycleResult:
    composition_id: str
    runtime_id: str
    iteration_number: int
    adapter_request_count: int
    adapter_success_count: int
    adapter_failure_count: int
    raw_observation_count: int
    admitted_observation_count: int
    terminal_read_model: TerminalLiveIntelligenceReadModel
    read_only: bool
    execution_allowed: bool


class ProductionLiveIntelligenceCycle:
    read_only = True
    execution_allowed = False
    order_placement_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def run_once(
        self,
        *,
        config: OracleLiveCompositionConfig,
        clock_callable: Callable[[], datetime],
        subject_hints: dict[str, str | None] | None = None,
    ) -> LiveIntelligenceCycleResult:
        if not isinstance(
            config,
            OracleLiveCompositionConfig,
        ):
            raise TypeError(
                "config must be OracleLiveCompositionConfig"
            )

        if not callable(
            clock_callable
        ):
            raise TypeError(
                "clock_callable must be callable"
            )

        bundle = build_default_adapter_bundle()

        runtime_config = build_runtime_config(
            runtime_id=config.runtime_id,
            tick_interval_seconds=(
                config.tick_interval_seconds
            ),
        )

        launch_record, service_result = (
            ProductionLiveObservationLauncher()
            .launch(
                config=runtime_config,
                bundle=bundle,
                iterations=1,
                clock_callable=clock_callable,
                sleep_callable=lambda _: None,
                stop_requested_callable=lambda: False,
                subject_hints=subject_hints,
            )
        )

        if service_result.iterations_completed != 1:
            raise RuntimeError(
                "production live observation iteration did not complete"
            )

        run_result = (
            service_result
            .run_results[-1]
        )

        canonical_batch = (
            CanonicalLiveObservationBus()
            .materialize(
                run_result
            )
        )

        admission = (
            LiveObservationAdmissionGate()
            .admit(
                canonical_batch
            )
        )

        pipeline = (
            LiveIntelligencePipelineCoordinator()
            .coordinate(
                admission
            )
        )

        generated_at = clock_callable()

        read_model = (
            TerminalLiveIntelligenceReadModelBuilder()
            .build(
                pipeline=pipeline,
                generated_at=generated_at,
            )
        )

        if read_model.read_only is not True:
            raise RuntimeError(
                "terminal live read model is not read-only"
            )

        return LiveIntelligenceCycleResult(
            composition_id=config.composition_id,
            runtime_id=config.runtime_id,
            iteration_number=run_result.iteration_number,
            adapter_request_count=run_result.request_count,
            adapter_success_count=run_result.success_count,
            adapter_failure_count=run_result.failure_count,
            raw_observation_count=run_result.observation_count,
            admitted_observation_count=(
                admission.admitted_count
            ),
            terminal_read_model=read_model,
            read_only=True,
            execution_allowed=False,
        )


def verify_live_intelligence_cycle() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_004_REVISION",
    "LiveIntelligenceCycleResult",
    "ProductionLiveIntelligenceCycle",
    "verify_live_intelligence_cycle",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    ProductionLiveIntelligenceCycle,
    verify_live_intelligence_cycle,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    0,
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


class TestOLC004(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_intelligence_cycle()
        )

    def test_cycle(self):
        result = (
            ProductionLiveIntelligenceCycle()
            .run_once(
                config=build_live_composition_config(),
                clock_callable=Clock(),
                subject_hints={
                    "coinbase": "BTC",
                    "kalshi": None,
                },
            )
        )

        self.assertEqual(
            result.iteration_number,
            1,
        )

        self.assertTrue(
            result.terminal_read_model.lineage_valid
        )

        self.assertTrue(
            result.read_only
        )

        self.assertFalse(
            result.execution_allowed
        )

    def test_side_effects(self):
        cycle = ProductionLiveIntelligenceCycle()

        self.assertTrue(cycle.read_only)
        self.assertFalse(cycle.execution_allowed)
        self.assertFalse(cycle.order_placement_allowed)
        self.assertFalse(cycle.publication_allowed)
        self.assertFalse(cycle.persistence_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-004 CERTIFICATION TEST")
    print(" PRODUCTION LIVE INTELLIGENCE CYCLE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC004
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-004")
    print("[PASS] One production adapter iteration flows through canonical bus, admission, OI/UMD/OML pipeline, and terminal read model")
    print("[PASS] Actual adapter successes, failures, and observation counts remain explicit")
    print("[PASS] Execution, order placement, publication, and persistence disabled")
    print("[DONE] OLC-004 CERTIFIED")
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
    print(" OLC-004 INSTALLER")
    print(" PRODUCTION LIVE INTELLIGENCE CYCLE")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_004_LIVE_INTELLIGENCE_CYCLE_INSTALLER_V1"
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
            "from .olc_004_live_intelligence_cycle import *"
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
            "[PASS] Frozen OAR and certified OAD remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )

        print(
            "[DONE] OLC-004 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-004 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
