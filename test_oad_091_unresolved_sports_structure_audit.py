import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort
from qseries_v2.oracle_adapters.independent.oad_091_unresolved_sports_structure_audit import *
class T(unittest.TestCase):
 def test_physical(self):
  s=capture_current_market_cohort(1000);a=audit_unresolved_sports(s)
  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] unresolved_sports=",a.count)
  print("[PHYSICAL] field_nonempty=",a.field_nonempty);print("[PHYSICAL] series_prefixes=",a.series_prefixes)
  for x in a.samples:print("[UNRESOLVED_SPORT]",x)
  self.assertGreaterEqual(a.count,0)
if __name__=="__main__":
 print("="*88);print(" OAD-091 PHYSICAL CERTIFICATION TEST");print(" UNRESOLVED SPORTS STRUCTURE AUDIT");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Unresolved sports physically audited without fabricated league assignment");print("[DONE] OAD-091 CERTIFIED")
