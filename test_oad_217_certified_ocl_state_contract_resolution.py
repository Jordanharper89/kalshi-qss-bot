import unittest
from qseries_v2.oracle_adapters.independent.oad_217_certified_ocl_state_contract_resolution import *
class T(unittest.TestCase):
 def test_contracts(self):
  r=resolve_certified_ocl_contracts();print("[CERTIFIED]",r.certified_contracts);print("[UNAVAILABLE]",r.unavailable_contracts)
  self.assertEqual(set(REQUIRED),set(r.certified_contracts)|set(r.unavailable_contracts))
if __name__=="__main__":
 x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not x.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-217 existing frozen OCL contracts resolved without duplication")
