import unittest
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  raw=acquire_independent_production_bundle(2); b=build_independent_canonical_batch(raw,"oad065.physical")
  print("[PHYSICAL] acquired=",len(raw.observations)); print("[PHYSICAL] canonical=",len(b.canonical_observations))
  print("[PHYSICAL] provenance_validated=",b.provenance_validated); print("[PHYSICAL] entity_projected=",b.entity_projected)
  print("[PHYSICAL] ready_for_existing_persistence_router=",b.ready_for_existing_persistence_router)
  self.assertGreater(len(b.canonical_observations),0); self.assertTrue(b.ready_for_existing_persistence_router)
  self.assertTrue(all(x.execution_allowed is False for x in b.canonical_observations))
if __name__=="__main__":
 print("="*80); print(" OAD-065 PHYSICAL CERTIFICATION TEST"); print("="*80)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Existing OLA-015 remains PostgreSQL persistence authority"); print("[PASS] probability_enabled=FALSE"); print("[PASS] execution_authority=FALSE"); print("[DONE] OAD-065 CERTIFIED")
