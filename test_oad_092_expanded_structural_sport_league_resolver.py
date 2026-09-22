import unittest
from qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import *
class T(unittest.TestCase):
 def test_mma(self):self.assertEqual(expanded_resolve_sport_league({"title":"Fight Night bout by submission","rules_primary":"MMA"}).league,"UFC_MMA")
 def test_tennis(self):self.assertEqual(expanded_resolve_sport_league({"title":"Will player win Set 1?","rules_primary":"tennis"}).league,"ATP_WTA")
 def test_unknown(self):self.assertEqual(expanded_resolve_sport_league({"title":"Team prop points scored"}).league,"UNKNOWN")
if __name__=="__main__":
 print("="*88);print(" OAD-092 CERTIFICATION TEST");print(" EXPANDED STRUCTURAL SPORT / LEAGUE RESOLVER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Additional sport structures resolved without player/team dictionaries");print("[DONE] OAD-092 CERTIFIED")
