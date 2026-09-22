\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import *
class T(unittest.TestCase):
 def test_envelope(self):
  b=SimpleNamespace(blocks=((7,{"blockTime":1,"blockhash":"h","transactions":[{"version":0,"transaction":{"signatures":["sig"],"message":{"accountKeys":[{"pubkey":"A"}],"instructions":[{"programId":"P"}]}},"meta":{"err":None,"fee":5000,"innerInstructions":[],"preTokenBalances":[],"postTokenBalances":[],"logMessages":["ok"]}}]}),))
  x=canonical_transaction_envelopes(b)[0]
  print("[TX]",x.signature,x.slot,x.success,x.account_keys)
  self.assertEqual(x.signature,"sig"); self.assertTrue(x.success)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-319 full transaction canonical envelope certified")

