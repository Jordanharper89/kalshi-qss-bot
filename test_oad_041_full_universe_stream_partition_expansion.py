import unittest
from qseries_v2.oracle_adapters.kalshi.oad_041_full_universe_partitioning import *
class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_041_full_universe_stream_partition_expansion())
    def test_no_loss(self):
        p=build_full_universe_partition_plan(tuple("ABCDEFG"),3)
        self.assertEqual(sum(len(x.market_tickers) for x in p.partitions),7)
if __name__=="__main__":
    print("="*72);print(" OAD-041 CERTIFICATION TEST");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Full-universe stream partition expansion certified")
    print("[DONE] OAD-041 CERTIFIED")
