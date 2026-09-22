import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_081_meteora_dbc_exact_transfer_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]: print("[DBC]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertEqual(d["exact_economic_count"],d["row_count"],"DBC_EXACT_ECONOMICS_INCOMPLETE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-081 DBC exact role + CPI-transfer economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
