import unittest
from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import *
class T(unittest.TestCase):
    def test_physical(self):
        markets,index=fetch_current_open_kalshi_market_index(limit=1000)
        print("[PHYSICAL] current_open_markets=",len(markets));print("[PHYSICAL] indexed_markets=",len(index))
        self.assertGreater(len(markets),0);self.assertLessEqual(len(markets),1000)
if __name__=="__main__":
    print("="*88);print(" OAD-069 PHYSICAL CERTIFICATION TEST");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Real current open Kalshi market page indexed read-only");print("[DONE] OAD-069 CERTIFIED")
