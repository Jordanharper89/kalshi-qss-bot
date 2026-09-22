from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"

UPSTREAMS = (
    PACKAGE / "olc_001_live_composition_foundation.py",
    PACKAGE / "olc_002_terminal_runtime_resolver.py",
    PACKAGE / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json",
    OAR / "oar_006_production_launch_boundary.py",
    OAR / "oar_010_canonical_live_observation_bus.py",
    OAR / "oar_011_live_observation_admission.py",
    OAR / "oar_021_live_intelligence_pipeline_coordinator.py",
    OAR / "oar_022_terminal_live_intelligence_read_model.py",
    OAR / "oar_029_terminal_live_activation.py",
    OAR / "oar_030_final_certification_freeze.py",
    OAD / "oad_006_default_adapter_bundle.py",
)

MODULE = PACKAGE / "olc_003_live_runtime_terminal_composition.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_003_live_runtime_terminal_composition.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .olc_001_live_composition_foundation import (
    OracleLiveCompositionConfig,
)

BUILD_ID = "OLC-003"
OLC_003_REVISION = "OLC_003_LIVE_RUNTIME_TERMINAL_COMPOSITION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveRuntimeTerminalCompositionPlan:
    composition_id: str
    runtime_id: str
    terminal_id: str
    terminal_module_name: str
    terminal_symbol_name: str
    stages: tuple[str, ...]
    legacy_terminal_fallback: bool
    continuous_runtime_required: bool
    live_read_model_required: bool
    interactive_terminal_required: bool
    read_only: bool
    execution_allowed: bool


class LiveRuntimeTerminalCompositionPlanner:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    order_placement_allowed = False

    def build(
        self,
        *,
        config: OracleLiveCompositionConfig,
        terminal_module_name: str,
        terminal_symbol_name: str,
    ) -> LiveRuntimeTerminalCompositionPlan:
        if not isinstance(
            config,
            OracleLiveCompositionConfig,
        ):
            raise TypeError(
                "config must be OracleLiveCompositionConfig"
            )

        terminal_module_name = str(
            terminal_module_name
        ).strip()

        terminal_symbol_name = str(
            terminal_symbol_name
        ).strip()

        if not terminal_module_name:
            raise ValueError(
                "terminal_module_name must not be empty"
            )

        if not terminal_symbol_name:
            raise ValueError(
                "terminal_symbol_name must not be empty"
            )

        stages = (
            "build_default_adapter_bundle",
            "start_production_live_observation_runtime",
            "materialize_canonical_live_observations",
            "admit_live_observations",
            "build_live_intelligence_pipeline",
            "build_terminal_live_read_model",
            "activate_read_only_live_query_path",
            "enter_existing_interactive_oracle_terminal",
        )

        return LiveRuntimeTerminalCompositionPlan(
            composition_id=config.composition_id,
            runtime_id=config.runtime_id,
            terminal_id=config.terminal_id,
            terminal_module_name=terminal_module_name,
            terminal_symbol_name=terminal_symbol_name,
            stages=stages,
            legacy_terminal_fallback=(
                config.legacy_terminal_fallback
            ),
            continuous_runtime_required=True,
            live_read_model_required=True,
            interactive_terminal_required=True,
            read_only=True,
            execution_allowed=False,
        )


def verify_live_runtime_terminal_composition() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_003_REVISION",
    "LiveRuntimeTerminalCompositionPlan",
    "LiveRuntimeTerminalCompositionPlanner",
    "verify_live_runtime_terminal_composition",
]
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_001_live_composition_foundation import (
    build_live_composition_config,
)
from qseries_v2.oracle_live_composition.olc_003_live_runtime_terminal_composition import (
    LiveRuntimeTerminalCompositionPlanner,
    verify_live_runtime_terminal_composition,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_runtime_terminal_composition()
        )

    def test_plan(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        top = payload[
            "top_candidate"
        ]

        plan = (
            LiveRuntimeTerminalCompositionPlanner()
            .build(
                config=(
                    build_live_composition_config()
                ),
                terminal_module_name=(
                    top["module_name"]
                ),
                terminal_symbol_name=(
                    top["symbol_name"]
                ),
            )
        )

        self.assertTrue(
            plan.continuous_runtime_required
        )

        self.assertTrue(
            plan.live_read_model_required
        )

        self.assertTrue(
            plan.interactive_terminal_required
        )

        self.assertTrue(
            plan.legacy_terminal_fallback
        )

        self.assertEqual(
            plan.stages[-1],
            "enter_existing_interactive_oracle_terminal",
        )

    def test_side_effects(self):
        planner = (
            LiveRuntimeTerminalCompositionPlanner()
        )

        self.assertTrue(
            planner.read_only
        )

        self.assertFalse(
            planner.execution_allowed
        )

        self.assertFalse(
            planner.publication_allowed
        )

        self.assertFalse(
            planner.order_placement_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-003 CERTIFICATION TEST")
    print(" LIVE RUNTIME / TERMINAL COMPOSITION PLAN")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC003
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-003")
    print("[PASS] Live adapters, production observation runtime, canonical bus, OI/UMD/OML pipeline, terminal read model, and interactive terminal compose into one production plan")
    print("[PASS] Existing interactive Oracle Terminal remains the final command-loop boundary")
    print("[PASS] Execution, order placement, and publication remain disabled")
    print("[DONE] OLC-003 CERTIFIED")
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
    print(" OLC-003 INSTALLER")
    print(" LIVE RUNTIME / TERMINAL COMPOSITION PLAN")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_003_LIVE_RUNTIME_TERMINAL_COMPOSITION_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    manifest = json.loads(
        (
            PACKAGE
            / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    top = manifest.get(
        "top_candidate"
    )

    if not top:
        raise RuntimeError(
            "OLC-002 terminal runtime manifest has no top candidate"
        )

    if top.get("score", 0) < 8:
        raise RuntimeError(
            "OLC-002 terminal runtime boundary is not sufficiently certified"
        )

    print(
        "[PASS] Exact interactive terminal boundary consumed: "
        f"{top['module_name']}.{top['symbol_name']}"
    )

    hashes = {
        path: sha(path)
        for path in UPSTREAMS
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__MANIFEST__",
            repr(
                str(
                    PACKAGE
                    / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json"
                )
            ),
        )
    )

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
            test_source,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .olc_003_live_runtime_terminal_composition import *"
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
            "[PASS] Production live runtime / interactive terminal composition contract established"
        )

        print(
            "[DONE] OLC-003 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-003 installation failed; affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
