\

import tempfile,unittest
from qseries_v2.oracle_adapters.independent.oad_323_solana_durable_slot_checkpoint import *
class T(unittest.TestCase):
 def test_restart_and_regression(self):
  with tempfile.TemporaryDirectory() as d:
   a=load_solana_chain_checkpoint(d);self.assertIsNone(a.last_committed_slot)
   b=commit_solana_chain_checkpoint(100,"sig100",d);c=load_solana_chain_checkpoint(d)
   print("[CHECKPOINT]",c.last_committed_slot,c.last_committed_signature,"generation=",c.generation)
   self.assertEqual(c.last_committed_slot,100);self.assertEqual(c.generation,1)
   with self.assertRaises(ValueError):commit_solana_chain_checkpoint(99,"old",d)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-323 durable Solana slot checkpoint + regression guard certified")

