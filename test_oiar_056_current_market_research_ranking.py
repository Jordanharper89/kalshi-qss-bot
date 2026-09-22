import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_056_current_market_research_ranking as m
class T(unittest.TestCase):
    def test_identity(self): self.assertEqual(m.OIAR_056_BUILD_ID,"OIAR-056")
    def test_snapshot(self):
        x=m.read_latest_current_market_research_ranking()
        self.assertTrue(x); self.assertGreater(x["market_count"],0)
        self.assertTrue(x["ranking_is_research_priority_only"]); self.assertFalse(x["execution_authority"])
        self.assertEqual([v["rank"] for v in x["markets"]], list(range(1,len(x["markets"])+1)))
if __name__=="__main__":
    print("="*88);print(" OIAR-056 CERTIFICATION TEST");print(" CURRENT MARKET RESEARCH RANKING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] current research ranking certified");print("[DONE] OIAR-056 CERTIFIED")
