
import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_028_relative_strength_semantics as m
class T(unittest.TestCase):
 def test_strongest_not_edge(self):
  x=m.strongest_assessment([{"market_id":"A","setup_status":"NO_CONFIRMED_EDGE","live_evidence":"WEAK","historical_strength":"STRONG","direction":"NEUTRAL"}])
  self.assertFalse(x["clears_edge"]);self.assertIn("does not clear",x["message"])
if __name__=="__main__":
 print("="*88);print(" OIAR-028 CERTIFICATION TEST");print(" RELATIVE STRENGTH SEMANTICS");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] strongest-is-not-automatically-good semantics certified");print("[DONE] OIAR-028 CERTIFIED")
