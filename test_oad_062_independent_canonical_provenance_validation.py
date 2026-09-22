import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from qseries_v2.oracle_adapters.independent.oad_062_independent_canonical_provenance_validation import *
class T(unittest.TestCase):
 def test_physical(self):
  c=canonicalize_independent_bundle(acquire_independent_production_bundle(2),"oad062.physical"); v=[validate_independent_canonical(x) for x in c]
  print("[PHYSICAL] provenance_validated=",sum(x.valid for x in v),"total=",len(v))
  self.assertGreater(len(v),0); self.assertTrue(all(x.valid for x in v))
if __name__=="__main__":
 print("="*80); print(" OAD-062 PHYSICAL CERTIFICATION TEST"); print("="*80)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Independent provenance survives canonicalization"); print("[DONE] OAD-062 CERTIFIED")
