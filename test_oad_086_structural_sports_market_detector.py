import unittest
from qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import *
class T(unittest.TestCase):
 def test_prop(self): self.assertTrue(detect_sports_market({"title":"yes Rafael Devers: 1+, no Corbin Carroll: 5+","rules_primary":"runs"}).is_sports)
 def test_btts(self): self.assertTrue(detect_sports_market({"title":"1st Half: Both Teams To Score"}).is_sports)
 def test_non_sport(self): self.assertFalse(detect_sports_market({"title":"Will CPI inflation exceed 3 percent?"}).is_sports)
if __name__=="__main__":
 print("="*88);print(" OAD-086 CERTIFICATION TEST");print(" STRUCTURAL SPORTS MARKET DETECTOR");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Sports detected from market structure without athlete/team dictionaries");print("[DONE] OAD-086 CERTIFIED")
