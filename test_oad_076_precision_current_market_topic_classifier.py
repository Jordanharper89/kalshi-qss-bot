import unittest
from qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import *

class T(unittest.TestCase):
    def test_storm_surname_not_weather(self):
        x=classify_market_topic({"ticker":"X","title":"Lloyd Storm vs Frances Tiafoe"})
        self.assertEqual(x.primary_topic,"sports")
    def test_real_storm_weather(self):
        x=classify_market_topic({"ticker":"X","title":"Will a tropical storm make landfall in Florida?"})
        self.assertEqual(x.primary_topic,"weather")
    def test_florida_person_fragment_not_geography_logic(self):
        x=classify_market_topic({"ticker":"X","title":"Dakota Davis vs Florida King"})
        self.assertNotEqual(x.primary_topic,"weather")
    def test_verify(self): self.assertTrue(verify_oad_076_false_positive_guards())

if __name__=="__main__":
    print("="*88);print(" OAD-076 CERTIFICATION TEST");print(" PRECISION CURRENT-MARKET TOPIC CLASSIFIER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Substring/name collisions no longer create weather classifications")
    print("[PASS] Exact phrase boundaries and context rules certified")
    print("[DONE] OAD-076 CERTIFIED")
