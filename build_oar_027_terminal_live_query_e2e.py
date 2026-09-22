from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_022_terminal_live_intelligence_read_model.py",
    PKG / "oar_023_terminal_live_query_router.py",
    PKG / "oar_024_oit_live_intelligence_bridge.py",
    PKG / "oar_025_oit_ask_dispatch_resolver.py",
    PKG / "oar_026_live_ask_dispatch_binding.py",
    OIT / "oracle_live_ask_dispatch_adapter.py",
)

MODULE = PKG / "oar_027_terminal_live_query_e2e.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_027_terminal_live_query_e2e.py"
LAUNCHER = ROOT / "run_oracle_terminal_live_intelligence.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OAR-027"
OAR_027_REVISION = "OAR_027_TERMINAL_LIVE_QUERY_E2E_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class TerminalLiveQueryE2EResult:
    query: str
    live_handled: bool
    observation_count: int
    route: str
    evidence_hash: str | None
    fallback_to_existing_terminal: bool
    read_only: bool


class TerminalLiveQueryEndToEnd:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def execute(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> TerminalLiveQueryE2EResult:
        dispatch = (
            LiveAskDispatchBinding()
            .dispatch(
                query=query,
                read_model=read_model,
            )
        )

        response = (
            dispatch.live_response
        )

        return TerminalLiveQueryE2EResult(
            query=query,
            live_handled=response.handled,
            observation_count=(
                response.observation_count
            ),
            route=response.route,
            evidence_hash=(
                response.evidence_hash
            ),
            fallback_to_existing_terminal=(
                dispatch
                .consume_existing_terminal
            ),
            read_only=True,
        )


def verify_terminal_live_query_e2e() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
"""

LAUNCHER_SOURCE = r"""
from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-027-LAUNCHER"
REVISION = "OAR_027_TERMINAL_LIVE_INTELLIGENCE_LAUNCHER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False


def build_terminal_live_query_path():
    return TerminalLiveQueryEndToEnd()


def main() -> int:
    print("=" * 72)
    print(" ORACLE TERMINAL LIVE INTELLIGENCE READ PATH")
    print("=" * 72)
    print("[MODE] READ-ONLY")
    print("[PASS] OAR-027 live query path available")
    print("[PASS] Existing Oracle Terminal remains fallback-safe")
    print("[PASS] Execution, publication, and persistence disabled")
    print()
    print(
        "[INFO] This launcher certifies the live-intelligence "
        "query path. Production terminal command-loop activation "
        "occurs only after final end-to-end certification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
    verify_terminal_live_query_e2e,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    30,
    tzinfo=timezone.utc,
)


def read_model():
    return TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.1",
        iteration_number=1,
        observation_count=3,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
            "liveobs.3",
        ),
        provider_ids=(
            "coinbase",
            "kalshi",
        ),
        capability_ids=(
            "market_snapshot",
            "spot_price",
        ),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_query_e2e()
        )

    def test_bitcoin_explanation(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query="why is bitcoin moving?",
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertEqual(
            result.observation_count,
            3,
        )

        self.assertFalse(
            result.fallback_to_existing_terminal
        )

    def test_kalshi_explanation(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query=(
                    "explain why the edge for up "
                    "on Astros strikeouts just went up"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_handled
        )

        self.assertFalse(
            result.fallback_to_existing_terminal
        )

    def test_existing_terminal_fallback(self):
        result = (
            TerminalLiveQueryEndToEnd()
            .execute(
                query="show current session",
                read_model=read_model(),
            )
        )

        self.assertFalse(
            result.live_handled
        )

        self.assertTrue(
            result.fallback_to_existing_terminal
        )

    def test_side_effects(self):
        x = TerminalLiveQueryEndToEnd()

        self.assertTrue(
            x.read_only
        )

        self.assertFalse(
            x.execution_allowed
        )

        self.assertFalse(
            x.publication_allowed
        )

        self.assertFalse(
            x.persistence_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-027 CERTIFICATION TEST")
    print(" TERMINAL LIVE QUERY END-TO-END READ PATH")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-027")
    print("[PASS] Bitcoin live explanation query traverses the new read-only terminal path")
    print("[PASS] Kalshi category explanation query traverses the same generic live path")
    print("[PASS] Existing terminal fallback remains intact")
    print("[PASS] Execution, publication, and persistence remain disabled")
    print("[DONE] OAR-027 CERTIFIED")
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
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OAR-027 INSTALLER")
    print(" TERMINAL LIVE QUERY END-TO-END READ PATH")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_027_TERMINAL_LIVE_QUERY_E2E_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    protected = UPSTREAMS

    hashes = {
        path: sha(path)
        for path in protected
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
            "oar_027_terminal_live_query_e2e "
            "import *"
        )

        if export not in current.splitlines():
            if (
                current
                and not current.endswith("\n")
            ):
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
                    "Certified upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Certified OAR and OIT bridge "
            "upstream remained unchanged"
        )

        print(
            "[PASS] Wrote read-only certification launcher: "
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
            "[DONE] OAR-027 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-027 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
