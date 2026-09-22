
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_oad_048_physical_multi_partition_persistence_runtime()
        )

    def test_global_fast_lane_has_no_market_filter(self):
        cmd=build_kalshi_subscription_command(
            1,
            ("ticker","trade"),
            None,
        )
        self.assertNotIn("market_tickers",cmd["params"])

    def test_backward_compatibility_symbol(self):
        self.assertEqual(MultiPartitionRuntimeSummary.__name__,"MultiPartitionRuntimeSummary")
        self.assertTrue(callable(run_physical_multi_partition_persistence))

    def test_orderbook_requires_explicit_markets(self):
        cmd=build_kalshi_subscription_command(
            2,
            ("orderbook_delta",),
            ("A","B"),
        )
        self.assertEqual(
            cmd["params"]["market_tickers"],
            ["A","B"],
        )

if __name__=="__main__":
    print("="*72)
    print(" OAD-048 TRUE LIVE-FIRST CORRECTION V4 CERTIFICATION TEST")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Global all-market fast lane is independent of REST enumeration")
    print("[PASS] Orderbook lane remains explicitly partitioned")
    print("[DONE] OAD-048 CORRECTION V4 CERTIFIED")
