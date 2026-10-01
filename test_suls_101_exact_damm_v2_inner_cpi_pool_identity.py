import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_101_exact_damm_v2_inner_cpi_pool_identity import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="accounts"},sort_keys=True))
  print("[ACCOUNTS]",json.dumps(d["accounts"],indent=2))
  self.assertGreaterEqual(d["account_count"],21)
  self.assertTrue(d["pool_address"])
  self.assertTrue(d["token_a_mint"])
  self.assertTrue(d["token_b_mint"])
  self.assertTrue(d["token_a_vault"])
  self.assertTrue(d["token_b_vault"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] SULS-101 exact DAMM V2 inner-CPI pool identity certification")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
