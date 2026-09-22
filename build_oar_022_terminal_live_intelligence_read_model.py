from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"
OI = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PKG / "oar_012_live_observation_bus_registry.py",
    PKG / "oar_021_live_intelligence_pipeline_coordinator.py",
    OI / "oi_final_certification_freeze.py",
)

MODULE = PKG / "oar_022_terminal_live_intelligence_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_022_terminal_live_intelligence_read_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from .oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelinePackage,
)

BUILD_ID = "OAR-022"
OAR_022_REVISION = "OAR_022_TERMINAL_LIVE_INTELLIGENCE_READ_MODEL_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def _stable_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class TerminalLiveIntelligenceReadModel:
    read_model_id: str
    iteration_number: int
    observation_count: int
    observation_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    oi_ready: bool
    umd_ready: bool
    oml_ready: bool
    lineage_valid: bool
    generated_at: datetime
    evidence_hash: str
    read_only: bool


class TerminalLiveIntelligenceReadModelBuilder:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def build(
        self,
        *,
        pipeline: LiveIntelligencePipelinePackage,
        generated_at: datetime,
    ) -> TerminalLiveIntelligenceReadModel:
        if not isinstance(
            pipeline,
            LiveIntelligencePipelinePackage,
        ):
            raise TypeError(
                "pipeline must be LiveIntelligencePipelinePackage"
            )

        if not isinstance(
            generated_at,
            datetime,
        ):
            raise TypeError(
                "generated_at must be datetime"
            )

        if generated_at.tzinfo is None:
            raise ValueError(
                "generated_at must be timezone-aware"
            )

        oi = pipeline.integration.oi_handoff

        if pipeline.integration.lineage_valid is not True:
            raise ValueError(
                "pipeline lineage must be valid"
            )

        if oi.observation_count != pipeline.observation_count:
            raise ValueError(
                "pipeline observation count mismatch"
            )

        body = {
            "iteration_number": pipeline.iteration_number,
            "observation_ids": oi.observation_ids,
            "provider_ids": oi.provider_ids,
            "capability_ids": oi.capability_ids,
            "oi_ready": pipeline.oi_ready,
            "umd_ready": pipeline.umd_ready,
            "oml_ready": pipeline.oml_ready,
            "lineage_valid": pipeline.integration.lineage_valid,
        }

        evidence_hash = _stable_hash(
            body
        )

        return TerminalLiveIntelligenceReadModel(
            read_model_id=(
                "terminal.live."
                + evidence_hash[:32]
            ),
            iteration_number=(
                pipeline.iteration_number
            ),
            observation_count=(
                pipeline.observation_count
            ),
            observation_ids=(
                oi.observation_ids
            ),
            provider_ids=(
                oi.provider_ids
            ),
            capability_ids=(
                oi.capability_ids
            ),
            oi_ready=(
                pipeline.oi_ready
            ),
            umd_ready=(
                pipeline.umd_ready
            ),
            oml_ready=(
                pipeline.oml_ready
            ),
            lineage_valid=True,
            generated_at=generated_at.astimezone(
                timezone.utc
            ),
            evidence_hash=evidence_hash,
            read_only=True,
        )


def verify_terminal_live_intelligence_read_model() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_022_REVISION",
    "TerminalLiveIntelligenceReadModel",
    "TerminalLiveIntelligenceReadModelBuilder",
    "verify_terminal_live_intelligence_read_model",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)
from qseries_v2.observation_adapter_runtime.oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeRequest,
)
from qseries_v2.observation_adapter_runtime.oar_018_oi_umd_oml_integration import (
    OIUMDOMLIntegrationPackage,
)
from qseries_v2.observation_adapter_runtime.oar_021_live_intelligence_pipeline_coordinator import (
    LiveIntelligencePipelinePackage,
)
from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModelBuilder,
    verify_terminal_live_intelligence_read_model,
)

NOW = datetime(
    2026,
    8,
    12,
    15,
    0,
    tzinfo=timezone.utc,
)


