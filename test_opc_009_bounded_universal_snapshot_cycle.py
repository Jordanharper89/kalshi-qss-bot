import unittest

from qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (
    build_universal_market_snapshot,
)
from qseries_v2.oracle_pre_settlement_coverage.opc_009_bounded_universal_snapshot_cycle import (
    verify_opc_009_bounded_universal_snapshot_cycle,
)

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_opc_009_bounded_universal_snapshot_cycle()
        )

    def test_same_state_different_epochs_are_distinct(self):
        market={"ticker":"KXTEST","yes_bid":50}
        first=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.000001Z",
            batch_id="batch",
        )
        second=build_universal_market_snapshot(
            market,
            acquired_at="2026-08-16T20:00:00.000002Z",
            batch_id="batch",
        )
        self.assertNotEqual(first.observation_id,second.observation_id)

if __name__=="__main__":
    print("="*72)
    print(" OPC-009 ALIGNMENT V2 CERTIFICATION TEST")
    print(" FRESH OBSERVATION EPOCH SNAPSHOT CYCLE")
    print("="*72)

    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OPC-009 aligned to OPC-006 time-aware observation identity")
    print("[PASS] Each snapshot receives a distinct observation epoch")
    print("[PASS] Frozen OLA persistence boundary remains untouched")
    print("[DONE] OPC-009 ALIGNMENT V2 CERTIFIED")
