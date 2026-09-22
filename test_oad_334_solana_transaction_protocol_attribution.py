\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_334_solana_transaction_protocol_attribution import *
class T(unittest.TestCase):
 def test_top_and_inner(self):
  e=SimpleNamespace(signature="s",slot=7,
   account_keys=("A","JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4","pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),
   instructions=({"programIdIndex":1},),
   inner_instructions=({"index":0,"instructions":[{"programIdIndex":2},{"programId":"Vote111111111111111111111111111111111111111"}]},))
  x=attribute_transaction_protocols((e,))[0]
  print("[ATTR]",x.known_protocols,"infra=",x.infrastructure_programs,"inner=",x.inner_program_ids)
  self.assertIn("JUPITER_V6",x.known_protocols)
  self.assertIn("PUMP_FUN_AMM",x.known_protocols)
  self.assertIn("SOLANA_VOTE",x.infrastructure_programs)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-334 top-level + CPI Solana protocol attribution certified")

