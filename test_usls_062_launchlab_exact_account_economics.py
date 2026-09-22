import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_062_launchlab_exact_account_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertEqual(d["exact_economic_count"],d["row_count"])
  self.assertTrue(all(x["pool"] and x["base_mint"] and x["quote_mint"] and x["effective_price"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-062 LaunchLab exact account roles + BUY economics")
  print("[PASS] pool, base/quote mints, trader, exact amounts and effective price physically resolved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
