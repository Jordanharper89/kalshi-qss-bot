import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_062c_launchlab_exact_inner_transfer_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:
   print("[ECON]",json.dumps({k:x[k] for k in ("signature","parent_instruction_index","pool","base_mint","quote_mint",
    "matched_quote_transfers","matched_base_transfers","base_amount","quote_amount","effective_price","decoder_state")},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_economic_count"],d["row_count"],"LAUNCHLAB_INNER_TRANSFER_ECONOMICS_INCOMPLETE")
  self.assertTrue(all(x["effective_price"]>0 and x["side"]=="BUY" for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-062C LaunchLab exact inner-transfer economics")
  print("[PASS] actual token-program CPI transfers replace failed owner/account-index balance heuristics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
