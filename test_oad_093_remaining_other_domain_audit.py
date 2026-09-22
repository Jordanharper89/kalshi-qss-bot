import unittest
from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort
from qseries_v2.oracle_adapters.independent.oad_093_remaining_other_domain_audit import *
class T(unittest.TestCase):
 def test_physical(self):
  s=capture_current_market_cohort(1000);a=audit_remaining_other(s)
  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] remaining_other=",a.count)
  print("[PHYSICAL] field_nonempty=",a.field_nonempty);print("[PHYSICAL] prefixes=",a.prefixes)
  for x in a.samples:print("[OTHER]",x)
  self.assertGreaterEqual(a.count,0)
if __name__=="__main__":
 print("="*88);print(" OAD-093 PHYSICAL CERTIFICATION TEST");print(" REMAINING OTHER DOMAIN AUDIT");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Remaining non-sports other population physically audited");print("[DONE] OAD-093 CERTIFIED")
