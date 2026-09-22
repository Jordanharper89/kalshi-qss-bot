from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OAD = ROOT / "qseries_v2" / "observation_adapters"
OI = ROOT / "qseries_v2" / "observation_intelligence"
UMD = ROOT / "qseries_v2" / "universal_market_discovery"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_006_production_launch_boundary.py",
    PKG / "oar_009_runtime_health_registry.py",
    PKG / "oar_012_live_observation_bus_registry.py",
    PKG / "oar_018_oi_umd_oml_integration.py",
    PKG / "oar_021_live_intelligence_pipeline_coordinator.py",
    PKG / "oar_022_terminal_live_intelligence_read_model.py",
    PKG / "oar_024_oit_live_intelligence_bridge.py",
    PKG / "oar_026_live_ask_dispatch_binding.py",
    PKG / "oar_027_terminal_live_query_e2e.py",
    OAD / "oad_006_default_adapter_bundle.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PKG / "oar_028_full_live_intelligence_certification.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_028_full_live_intelligence_certification.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-028"
OAR_028_REVISION = "OAR_028_FULL_LIVE_INTELLIGENCE_CERTIFICATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class FullLiveIntelligenceCertificationResult:
    bitcoin_query_passed: bool
    kalshi_query_passed: bool
    fallback_query_passed: bool
    observation_count: int
    evidence_hash: str
    read_only: bool
    execution_allowed: bool


class FullLiveIntelligenceCertification:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def certify(
        self,
        *,
        read_model: TerminalLiveIntelligenceReadModel,
    ) -> FullLiveIntelligenceCertificationResult:
        if not isinstance(
            read_model,
            TerminalLiveIntelligenceReadModel,
        ):
            raise TypeError(
                "read_model must be TerminalLiveIntelligenceReadModel"
            )

        if read_model.read_only is not True:
            raise ValueError(
                "read_model must be read-only"
            )

        if read_model.lineage_valid is not True:
            raise ValueError(
                "read_model lineage must be valid"
            )

        engine = TerminalLiveQueryEndToEnd()

        bitcoin = engine.execute(
            query="why is bitcoin moving?",
            read_model=read_model,
        )

        kalshi = engine.execute(
            query=(
                "explain why the edge for up "
                "on Astros strikeouts just went up"
            ),
            read_model=read_model,
        )

        fallback = engine.execute(
            query="show current session",
            read_model=read_model,
        )

        bitcoin_passed = (
            bitcoin.live_handled
            and not bitcoin.fallback_to_existing_terminal
        )

        kalshi_passed = (
            kalshi.live_handled
            and not kalshi.fallback_to_existing_terminal
        )

        fallback_passed = (
            not fallback.live_handled
            and fallback.fallback_to_existing_terminal
        )

        if not (
            bitcoin_passed
            and kalshi_passed
            and fallback_passed
        ):
            raise RuntimeError(
                "full live-intelligence certification failed"
            )

        return FullLiveIntelligenceCertificationResult(
            bitcoin_query_passed=True,
            kalshi_query_passed=True,
            fallback_query_passed=True,
            observation_count=read_model.observation_count,
            evidence_hash=read_model.evidence_hash,
            read_only=True,
            execution_allowed=False,
        )


def verify_full_live_intelligence_certification() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_028_full_live_intelligence_certification import (
    FullLiveIntelligenceCertification,
    verify_full_live_intelligence_certification,
)

NOW = datetime(
    2026,
    8,
    12,
    17,
    0,
    tzinfo=timezone.utc,
)


def read_model():
    return TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.certification",
        iteration_number=1,
        observation_count=4,
        observation_ids=(
            "liveobs.1",
            "liveobs.2",
            "liveobs.3",
            "liveobs.4",
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
            verify_full_live_intelligence_certification()
        )

    def test_full_certification(self):
        result = (
            FullLiveIntelligenceCertification()
            .certify(
                read_model=read_model()
            )
        )

        self.assertTrue(
            result.bitcoin_query_passed
        )
        self.assertTrue(
            result.kalshi_query_passed
        )
        self.assertTrue(
            result.fallback_query_passed
        )
        self.assertEqual(
            result.observation_count,
            4,
        )

    def test_side_effects(self):
        x = FullLiveIntelligenceCertification()
        self.assertTrue(x.read_only)
        self.assertFalse(x.execution_allowed)
        self.assertFalse(x.publication_allowed)
        self.assertFalse(x.persistence_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-028 CERTIFICATION TEST")
    print(" FULL RUNTIME-TO-TERMINAL LIVE INTELLIGENCE CERTIFICATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-028")
    print("[PASS] Bitcoin live explanation path certified")
    print("[PASS] Kalshi category live explanation path certified")
    print("[PASS] Existing terminal fallback path certified")
    print("[PASS] Runtime-to-terminal intelligence path remains read-only")
    print("[DONE] OAR-028 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_files(root: Path, pattern: str = "**/*.py"):
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            p for p in root.glob(pattern)
            if p.is_file()
        )
    )


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAR-028 INSTALLER")
    print(" FULL RUNTIME-TO-TERMINAL LIVE INTELLIGENCE CERTIFICATION")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_028_FULL_LIVE_INTELLIGENCE_CERTIFICATION_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    umd_files = discover_files(UMD)
    oit_files = discover_files(OIT)

    if not umd_files:
        raise RuntimeError(
            "Certified UMD boundary missing"
        )

    if not oit_files:
        raise RuntimeError(
            "Certified OIT boundary missing"
        )

    protected = (
        *UPSTREAMS,
        *umd_files,
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
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from ."
            "oar_028_full_live_intelligence_certification "
            "import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {path.name}"
                )

        print(
            "[PASS] Certified OAD, OI, UMD, OIT, "
            "and OAR boundaries remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[DONE] OAR-028 INSTALLATION COMPLETE"
        )
        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(original)
        print(
            "[ROLLBACK] OAR-028 installation failed; "
            "affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
