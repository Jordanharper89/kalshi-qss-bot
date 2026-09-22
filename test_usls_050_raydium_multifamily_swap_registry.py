import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertTrue(classify("RAYDIUM_V4",bytes([9])+b"\0"*16)["is_exact_swap"])
  self.assertEqual(classify("RAYDIUM_CPMM",bytes.fromhex("8fbe5adac41e33de"))["instruction_name"],"SWAP_BASE_INPUT")
  self.assertEqual(classify("RAYDIUM_CLMM",bytes.fromhex("2b04ed0b1ac91e62"))["instruction_name"],"SWAP_V2")
  self.assertEqual(classify("RAYDIUM_LAUNCHLAB",bytes.fromhex("faea0d7bd59c13ec"))["instruction_name"],"BUY_EXACT_IN")
  self.assertFalse(classify("RAYDIUM_LAUNCHLAB",b"\xff"*8)["is_exact_swap"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-050 Raydium multi-family exact swap registry")
  print("[PASS] V4/CPMM/CLMM exact swap keys registered; LaunchLab verified buys only")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
