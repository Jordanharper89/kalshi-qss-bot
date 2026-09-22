import unittest
from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import *
class T(unittest.TestCase):
 def test_btts(self):self.assertEqual(resolve_sports_market_type({"title":"1st Half: Both Teams To Score"}).market_type,"both_teams_to_score")
 def test_spread(self):self.assertEqual(resolve_sports_market_type({"title":"Indiana wins by over 1.5 points"}).market_type,"spread")
if __name__=="__main__":
 print("="*88);print(" OAD-088 CERTIFICATION TEST");print(" SPORTS MARKET-TYPE RESOLVER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Sports market-type resolution certified");print("[DONE] OAD-088 CERTIFIED")
