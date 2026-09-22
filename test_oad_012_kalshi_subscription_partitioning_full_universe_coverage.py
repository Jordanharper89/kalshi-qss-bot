import unittest
from qseries_v2.oracle_adapters.kalshi.oad_012_subscription_partitioning import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage())
    def test_no_loss(self):
        p=partition_subscriptions(tuple("ABCDE"),partition_size=2)
        got=tuple(x for part in p.partitions for x in part.market_tickers)
        self.assertEqual(got,("A","B","C","D","E"))
    def test_commands(self):
        self.assertEqual(len(build_partition_subscribe_commands(partition_subscriptions(("A","B"),partition_size=1))),2)
if __name__=="__main__":
    print("="*72);print(" OAD-012 CERTIFICATION TEST");print(" SUBSCRIPTION PARTITIONING + FULL-UNIVERSE COVERAGE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi deterministic full-universe subscription partitioning certified");print("[DONE] OAD-012 CERTIFIED")
