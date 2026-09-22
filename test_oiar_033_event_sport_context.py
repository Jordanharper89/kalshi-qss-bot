import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_033_event_sport_context as m
class T(unittest.TestCase):
 def test_soccer(self):self.assertEqual(m.classify_event_context({"market_title":"yes Both Teams To Score,yes Atletico,yes Real Madrid"})["sport"],"SOCCER")
 def test_baseball(self):self.assertEqual(m.classify_event_context({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh"})["sport"],"BASEBALL")
 def test_unknown_not_guessed(self):self.assertEqual(m.classify_event_context({"market_title":"Something Else"})["sport"],"UNKNOWN")
if __name__=="__main__":
 print("="*88);print(" OIAR-033 CERTIFICATION TEST");print(" EVENT AND SPORT CONTEXT");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] event/sport context certification complete");print("[DONE] OIAR-033 CERTIFIED")
