import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle
from qseries_v2.oracle_adapters.independent.oad_063_independent_entity_term_projection import *
class T(unittest.TestCase):
 def test_physical(self):
  c=canonicalize_independent_bundle(acquire_independent_production_bundle(2),"oad063.physical"); e=[extract_independent_entity_terms(x) for x in c]
  print("[PHYSICAL] observations=",len(e),"with_terms=",sum(bool(x.terms) for x in e))
  self.assertGreater(len(e),0); self.assertTrue(any(x.terms for x in e))
if __name__=="__main__":
 print("="*80); print(" OAD-063 PHYSICAL CERTIFICATION TEST"); print("="*80)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Real observations projected into association terms"); print("[DONE] OAD-063 CERTIFIED")
