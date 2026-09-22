import unittest
from qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import *

class T(unittest.TestCase):
    def test_physical(self):
        r=build_live_topic_inventory(1000)
        print("[PHYSICAL] current_open_markets=",r.market_count)
        print("[PHYSICAL] classified_markets=",r.classified_count)
        print("[PHYSICAL] unclassified_markets=",r.unclassified_count)
        print("[PHYSICAL] topic_counts=",r.topic_counts)
        self.assertGreater(r.market_count,0)
        self.assertEqual(r.classified_count+r.unclassified_count,r.market_count)

if __name__=="__main__":
    print("="*88);print(" OAD-077 PHYSICAL CERTIFICATION TEST");print(" LIVE MARKET TOPIC INVENTORY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Real current Kalshi cohort classified without forcing unknown markets")
    print("[DONE] OAD-077 CERTIFIED")
