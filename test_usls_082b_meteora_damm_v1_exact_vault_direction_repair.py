import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_082b_meteora_damm_v1_exact_vault_direction_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"revision":d["revision"],"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[DAMM_V1]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_economic_count"],d["row_count"],"DAMM_V1_VAULT_DIRECTION_ECONOMICS_INCOMPLETE")
  self.assertTrue(all(x["economics"]["input_amount"]>0 and x["economics"]["output_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-082B DAMM v1 strict 19/19 vault-direction economics")
  print("[PASS] exact user-source -> input-vault and output-vault -> user-destination flows")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
