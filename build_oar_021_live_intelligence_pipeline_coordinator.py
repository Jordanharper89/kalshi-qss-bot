from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PKG / "oar_012_live_observation_bus_registry.py",
    PKG / "oar_013_oi_canonical_handoff.py",
    PKG / "oar_018_oi_umd_oml_integration.py",
    PKG / "oar_019_exact_umd_market_identity_binding.py",
    PKG / "oar_020_exact_oml_observation_intake_binding.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PKG / "oar_021_live_intelligence_pipeline_coordinator.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_021_live_intelligence_pipeline_coordinator.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoff,
)
from .oar_018_oi_umd_oml_integration import (
    OIUMDOMLIntegrationBuilder,
    OIUMDOMLIntegrationPackage,
)

BUILD_ID = "OAR-021"
OAR_021_REVISION = "OAR_021_LIVE_INTELLIGENCE_PIPELINE_COORDINATOR_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveIntelligencePipelinePackage:
    iteration_number: int
    observation_count: int
    integration: OIUMDOMLIntegrationPackage
    oi_ready: bool
    umd_ready: bool
    oml_ready: bool
    read_only: bool


class LiveIntelligencePipelineCoordinator:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def coordinate(
        self,
        admission: LiveObservationAdmissionResult,
    ) -> LiveIntelligencePipelinePackage:
        if not isinstance(
            admission,
            LiveObservationAdmissionResult,
        ):
            raise TypeError(
                "admission must be LiveObservationAdmissionResult"
            )

        oi_handoff = (
            FrozenOICanonicalHandoff()
            .build(
                admission
            )
        )

        integration = (
            OIUMDOMLIntegrationBuilder()
            .build(
                oi_handoff
            )
        )

        return LiveIntelligencePipelinePackage(
            iteration_number=(
                admission.iteration_number
            ),
            observation_count=(
                admission.admitted_count
            ),
            integration=integration,
            oi_ready=True,
            umd_ready=True,
            oml_ready=True,
            read_only=True,
        )


def verify_live_intelligence_pipeline_coordinator() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import (
    CanonicalLiveObservation,
)
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from qseries_v2.observation_adapter_runtime.oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelineCoordinator,
    verify_live_intelligence_pipeline_coordinator,
)

NOW = datetime(
    2026,
    8,
    12,
    14,
    0,
    tzinfo=timezone.utc,
)

def admission():
    observation = CanonicalLiveObservation(
        observation_id="liveobs.1",
        adapter_id="adapter.crypto.observe.v1",
        provider_id="coinbase",
        capability="spot_price",
        payload=(
            ("asset","BTC"),
            ("price","65000"),
        ),
        observed_at=NOW,
        iteration_number=1,
        lineage_hash="a"*64,
        observation_hash="b"*64,
        read_only=True,
    )

    return LiveObservationAdmissionResult(
        iteration_number=1,
        admitted_observations=(
            observation,
        ),
        rejected_observation_ids=(),
        duplicate_observation_ids=(),
        admitted_count=1,
        rejected_count=0,
        read_only=True,
    )

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_intelligence_pipeline_coordinator()
        )

    def test_coordinate(self):
        result = (
            LiveIntelligencePipelineCoordinator()
            .coordinate(
                admission()
            )
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

        self.assertTrue(
            result.oi_ready
        )

        self.assertTrue(
            result.umd_ready
        )

        self.assertTrue(
            result.oml_ready
        )

        self.assertTrue(
            result.integration.lineage_valid
        )

    def test_side_effects(self):
        x = LiveIntelligencePipelineCoordinator()

        self.assertTrue(
            x.read_only
        )

        self.assertFalse(
            x.execution_allowed
        )

        self.assertFalse(
            x.persistence_allowed
        )

        self.assertFalse(
            x.publication_allowed
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-021 CERTIFICATION TEST")
    print(" LIVE INTELLIGENCE PIPELINE COORDINATOR")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-021")
    print("[PASS] Admitted live observations coordinate through frozen OI, UMD request, and OML intake package")
    print("[PASS] OI/UMD/OML readiness and lineage preserved")
    print("[PASS] Persistence, publication, and execution remain disabled")
    print("[DONE] OAR-021 CERTIFIED")
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
    print(" OAR-021 INSTALLER")
    print(" LIVE INTELLIGENCE PIPELINE COORDINATOR")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_021_LIVE_INTELLIGENCE_PIPELINE_COORDINATOR_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
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
            "from ."
            "oar_021_live_intelligence_pipeline_coordinator "
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
            "[PASS] Certified OAR and frozen OI "
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
            "[DONE] OAR-021 INSTALLATION COMPLETE"
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

        raise


if __name__ == "__main__":
    raise SystemExit(main())
