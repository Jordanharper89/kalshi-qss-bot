
import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_029_trader_session_context as m
class T(unittest.TestCase):
 def test_context(self):
  c=m.TraderSessionContext();self.assertEqual(c.timeframe,"now");self.assertEqual(c.direction,"any")
if __name__=="__main__":
 print("="*88);print(" OIAR-029 CERTIFICATION TEST");print(" TRADER SESSION CONTEXT");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] trader session/timeframe context certified");print("[DONE] OIAR-029 CERTIFIED")
