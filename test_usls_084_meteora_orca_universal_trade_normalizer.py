import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_084_meteora_orca_universal_trade_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],"venue_counts":d["venue_counts"]},sort_keys=True))
  for v,n in d["venue_counts"].items():self.assertGreater(n,0,f"NO_EXACT_ROWS_{v}")
  self.assertTrue(all(x["input_mint"] and x["output_mint"] and x["input_amount"]>0 and x["output_amount"]>0 for x in d["rows"]))
  self.assertEqual(d["orientation_policy"],"INPUT_OUTPUT_NATIVE_NO_FORCED_QUOTE_SIDE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-084 Meteora + Orca exact trades normalized into universal tape")
  print("[PASS] arbitrary token-token pairs preserved without false BUY/SELL orientation")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
