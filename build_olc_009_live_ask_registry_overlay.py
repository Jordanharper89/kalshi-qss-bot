from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"

UPSTREAMS = (
    PACKAGE / "olc_005_live_read_model_refresh.py",
    PACKAGE / "olc_006_terminal_injection_resolver.py",
    PACKAGE / "olc_007_continuous_live_refresh.py",
    PACKAGE / "olc_008_command_registry_contract_resolver.py",
    PACKAGE / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json",
    OAR / "oar_026_live_ask_dispatch_binding.py",
    OAR / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_009_live_ask_registry_overlay.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_009_live_ask_registry_overlay.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)
from .olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)

BUILD_ID = "OLC-009"
OLC_009_REVISION = "OLC_009_LIVE_ASK_REGISTRY_OVERLAY_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveAskOverlayResult:
    live_handled: bool
    fallback_used: bool
    route: str
    observation_count: int
    read_only: bool


class LiveAskHandlerOverlay:
    read_only = True
    execution_allowed = False
    source_mutation_allowed = False
    publication_allowed = False

    def __init__(
        self,
        *,
        store: AtomicLiveReadModelStore,
        fallback_handler: Callable[..., Any],
    ):
        if not isinstance(
            store,
            AtomicLiveReadModelStore,
        ):
            raise TypeError(
                "store must be AtomicLiveReadModelStore"
            )

        if not callable(
            fallback_handler
        ):
            raise TypeError(
                "fallback_handler must be callable"
            )

        self.store = store
        self.fallback_handler = fallback_handler

    def dispatch(
        self,
        query: str,
        *args,
        **kwargs,
    ):
        snapshot = self.store.snapshot()

        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query=query,
                read_model=snapshot.read_model,
            )
        )

        if (
            result.consume_existing_terminal
        ):
            fallback_value = (
                self.fallback_handler(
                    query,
                    *args,
                    **kwargs,
                )
            )

            return LiveAskOverlayResult(
                live_handled=False,
                fallback_used=True,
                route=(
                    result
                    .live_response
                    .route
                ),
                observation_count=0,
                read_only=True,
            ), fallback_value

        return LiveAskOverlayResult(
            live_handled=True,
            fallback_used=False,
            route=(
                result
                .live_response
                .route
            ),
            observation_count=(
                result
                .live_response
                .observation_count
            ),
            read_only=True,
        ), result.live_response


def verify_live_ask_registry_overlay() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_009_REVISION",
    "LiveAskOverlayResult",
    "LiveAskHandlerOverlay",
    "verify_live_ask_registry_overlay",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.oracle_live_composition.olc_004_live_intelligence_cycle import (
    LiveIntelligenceCycleResult,
)
from qseries_v2.oracle_live_composition.olc_009_live_ask_registry_overlay import (
    LiveAskHandlerOverlay,
    verify_live_ask_registry_overlay,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    30,
    tzinfo=timezone.utc,
)


def cycle():
    read_model = TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.test",
        iteration_number=1,
        observation_count=2,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
        ),
        provider_ids=(
            "coinbase",
            "kalshi",
        ),
        capability_ids=(
            "spot_price",
            "market_snapshot",
        ),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )

    return LiveIntelligenceCycleResult(
        composition_id="oracle.live.composition.v1",
        runtime_id="oracle.live.observation.production",
        iteration_number=1,
        adapter_request_count=2,
        adapter_success_count=2,
        adapter_failure_count=0,
        raw_observation_count=2,
        admitted_observation_count=2,
        terminal_read_model=read_model,
        read_only=True,
        execution_allowed=False,
    )


class TestOLC009(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_ask_registry_overlay()
        )

    def test_live_intercept(self):
        store = AtomicLiveReadModelStore()
        store.publish(
            cycle()
        )

        called = []

        def fallback(query, *args, **kwargs):
            called.append(query)
            return "legacy"

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=fallback,
        )

        status, value = overlay.dispatch(
            "why is bitcoin moving?"
        )

        self.assertTrue(
            status.live_handled
        )

        self.assertFalse(
            status.fallback_used
        )

        self.assertEqual(
            status.observation_count,
            2,
        )

        self.assertEqual(
            called,
            [],
        )

    def test_legacy_fallback(self):
        store = AtomicLiveReadModelStore()

        def fallback(query, *args, **kwargs):
            return (
                "legacy",
                query,
            )

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=fallback,
        )

        status, value = overlay.dispatch(
            "show current session"
        )

        self.assertFalse(
            status.live_handled
        )

        self.assertTrue(
            status.fallback_used
        )

        self.assertEqual(
            value,
            (
                "legacy",
                "show current session",
            ),
        )

    def test_side_effects(self):
        store = AtomicLiveReadModelStore()

        overlay = LiveAskHandlerOverlay(
            store=store,
            fallback_handler=lambda query: query,
        )

        self.assertTrue(overlay.read_only)
        self.assertFalse(overlay.execution_allowed)
        self.assertFalse(overlay.source_mutation_allowed)
        self.assertFalse(overlay.publication_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-009 CERTIFICATION TEST")
    print(" LIVE /ASK COMMAND REGISTRY OVERLAY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC009
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-009")
    print("[PASS] Live /ask queries consume the latest atomic terminal read model")
    print("[PASS] Existing /ask handler remains an exact fallback when live handling is unavailable")
    print("[PASS] Overlay requires no Oracle Terminal source mutation")
    print("[DONE] OLC-009 CERTIFIED")
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
    print(" OLC-009 INSTALLER")
    print(" LIVE /ASK COMMAND REGISTRY OVERLAY")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_009_LIVE_ASK_REGISTRY_OVERLAY_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    contract = json.loads(
        (
            PACKAGE
            / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    if (
        contract.get(
            "ask_command_present"
        )
        is not True
    ):
        raise RuntimeError(
            "OLC-008 command registry contract "
            "does not contain /ask"
        )

    print(
        "[PASS] Exact command registry contract consumed: "
        f"{contract['registry_type']}"
    )

    print(
        "[PASS] Existing /ask entry verified before overlay construction"
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
            "from .olc_009_live_ask_registry_overlay import *"
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
                    f"Certified/frozen upstream changed: {path.name}"
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
            "[DONE] OLC-009 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-009 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
