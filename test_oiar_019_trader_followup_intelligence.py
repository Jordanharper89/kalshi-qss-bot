import unittest
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_019_trader_followup_intelligence import classify_followup,OIAR_019_BUILD_ID
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OIAR_019_BUILD_ID,"OIAR-019")
    def test_routes(self):self.assertEqual(classify_followup("why do you like it"),"WHY");self.assertEqual(classify_followup("whats the risk"),"RISK")
if __name__=="__main__":
    print("="*88);print(" OIAR-019 CERTIFICATION TEST");print(" TRADER FOLLOW-UP INTELLIGENCE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] trader follow-up routing certified")
    print("[DONE] OIAR-019 CERTIFIED")
