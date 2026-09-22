import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_026_pump_marginal_price_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_price(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:print("[PRICE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertTrue(all(x["marginal_quote_per_token"] is not None and x["marginal_quote_per_token"]>0 for x in d["rows"]))
  self.assertTrue(all(not x["profitability_eligible"] for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-026 Pump marginal price semantics certified")
  print("[PASS] reserve-derived price is explicitly blocked from executable-profit claims")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
