import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertNotEqual(CORRECT_PROGRAM,RETIRED_BAD_PROGRAM)
  self.assertEqual(CORRECT_PROGRAM,"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB")
  self.assertEqual(SWAP_DISC.hex(),"f8c69e91e17587c8")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-075 Meteora DAMM v1 program-ID correction")
  print("[PASS] retired bad ...67jJ... address; official ...67rjJ... address frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
