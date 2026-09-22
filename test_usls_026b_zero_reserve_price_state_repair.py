import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_026b_zero_reserve_price_state_repair import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_repair(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "row_count":d["row_count"],
   "price_available_count":d["price_available_count"],
   "price_unavailable_count":d["price_unavailable_count"],
   "profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:
   print("[PRICE]",json.dumps({
    "token_address":x["token_address"],
    "quote_mint":x["quote_mint"],
    "marginal_quote_per_token":x["marginal_quote_per_token"],
    "price_state":x["price_state"]},sort_keys=True))
  self.assertEqual(d["row_count"],3)
  self.assertGreaterEqual(d["price_available_count"],2)
  self.assertGreaterEqual(d["price_unavailable_count"],1)
  self.assertTrue(all((x["marginal_quote_per_token"] is None) ==
                      (not x["price_available"]) for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-026B zero-reserve price state repaired")
  print("[PASS] unavailable curves retained without fabricated price")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
