import unittest

from qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (
    build_universal_market_snapshot,
    verify_opc_006_universal_market_snapshot_canonicalizer,
)

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_opc_006_universal_market_snapshot_canonicalizer()
        )

    def test_same_state_new_epoch_new_identity(self):
        market={"ticker":"KX","yes_bid":1}
        first=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.000001Z",
            batch_id="b1",
        )
        second=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.000002Z",
            batch_id="b2",
        )
        self.assertNotEqual(first.observation_id,second.observation_id)
        self.assertNotEqual(first.content_hash,second.content_hash)
        self.assertEqual(
            dict(first.payload)["opc_source_state_hash"],
            dict(second.payload)["opc_source_state_hash"],
        )

    def test_exact_epoch_is_deterministic(self):
        market={"ticker":"KX","yes_bid":1}
        first=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.123456Z",
            batch_id="same",
        )
        second=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.123456Z",
            batch_id="same",
        )
        self.assertEqual(first.observation_id,second.observation_id)
        self.assertEqual(first.content_hash,second.content_hash)

if __name__=="__main__":
    print("="*72)
    print(" OPC-006 CORRECTION V3 CERTIFICATION TEST")
    print(" TIME-AWARE UNIVERSAL MARKET SNAPSHOT IDENTITY")
    print("="*72)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Stable market-state hash preserved")
    print("[PASS] New observation epoch produces new observation identity")
    print("[PASS] Exact same state + exact same epoch remains deterministic")
    print("[PASS] duplicate_observation_identity defect corrected at OPC boundary")
    print("[DONE] OPC-006 CORRECTION V3 CERTIFIED")
