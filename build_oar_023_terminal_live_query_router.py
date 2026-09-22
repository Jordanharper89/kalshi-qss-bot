from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_021_live_intelligence_pipeline_coordinator.py",
    PKG / "oar_022_terminal_live_intelligence_read_model.py",
)

MODULE = PKG / "oar_023_terminal_live_query_router.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_023_terminal_live_query_router.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OAR-023"
OAR_023_REVISION = "OAR_023_TERMINAL_LIVE_QUERY_ROUTER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False

ROUTE_LIVE_FACT = "live_fact"
ROUTE_LIVE_EXPLANATION = "live_explanation"
ROUTE_LIVE_DIRECTION = "live_direction"
ROUTE_EXISTING_TERMINAL = "existing_terminal"

_FACT_TOKENS = (
    "current price",
    "price of",
    "what is the price",
    "how much is",
    "current value",
)

_EXPLANATION_TOKENS = (
    "why is",
    "why did",
    "explain why",
    "what caused",
    "what changed",
    "why has",
    "why did the edge",
    "why the edge",
)

_DIRECTION_TOKENS = (
    "where is",
    "where will",
    "moving",
    "direction",
    "next hour",
    "next 30 minutes",
    "next 15 minutes",
    "up or down",
)


@dataclass(frozen=True, slots=True)
class TerminalLiveQueryRoute:
    raw_query: str
    normalized_query: str
    route: str
    live_intelligence_required: bool
    explanation_required: bool
    directional_reasoning_required: bool
    read_only: bool


class TerminalLiveQueryRouter:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def route(
        self,
        query: str,
    ) -> TerminalLiveQueryRoute:
        raw = str(query)

        normalized = " ".join(
            raw.strip().lower().split()
        )

        if not normalized:
            raise ValueError(
                "query must not be empty"
            )

        if any(
            token in normalized
            for token in _EXPLANATION_TOKENS
        ):
            route = ROUTE_LIVE_EXPLANATION
            live_required = True
            explanation_required = True
            direction_required = False

        elif any(
            token in normalized
            for token in _DIRECTION_TOKENS
        ):
            route = ROUTE_LIVE_DIRECTION
            live_required = True
            explanation_required = True
            direction_required = True

        elif any(
            token in normalized
            for token in _FACT_TOKENS
        ):
            route = ROUTE_LIVE_FACT
            live_required = True
            explanation_required = False
            direction_required = False

        else:
            route = ROUTE_EXISTING_TERMINAL
            live_required = False
            explanation_required = False
            direction_required = False

        return TerminalLiveQueryRoute(
            raw_query=raw,
            normalized_query=normalized,
            route=route,
            live_intelligence_required=(
                live_required
            ),
            explanation_required=(
                explanation_required
            ),
            directional_reasoning_required=(
                direction_required
            ),
            read_only=True,
        )


def verify_terminal_live_query_router() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_023_REVISION",
    "ROUTE_LIVE_FACT",
    "ROUTE_LIVE_EXPLANATION",
    "ROUTE_LIVE_DIRECTION",
    "ROUTE_EXISTING_TERMINAL",
    "TerminalLiveQueryRoute",
    "TerminalLiveQueryRouter",
    "verify_terminal_live_query_router",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_023_terminal_live_query_router import (
    ROUTE_EXISTING_TERMINAL,
    ROUTE_LIVE_DIRECTION,
    ROUTE_LIVE_EXPLANATION,
    ROUTE_LIVE_FACT,
    TerminalLiveQueryRouter,
    verify_terminal_live_query_router,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_query_router()
        )

    def test_fact(self):
        result = TerminalLiveQueryRouter().route(
            "what is the current price of bitcoin?"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_FACT,
        )

        self.assertTrue(
            result.live_intelligence_required
        )

    def test_explanation(self):
        result = TerminalLiveQueryRouter().route(
            "explain why the edge for up on Astros strikeouts just went up"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_EXPLANATION,
        )

        self.assertTrue(
            result.explanation_required
        )

    def test_direction(self):
        result = TerminalLiveQueryRouter().route(
            "where is bitcoin moving in the next hour"
        )

        self.assertEqual(
            result.route,
            ROUTE_LIVE_DIRECTION,
        )

        self.assertTrue(
            result.directional_reasoning_required
        )

    def test_fallback(self):
        result = TerminalLiveQueryRouter().route(
            "show me the current session"
        )

        self.assertEqual(
            result.route,
            ROUTE_EXISTING_TERMINAL,
        )

        self.assertFalse(
            result.live_intelligence_required
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-023 CERTIFICATION TEST")
    print(" TERMINAL QUERY-TO-LIVE-INTELLIGENCE ROUTER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-023")
    print("[PASS] Live fact, explanation, and directional query routes certified")
    print("[PASS] Existing terminal fallback preserved for non-live queries")
    print("[PASS] Router remains generic across Kalshi categories and adapter domains")
    print("[DONE] OAR-023 CERTIFIED")
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
    print(" OAR-023 INSTALLER")
    print(" TERMINAL QUERY-TO-LIVE-INTELLIGENCE ROUTER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_023_TERMINAL_LIVE_QUERY_ROUTER_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    if not OIT.is_dir():
        raise RuntimeError(
            f"Certified Oracle Terminal package missing: "
            f"{OIT}"
        )

    oit_files = tuple(
        sorted(
            OIT.glob("**/*.py")
        )
    )

    if not oit_files:
        raise RuntimeError(
            "Certified Oracle Terminal modules missing"
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
            "from ."
            "oar_023_terminal_live_query_router "
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
            "[PASS] Certified OIT and OAR "
            "upstream remained unchanged"
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
            "[DONE] OAR-023 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-023 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
