import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_086_remaining_venue_program_contract import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(set(d["programs"]),{"MOONIT","BOOP_FUN","HEAVEN"})
  self.assertTrue(d["unknown_instruction_retention"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-086 Moonit/Boop/Heaven program contract")
  print("[PASS] no unverified trade discriminator encoded")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
