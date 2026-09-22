import unittest
from qseries_v2.oracle_adapters.kalshi.oad_008_full_universe_discovery import build_full_universe_snapshot
from qseries_v2.oracle_adapters.kalshi.oad_009_universe_reconciliation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_009_kalshi_universe_reconciliation_lifecycle())
    def test_paused_surveillance(self):
        s=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"inactive"}],"cursor":""},))
        r=reconcile_universe(s,s); self.assertEqual(r.broad_surveillance,("A",)); self.assertEqual(r.active_fast_lane,())
    def test_terminal_excluded(self):
        s=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"finalized"}],"cursor":""},))
        r=reconcile_universe(s,s); self.assertEqual(r.broad_surveillance,()); self.assertEqual(r.terminal_markets,("A",))
if __name__=="__main__":
    print("="*72);print(" OAD-009 CERTIFICATION TEST");print(" KALSHI UNIVERSE RECONCILIATION + LIFECYCLE CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi two-speed universe lifecycle classification certified");print("[DONE] OAD-009 CERTIFIED")
