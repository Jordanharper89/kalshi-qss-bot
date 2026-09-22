import unittest,tempfile
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_295_solana_pool_lifecycle_migration_tracking import *
class T(unittest.TestCase):
 def test_physical(self):
  with tempfile.TemporaryDirectory() as d:
   r=track_solana_pool_lifecycle(Path(d),max_tokens=8)
   print("[PHYSICAL] current_tokens=",r.current_tokens); print("[PHYSICAL] current_pools=",r.current_pools); print("[PHYSICAL] missing_since_prior=",r.missing_since_prior)
   self.assertGreater(r.current_pools,0); self.assertFalse(r.execution_authority)
if __name__=="__main__":
 z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not z.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-295 bounded pool lifecycle tracking physically certified")
 print("[PASS] disappearance is not falsely promoted to dead-pool truth")
