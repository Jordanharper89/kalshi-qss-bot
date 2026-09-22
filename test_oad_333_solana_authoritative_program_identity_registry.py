\

import unittest
from qseries_v2.oracle_adapters.independent.oad_333_solana_authoritative_program_identity_registry import *
class T(unittest.TestCase):
 def test_registry(self):
  vote=identify_solana_program("Vote111111111111111111111111111111111111111")
  pump=identify_solana_program("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
  jup=identify_solana_program("JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4")
  met=identify_solana_program("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo")
  print("[PROGRAMS]",vote.name,pump.name,jup.name,met.name)
  self.assertFalse(vote.market_relevant)
  self.assertEqual(pump.name,"PUMP_FUN_AMM")
  self.assertEqual(jup.category,"ROUTER")
  self.assertEqual(met.name,"METEORA_DLMM")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-333 authoritative Solana program identity registry certified")

