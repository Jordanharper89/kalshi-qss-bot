\

import tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_326_solana_universal_resilient_worker as m
class T(unittest.TestCase):
 def test_commit_after_persistence(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.object(m,"_rpc",return_value=12),patch.object(m,"persist_solana_universal_chain_batch",return_value=SimpleNamespace(transactions=4,observations=8,committed_events=8,coverage_state="UNIVERSAL_BATCH_ACCOUNTED")):
    x=m.run_solana_universal_worker_cycle(d,2)
   cp=m.load_solana_chain_checkpoint(d)
   print("[WORKER]",x.mode,x.before_slot,"->",x.after_slot,"checkpoint=",cp.last_committed_slot)
   self.assertEqual(cp.last_committed_slot,x.after_slot);self.assertEqual(x.state,"COMMITTED")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-326 checkpoint advances only after successful universal persistence")

