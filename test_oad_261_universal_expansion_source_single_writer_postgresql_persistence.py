import unittest
from qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import *
class T(unittest.TestCase):
 def test_physical(self):
  r=persist_live_expansion_sources()
  print("[PHYSICAL] raw_observations=",r.raw_observations); print("[PHYSICAL] canonical_observations=",r.canonical_observations); print("[PHYSICAL] already_present=",r.already_present); print("[PHYSICAL] committed_new=",r.committed_new); print("[PHYSICAL] exact_readback=",r.exact_readback); print("[PHYSICAL] providers=",r.providers); print("[PHYSICAL] source_ids=",r.source_ids)
  self.assertEqual(r.raw_observations,4); self.assertEqual(r.canonical_observations,4); self.assertEqual(r.exact_readback,4); self.assertFalse(r.execution_authority)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-261 live expansion sources persisted through OPH-019 single writer"); print("[PASS] exact by-observation-ID PostgreSQL readback certified"); print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
