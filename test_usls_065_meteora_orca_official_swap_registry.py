import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_065_meteora_orca_official_swap_registry import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertTrue(classify("METEORA_DBC",disc("swap"))["is_exact_swap"])
  self.assertTrue(classify("METEORA_DAMM",disc("swap2"))["is_exact_swap"])
  self.assertTrue(classify("METEORA_DLMM",disc("swap2"))["is_exact_swap"])
  self.assertTrue(classify("ORCA",disc("swap_v2"))["is_exact_swap"])
  self.assertEqual(d["instruction_names"]["METEORA_DYN"],[])
  self.assertTrue(d["unknown_retention"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-065 Meteora/Orca official swap registry")
  print("[PASS] DBC/DAMM/DLMM/Orca exact names registered; DAMM v1/DYN held observe-only")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