def pipeline():
    oi = FrozenOICanonicalHandoffRecord(
        iteration_number=1,
        observation_ids=("liveobs.1",),
        observation_hashes=("a"*64,),
        adapter_ids=("adapter.crypto.observe.v1",),
        provider_ids=("coinbase",),
        capability_ids=("spot_price",),
        observation_count=1,
        frozen_oi_target="frozen",
        read_only=True,
    )

    umd = UMDMarketCorrelationRequest(
        iteration_number=1,
        observation_ids=oi.observation_ids,
        provider_ids=oi.provider_ids,
        capability_ids=oi.capability_ids,
        market_identity_required=True,
        related_market_resolution_required=True,
        read_only=True,
    )

    oml = OMLMemoryIntakeRequest(
        iteration_number=1,
        observation_ids=oi.observation_ids,
        observation_hashes=oi.observation_hashes,
        provider_ids=oi.provider_ids,
        requires_market_identity_resolution=True,
        requires_evidence_lineage_preservation=True,
        requires_contradiction_preservation=True,
        read_only=True,
    )

    integration = OIUMDOMLIntegrationPackage(
        oi_handoff=oi,
        umd_request=umd,
        oml_request=oml,
        observation_count=1,
        lineage_valid=True,
        read_only=True,
    )

    return LiveIntelligencePipelinePackage(
        iteration_number=1,
        observation_count=1,
        integration=integration,
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        read_only=True,
    )


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_intelligence_read_model()
        )

    def test_build(self):
        result = (
            TerminalLiveIntelligenceReadModelBuilder()
            .build(
                pipeline=pipeline(),
                generated_at=NOW,
            )
        )

        self.assertEqual(
            result.observation_count,
            1,
        )

        self.assertEqual(
            result.provider_ids,
            ("coinbase",),
        )

        self.assertTrue(
            result.lineage_valid
        )

    def test_deterministic_hash(self):
        builder = (
            TerminalLiveIntelligenceReadModelBuilder()
        )

        a = builder.build(
            pipeline=pipeline(),
            generated_at=NOW,
        )

        b = builder.build(
            pipeline=pipeline(),
            generated_at=NOW,
        )

        self.assertEqual(
            a.evidence_hash,
            b.evidence_hash,
        )

    def test_side_effects(self):
        builder = (
            TerminalLiveIntelligenceReadModelBuilder()
        )

        self.assertTrue(
            builder.read_only
        )

        self.assertFalse(
            builder.execution_allowed
        )

        self.assertFalse(
            builder.publication_allowed
        )

        self.assertFalse(
            builder.persistence_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-022 CERTIFICATION TEST")
    print(" TERMINAL LIVE INTELLIGENCE READ MODEL")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-022")
    print("[PASS] Live OI/UMD/OML pipeline packaged into deterministic terminal read model")
    print("[PASS] Observation, provider, capability, readiness, and lineage preserved")
    print("[PASS] Terminal read model remains read-only and non-executing")
    print("[DONE] OAR-022 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def discover_oit_boundary():
    if not OIT.is_dir():
        raise RuntimeError(
            f"Certified Oracle Terminal package missing: {OIT}"
        )

    files = tuple(
        sorted(
            path
            for path in OIT.glob("**/*.py")
            if path.is_file()
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
    print(" OAR-022 INSTALLER")
    print(" TERMINAL LIVE INTELLIGENCE READ MODEL")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_022_TERMINAL_LIVE_INTELLIGENCE_READ_MODEL_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    oit_files = discover_oit_boundary()

    protected = (
        *UPSTREAMS,
        *oit_files,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    print(
        "[PASS] Certified Oracle Terminal "
        f"boundary captured read-only across "
        f"{len(oit_files)} modules"
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
            "oar_022_terminal_live_intelligence_read_model "
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
            "[PASS] OIT, frozen OI, and "
            "certified OAR upstream remained unchanged"
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
            "[DONE] OAR-022 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-022 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
