import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import *

class T(unittest.TestCase):
    def test_physical(self):
        s=capture_current_market_cohort(1000)
        a=snapshot_markets(s)
        b=snapshot_markets(s)
        print("[PHYSICAL] snapshot_id=",s.snapshot_id)
        print("[PHYSICAL] captured_at=",s.captured_at)
        print("[PHYSICAL] current_open_markets=",s.market_count)
        self.assertGreater(s.market_count,0)
        self.assertEqual(len(a),s.market_count)
        self.assertEqual(a,b)

if __name__=="__main__":
    print("="*88);print(" OAD-082 PHYSICAL CERTIFICATION TEST");print(" SINGLE LIVE MARKET COHORT SNAPSHOT");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] One immutable live cohort snapshot reused deterministically downstream")
    print("[DONE] OAD-082 CERTIFIED")
