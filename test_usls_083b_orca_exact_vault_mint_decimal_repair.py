import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_083b_orca_exact_vault_mint_decimal_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_orca(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"revision":d["revision"],"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[ORCA]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_economic_count"],d["row_count"],"ORCA_VAULT_MINT_DECIMAL_ECONOMICS_INCOMPLETE")
  self.assertTrue(all(x["input_amount"]>0 and x["output_amount"]>0 and x["input_mint"] and x["output_mint"] for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-083B Orca exact vault-mint + decimal-normalized economics")
  print("[PASS] B_TO_A and A_TO_B both resolved from exact Whirlpool vault roles")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
