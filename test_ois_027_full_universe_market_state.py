import unittest
from qseries_v2.oracle_intelligence_state.ois_027_full_universe_state import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_027_full_universe_market_state())

    def test_deterministic_order(self):
        a=build_market_surveillance_state("kalshi","A","x",True,1,1,.5,.5)
        b=build_market_surveillance_state("kalshi","B","x",True,1,1,.5,.5)
        self.assertEqual(build_full_universe_state((b,a))[0].market_id,"A")

    def test_duplicate(self):
        a=build_market_surveillance_state("kalshi","A","x",True,1,1,.5,.5)
        with self.assertRaises(ValueError):
            build_full_universe_state((a,a))

if __name__=="__main__":
    print("="*72);print(" OIS-027 CERTIFICATION TEST");print(" FULL-UNIVERSE MARKET STATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic full-universe market surveillance state certified")
    print("[DONE] OIS-027 CERTIFIED")
