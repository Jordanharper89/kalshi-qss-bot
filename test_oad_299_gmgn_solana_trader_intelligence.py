import unittest
from qseries_v2.oracle_adapters.independent.oad_299_gmgn_solana_trader_intelligence import *
class T(unittest.TestCase):
    def test_physical(self):
        h,t=acquire_current_gmgn_holder_and_trader_pair()
        print("[PHYSICAL] token=",t.token_address); print("[PHYSICAL] holder_raw_type=",type(h.raw).__name__); print("[PHYSICAL] trader_raw_type=",type(t.raw).__name__)
        self.assertEqual(h.token_address,t.token_address); self.assertIsNotNone(h.raw); self.assertIsNotNone(t.raw)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-299 same-token GMGN holder/trader acquisition physically certified")
