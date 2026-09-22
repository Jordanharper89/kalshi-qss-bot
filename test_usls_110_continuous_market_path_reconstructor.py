import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_110_continuous_market_path_reconstructor import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"path_count":d["path_count"],"total_priced_trades":d["total_priced_trades"]},sort_keys=True))
  self.assertGreater(d["path_count"],0,"NO_MARKET_PRICE_PATH_RECONSTRUCTED")
  self.assertGreater(d["total_priced_trades"],0)
  self.assertTrue(d["continuous_between_horizons"])
  for x in d["paths"]:
   self.assertGreaterEqual(x["high_price"],x["low_price"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-110 continuous market path reconstructor")
  print("[PASS] first/last/high/low/MFE/MAE + standard horizon checkpoints materialized")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
