from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PKG / "oar_022_terminal_live_intelligence_read_model.py",
    PKG / "oar_023_terminal_live_query_router.py",
    PKG / "oar_021_live_intelligence_pipeline_coordinator.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PKG / "oar_024_oit_live_intelligence_bridge.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_024_oit_live_intelligence_bridge.py"

OIT_BRIDGE = OIT / "oracle_universal_live_intelligence_bridge.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_023_terminal_live_query_router import (
    ROUTE_EXISTING_TERMINAL,
    TerminalLiveQueryRoute,
    TerminalLiveQueryRouter,
)

BUILD_ID = "OAR-024"
OAR_024_REVISION = "OAR_024_OIT_LIVE_INTELLIGENCE_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OITLiveIntelligenceResponse:
    handled: bool
    route: str
    query: str
    read_model_id: str | None
    observation_count: int
    evidence_hash: str | None
    fallback_to_existing_terminal: bool
    read_only: bool


class OITLiveIntelligenceBridge:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def classify(
        self,
        query: str,
    ) -> TerminalLiveQueryRoute:
        return (
            TerminalLiveQueryRouter()
            .route(
                query
            )
        )

    def respond(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> OITLiveIntelligenceResponse:
        route = self.classify(
            query
        )

        if (
            route.route
            == ROUTE_EXISTING_TERMINAL
        ):
            return OITLiveIntelligenceResponse(
                handled=False,
                route=route.route,
                query=route.raw_query,
                read_model_id=None,
                observation_count=0,
                evidence_hash=None,
                fallback_to_existing_terminal=True,
                read_only=True,
            )

        if read_model is None:
            return OITLiveIntelligenceResponse(
                handled=False,
                route=route.route,
                query=route.raw_query,
                read_model_id=None,
                observation_count=0,
                evidence_hash=None,
                fallback_to_existing_terminal=True,
                read_only=True,
            )

        if not isinstance(
            read_model,
            TerminalLiveIntelligenceReadModel,
        ):
            raise TypeError(
                "read_model must be "
                "TerminalLiveIntelligenceReadModel or None"
            )

        if read_model.read_only is not True:
            raise ValueError(
                "terminal live read model must be read-only"
            )

        return OITLiveIntelligenceResponse(
            handled=True,
            route=route.route,
            query=route.raw_query,
            read_model_id=read_model.read_model_id,
            observation_count=read_model.observation_count,
            evidence_hash=read_model.evidence_hash,
            fallback_to_existing_terminal=False,
            read_only=True,
        )


def verify_oit_live_intelligence_bridge() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_024_REVISION",
    "OITLiveIntelligenceResponse",
    "OITLiveIntelligenceBridge",
    "verify_oit_live_intelligence_bridge",
]
"""

OIT_BRIDGE_SOURCE = r"""
from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_024_oit_live_intelligence_bridge import (
    OITLiveIntelligenceBridge,
)

BUILD_ID = "OAR-024-OIT"
REVISION = "OAR_024_OIT_READ_ONLY_LIVE_INTELLIGENCE_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def build_oracle_universal_live_intelligence_bridge():
    return OITLiveIntelligenceBridge()


def verify_oracle_universal_live_intelligence_bridge() -> bool:
    bridge = (
        build_oracle_universal_live_intelligence_bridge()
    )

    assert bridge.read_only is True
    assert bridge.execution_allowed is False
    assert bridge.publication_allowed is False
    assert bridge.persistence_allowed is False

    return True


__all__ = [
    "BUILD_ID",
    "REVISION",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "PUBLICATION_ALLOWED",
    "PERSISTENCE_ALLOWED",
    "build_oracle_universal_live_intelligence_bridge",
    "verify_oracle_universal_live_intelligence_bridge",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_024_oit_live_intelligence_bridge import (
    OITLiveIntelligenceBridge,
    verify_oit_live_intelligence_bridge,
)
from qseries_v2.oracle_terminal.oracle_universal_live_intelligence_bridge import (
    verify_oracle_universal_live_intelligence_bridge,
)

NOW = datetime(
    2026,
    8,
    12,
    15,
    30,
    tzinfo=timezone.utc,
)


def read_model():
    return TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.1",
        iteration_number=1,
        observation_count=1,
        observation_ids=("liveobs.1",),
        provider_ids=("coinbase",),
        capability_ids=("spot_price",),
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
            verify_oit_live_intelligence_bridge()
        )

        self.assertTrue(
            verify_oracle_universal_live_intelligence_bridge()
        )

    def test_live_fact_handled(self):
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query=(
                    "what is the current price "
                    "of bitcoin?"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            response.handled
        )

        self.assertFalse(
            response.fallback_to_existing_terminal
        )

        self.assertEqual(
            response.observation_count,
            1,
        )

    def test_live_explanation_handled(self):
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query=(
                    "explain why the edge for up "
                    "on Astros strikeouts just went up"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            response.handled
        )

    def test_non_live_falls_back(self):
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query="show current session",
                read_model=read_model(),
            )
        )

        self.assertFalse(
            response.handled
        )

        self.assertTrue(
            response.fallback_to_existing_terminal
        )

    def test_missing_read_model_falls_back(self):
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query="why is bitcoin moving?",
                read_model=None,
            )
        )

        self.assertFalse(
            response.handled
        )

        self.assertTrue(
            response.fallback_to_existing_terminal
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-024 CERTIFICATION TEST")
    print(" OIT-050 READ-ONLY LIVE INTELLIGENCE BRIDGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-024")
    print("[PASS] OIT-facing universal live-intelligence bridge installed")
    print("[PASS] Live fact, explanation, and directional queries can be intercepted read-only")
    print("[PASS] Existing terminal fallback remains available when live intelligence is unavailable")
    print("[PASS] Execution, publication, persistence, and Q Series action remain disabled")
    print("[DONE] OAR-024 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def discover_oit_files():
    if not OIT.is_dir():
        raise RuntimeError(
            f"Certified Oracle Terminal package missing: "
            f"{OIT}"
        )

    files = tuple(
        sorted(
            path
            for path in OIT.glob("**/*.py")
            if path.is_file()
            and path != OIT_BRIDGE
        )
    )

    if not files:
        raise RuntimeError(
            "Certified Oracle Terminal modules missing"
        )

    return files


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
    print(" OAR-024 INSTALLER")
    print(" OIT-050 READ-ONLY LIVE INTELLIGENCE BRIDGE")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_024_OIT_LIVE_INTELLIGENCE_BRIDGE_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    oit_files = discover_oit_files()

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
        OIT_BRIDGE,
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
            OIT_BRIDGE,
            OIT_BRIDGE_SOURCE,
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
            "oar_024_oit_live_intelligence_bridge "
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
            "[PASS] Existing certified OIT modules "
            "remained unchanged"
        )
        print(
            "[PASS] Frozen OI and certified OAR "
            "upstream remained unchanged"
        )
        print(
            "[PASS] OIT received one additive "
            "read-only universal live-intelligence bridge"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + OIT_BRIDGE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[DONE] OAR-024 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-024 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
