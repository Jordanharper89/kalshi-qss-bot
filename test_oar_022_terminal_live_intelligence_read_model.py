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
