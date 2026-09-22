import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(classify(BUY_EXACT_IN+b"123")["instruction_name"],"BUY_EXACT_IN")
  self.assertEqual(classify(BUY_EXACT_OUT+b"123")["instruction_name"],"BUY_EXACT_OUT")
  r=roles([str(i) for i in range(15)])
  self.assertEqual(r["pool_state"],"4");self.assertEqual(r["base_token_mint"],"9");self.assertEqual(r["quote_token_mint"],"10")
  self.assertEqual(d["official_trade_surface"],"BUY_ONLY_IN_CURRENT_IDL")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-060 LaunchLab official trade contract")
  print("[PASS] exact buy discriminators + 15-account role layout frozen from current official IDL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
