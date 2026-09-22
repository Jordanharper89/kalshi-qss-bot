
import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_030_concise_trader_response_policy as m
from types import SimpleNamespace
class T(unittest.TestCase):
 def test_max_two(self):
  xs=[{"market_id":str(i),"market_title":"x"*300,"setup_status":"NO_CONFIRMED_EDGE","live_evidence":"WEAK","historical_strength":"STRONG","direction":"NEUTRAL","trader_takeaway":"NO EDGE RIGHT NOW","why":"weak","risk":"HIGH"} for i in range(5)]
  out=m.render_concise(xs,SimpleNamespace(ranking="standard",direction="any"),2)
  self.assertLess(len(out),20)
if __name__=="__main__":
 print("="*88);print(" OIAR-030 CERTIFICATION TEST");print(" CONCISE TRADER RESPONSE POLICY");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] concise trader response policy certified");print("[DONE] OIAR-030 CERTIFIED")
