import unittest
from qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import *
class T(unittest.TestCase):
 def test_soccer(self):
  x=resolve_sport_league({"title":"1st Half: Both Teams To Score","rules_primary":"soccer goals"})
  self.assertEqual(x.sport,"soccer")
 def test_baseball(self):
  x=resolve_sport_league({"title":"Will the player hit 2 home runs?","series_ticker":"MLB"})
  self.assertEqual(x.league,"MLB")
if __name__=="__main__":
 print("="*88);print(" OAD-087 CERTIFICATION TEST");print(" SPORT / LEAGUE RESOLVER");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Sport and league resolution certified");print("[DONE] OAD-087 CERTIFIED")
