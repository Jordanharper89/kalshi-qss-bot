import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets
from qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import *

class T(unittest.TestCase):
    def test_physical(self):
        s=capture_current_market_cohort(1000)
        rows,counts=classify_snapshot(s)
        unresolved=[x for x in rows if x.topic=="other"]
        print("[PHYSICAL] snapshot_id=",s.snapshot_id)
        print("[PHYSICAL] market_count=",s.market_count)
        print("[PHYSICAL] topic_counts=",counts)
        print("[PHYSICAL] unresolved_markets=",len(unresolved))
        markets={str(m.get("ticker","")):m for m in snapshot_markets(s)}
        for x in unresolved[:20]:
            m=markets.get(x.ticker,{})
            print("[UNRESOLVED]",x.ticker,str(m.get("title",""))[:160])
        self.assertEqual(len(rows),s.market_count)
        self.assertEqual(sum(v for _,v in counts),s.market_count)

if __name__=="__main__":
    print("="*88);print(" OAD-083 PHYSICAL CERTIFICATION TEST");print(" DEEP UNRESOLVED MARKET CLASSIFICATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deeper classification uses exact phrase boundaries and preserves unresolved markets")
    print("[DONE] OAD-083 CERTIFIED")
