import unittest
from qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import *
class T(unittest.TestCase):
 def test_macro(self):self.assertEqual(expanded_domain_classify({"title":"Will CPI inflation exceed 3%?"}).domain,"macroeconomics")
 def test_crypto(self):self.assertEqual(expanded_domain_classify({"title":"Will Bitcoin exceed $100k?"}).domain,"crypto")
 def test_unknown(self):self.assertEqual(expanded_domain_classify({"title":"Unrecognized proposition"}).domain,"other")
if __name__=="__main__":
 print("="*88);print(" OAD-094 CERTIFICATION TEST");print(" EXPANDED UNIVERSAL DOMAIN CLASSIFIER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Expanded non-sports domain classification certified");print("[DONE] OAD-094 CERTIFIED")
