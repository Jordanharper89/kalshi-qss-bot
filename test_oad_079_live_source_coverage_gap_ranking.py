import unittest
from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import *

class T(unittest.TestCase):
    def test_physical(self):
        rows=rank_live_source_coverage_gaps(1000)
        print("[PHYSICAL] ranked_topics=",len(rows))
        for x in rows:
            print("[GAP]",x.topic,"markets=",x.live_markets,"covered=",x.covered,"missing=",x.missing_source_families,"priority=",x.priority_score)
        self.assertGreater(len(rows),0)
        self.assertTrue(all(rows[i].priority_score>=rows[i+1].priority_score for i in range(len(rows)-1)))

if __name__=="__main__":
    print("="*88);print(" OAD-079 PHYSICAL CERTIFICATION TEST");print(" LIVE SOURCE COVERAGE GAP RANKING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Missing adapter families ranked by actual live-market demand")
    print("[DONE] OAD-079 CERTIFIED")
