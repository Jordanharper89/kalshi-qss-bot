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
