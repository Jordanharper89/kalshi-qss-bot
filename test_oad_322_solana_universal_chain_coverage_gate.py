\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_322_solana_universal_chain_coverage_gate as m
class T(unittest.TestCase):
 def test_accounting(self):
  batch=SimpleNamespace(blocks=((1,{"blockTime":1,"blockhash":"h","transactions":[{"version":"legacy","transaction":{"signatures":["s"],"message":{"accountKeys":["A"],"instructions":[{"programId":"UNKNOWN"}]}},"meta":{"err":None,"fee":1,"innerInstructions":[],"preTokenBalances":[],"postTokenBalances":[],"logMessages":[]}}]}),))
  with patch.object(m,"acquire_finalized_block_batch",return_value=batch):
   x=m.build_universal_coverage_batch()
  print("[COVERAGE] blocks=",x.blocks,"transactions=",x.transactions,"unknown_instructions=",x.unknown_instructions,"state=",x.state)
  self.assertEqual(x.transactions,1); self.assertEqual(x.transaction_accounting_ratio,1.0); self.assertEqual(x.state,"UNIVERSAL_BATCH_ACCOUNTED")
  self.assertGreaterEqual(len(x.observations),1)
  self.assertEqual(x.unknown_instructions,1)
  self.assertEqual(x.instructions_accounted,x.instructions)
  self.assertTrue(all(getattr(o,"observed_at",None) is not None for o in x.observations))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-322 universal Solana chain accounting gate certified")
 print("[PASS] unknown programs retained rather than discarded")

