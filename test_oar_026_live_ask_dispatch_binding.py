from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
    verify_live_ask_dispatch_binding,
)
from qseries_v2.oracle_terminal.oracle_live_ask_dispatch_adapter import (
    verify_oracle_live_ask_dispatch_adapter,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    0,
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
            verify_live_ask_dispatch_binding()
        )

        self.assertTrue(
            verify_oracle_live_ask_dispatch_adapter()
        )

    def test_live_query_intercept(self):
        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query=(
                    "why is bitcoin moving?"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_response.handled
        )

        self.assertFalse(
            result.consume_existing_terminal
        )

    def test_fallback(self):
        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query="show current session",
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.consume_existing_terminal
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-026 CERTIFICATION TEST")
    print(" LIVE /ASK DISPATCH BINDING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-026")
    print("[PASS] Live /ask queries can be intercepted before legacy terminal fallback")
    print("[PASS] Non-live queries preserve the existing OIT dispatch path")
    print("[PASS] Binding remains additive, read-only, and non-executing")
    print("[DONE] OAR-026 CERTIFIED")
