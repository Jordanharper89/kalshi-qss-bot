import unittest
from qseries_v2.oracle_adapters.independent.oad_260_derivatives_open_interest_funding_physical_resilient_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  r=certify_live_derivatives_state()
  print("[PHYSICAL] provider=",r.provider); print("[PHYSICAL] symbol=",r.symbol); print("[PHYSICAL] open_interest=",r.open_interest); print("[PHYSICAL] funding_rate=",r.funding_rate); print("[PHYSICAL] primary_provider_succeeded=",r.primary_provider_succeeded); print("[PHYSICAL] fallback_used=",r.fallback_used)
  self.assertTrue(r.certified); self.assertFalse(r.execution_authority)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-260 physical live resilient derivatives acquisition certified")
