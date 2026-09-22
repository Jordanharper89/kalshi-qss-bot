import unittest
from qseries_v2.oracle_adapters.kalshi.oad_008_full_universe_discovery import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_008_kalshi_full_universe_discovery())
    def test_limit(self): self.assertEqual(build_markets_page_request()["limit"],1000)
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError): build_full_universe_snapshot(({"markets":[],"cursor":"NEXT"},))
    def test_deterministic(self):
        p=({"markets":[{"ticker":"A","event_ticker":"E","status":"active"}],"cursor":""},)
        self.assertEqual(build_full_universe_snapshot(p).snapshot_hash,build_full_universe_snapshot(p).snapshot_hash)
if __name__=="__main__":
    print("="*72);print(" OAD-008 CERTIFICATION TEST");print(" KALSHI FULL-UNIVERSE MARKET DISCOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi cursor-paginated full-universe discovery certified");print("[DONE] OAD-008 CERTIFIED")
