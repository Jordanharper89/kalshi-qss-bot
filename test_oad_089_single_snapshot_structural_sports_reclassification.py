import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort
from qseries_v2.oracle_adapters.independent.oad_089_single_snapshot_structural_sports_reclassification import *
class T(unittest.TestCase):
 def test_physical(self):
  s=capture_current_market_cohort(1000);r=reclassify_snapshot_with_structural_sports(s)
  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] market_count=",r.market_count)
  print("[PHYSICAL] baseline_sports=",r.baseline_sports);print("[PHYSICAL] structural_sports=",r.structural_sports)
  print("[PHYSICAL] rescued_from_other=",r.rescued_from_other);print("[PHYSICAL] unresolved=",r.unresolved)
  print("[PHYSICAL] sport_counts=",r.sport_counts);print("[PHYSICAL] market_type_counts=",r.market_type_counts)
  self.assertEqual(r.market_count,s.market_count);self.assertGreaterEqual(r.structural_sports,r.rescued_from_other)
if __name__=="__main__":
 print("="*88);print(" OAD-089 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT STRUCTURAL SPORTS RECLASSIFICATION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Structural sports rescue measured on one immutable live cohort");print("[DONE] OAD-089 CERTIFIED")
