import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_082_meteora_damm_v1_strict_vault_mint_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[DAMM_V1]",json.dumps(x,sort_keys=True))
  self.assertEqual(d["exact_economic_count"],d["row_count"],"DAMM_V1_STRICT_ECONOMICS_INCOMPLETE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-082 DAMM v1 19/19 strict vault-side mint/economics reconciliation")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
