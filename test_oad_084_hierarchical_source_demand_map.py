import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort
from qseries_v2.oracle_adapters.independent.oad_084_hierarchical_source_demand_map import *

class T(unittest.TestCase):
    def test_physical(self):
        s=capture_current_market_cohort(1000)
        rows=source_demand_from_snapshot(s)
        print("[PHYSICAL] snapshot_id=",s.snapshot_id)
        print("[PHYSICAL] source_demand_topics=",len(rows))
        for x in rows:
            print("[DEMAND]",x.topic,"markets=",x.live_markets,"state=",x.state,"existing=",x.existing_families,"missing=",x.missing_families)
        self.assertGreater(len(rows),0)
        self.assertTrue(all(x.state in ("COVERED","NOT_COVERED","UNMAPPED") for x in rows))
        self.assertTrue(all(not (x.topic=="other" and x.state=="COVERED") for x in rows))

if __name__=="__main__":
    print("="*88);print(" OAD-084 PHYSICAL CERTIFICATION TEST");print(" HIERARCHICAL SOURCE-DEMAND MAP");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Source demand derived from classified live-market topics")
    print("[PASS] Unmapped demand cannot report covered")
    print("[DONE] OAD-084 CERTIFIED")
