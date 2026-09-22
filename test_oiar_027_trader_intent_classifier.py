
import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_027_trader_intent_classifier import classify_trader_intent as c
class T(unittest.TestCase):
 def test_plays(self):self.assertEqual(c("what are the plays for this evening?").route,"trader_brief")
 def test_strongest(self):self.assertEqual(c("what is the strongest?").ranking,"strongest")
 def test_bull(self):self.assertEqual(c("anything bullish").direction,"bullish")
 def test_fallback(self):self.assertEqual(c("price of bitcoin").route,"fallback")
if __name__=="__main__":
 print("="*88);print(" OIAR-027 CERTIFICATION TEST");print(" TRADER INTENT CLASSIFIER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] broad trader intent routing certified");print("[DONE] OIAR-027 CERTIFIED")
