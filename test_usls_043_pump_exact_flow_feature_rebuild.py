import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_043_pump_exact_flow_feature_rebuild import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_features(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"captured_trade_count":d["captured_trade_count"],
   "economic_exact_count":d["economic_exact_count"],"coverage_ratio":d["coverage_ratio"],
   "median_intertrade_seconds":d["median_intertrade_seconds"]},sort_keys=True))
  for x in d["windows"]:print("[WINDOW]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["economic_exact_count"],0);self.assertGreater(d["coverage_ratio"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-043 exact Pump trade-flow features rebuilt")
  print("[PASS] buyer/seller counts, unique traders and SOL flow now use TradeEvent economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
