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
