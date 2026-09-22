import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import *
class T(unittest.TestCase):
 def test_physical(self):
  r=acquire_independent_production_bundle(2); c=canonicalize_independent_bundle(r,"oad061.physical")
  print("[PHYSICAL] acquired=",len(r.observations),"canonicalized=",len(c))
  self.assertGreater(len(c),0); self.assertEqual(len(c),len(r.observations))
  self.assertTrue(all(dict(x.payload).get("independent_evidence") is True for x in c))
if __name__=="__main__":
 print("="*80); print(" OAD-061 PHYSICAL CERTIFICATION TEST"); print("="*80)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Existing OLA canonical contract accepted real independent observations"); print("[DONE] OAD-061 CERTIFIED")
