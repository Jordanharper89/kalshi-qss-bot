import unittest,tempfile
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_294_solana_universe_durable_change_detection import *
class T(unittest.TestCase):
 def test_physical(self):
  with tempfile.TemporaryDirectory() as d:
   r=detect_and_checkpoint_solana_universe_changes(root=Path(d),max_tokens=8)
   print("[PHYSICAL] current_tokens=",r.current_tokens); print("[PHYSICAL] current_pools=",r.current_pools); print("[PHYSICAL] new_tokens=",len(r.new_tokens)); print("[PHYSICAL] new_pools=",len(r.new_pools))
   self.assertGreater(r.current_tokens,0); self.assertGreater(r.current_pools,0)
if __name__=="__main__":
 z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not z.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-294 durable new-token/new-pool change detection physically certified")
