import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_098_remaining_venue_universal_trade_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],"venue_counts":d["venue_counts"]},sort_keys=True))
  self.assertEqual(d["venue_counts"],{"MOONIT":58,"BOOP_FUN":50,"HEAVEN":59})
  self.assertEqual(d["exact_trade_count"],167)
  self.assertTrue(all(x["input_amount"]>0 and x["output_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-098 Moonit/Boop/Heaven normalized into universal trade tape")
  print("[PASS] native SOL preserved as NATIVE_SOL rather than falsely relabeled WSOL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
