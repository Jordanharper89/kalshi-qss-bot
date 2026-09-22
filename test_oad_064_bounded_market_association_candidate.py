import unittest
from qseries_v2.oracle_adapters.independent.oad_064_bounded_market_association_candidate import *
class T(unittest.TestCase):
 def test_bounded(self):
  class E: observation_id="o1"; terms=("federal","reserve","rate")
  r=bounded_market_association_candidates(E(),{"KX1":("federal","reserve"),"KX2":("weather","rain")})
  self.assertEqual(r[0].market_id,"KX1"); self.assertTrue(r[0].candidate_only)
 def test_no_scan(self):
  class E: observation_id="o"; terms=()
  with self.assertRaises(TypeError): bounded_market_association_candidates(E(),[])
if __name__=="__main__":
 print("="*80); print(" OAD-064 CERTIFICATION TEST"); print("="*80)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Association accepts only pre-bounded/indexed market sets"); print("[DONE] OAD-064 CERTIFIED")
