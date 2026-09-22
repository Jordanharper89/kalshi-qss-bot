\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_320_solana_program_instruction_registry import *
class T(unittest.TestCase):
 def test_unknown_retained(self):
  e=SimpleNamespace(signature="s",instructions=({"programId":"NEWPROGRAM","parsed":{"type":"mystery"}},),inner_instructions=(),account_keys=())
  x=classify_transaction_instructions((e,))[0]
  print("[PROGRAM]",x.program_id,x.program_class,"retained=",x.retained)
  self.assertEqual(x.program_class,"UNKNOWN_PROGRAM"); self.assertTrue(x.retained)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-320 known + unknown Solana instruction accounting certified")

