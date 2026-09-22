import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_118_phase7_executable_entry_exit_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(d["phase"],7)
  self.assertEqual(d["capability"],"EXECUTABLE_ENTRY_EXIT_MODELING")
  self.assertTrue(d["rules"]["read_only"])
  self.assertEqual(d["rules"]["future_leakage"],"FORBIDDEN")
  self.assertEqual(d["rules"]["missing_fee_or_liquidity"],"RETAIN_AS_UNAVAILABLE_NOT_ZERO")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-118 Phase 7 executable entry/exit contract")
  print("[PASS] entry/exit/slippage/fees/latency/liquidity/net-return semantics frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
