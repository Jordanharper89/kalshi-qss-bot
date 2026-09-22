import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_028_pump_sampled_path_outcomes import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_outcomes(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"token_address":d["token_address"],"sampled_mfe":d["sampled_mfe"],"sampled_mae":d["sampled_mae"],"remaining_horizons":d["remaining_horizons"]},sort_keys=True))
  for x in d["points"]:print("[OUTCOME]",json.dumps(x,sort_keys=True))
  self.assertEqual([x["horizon_seconds"] for x in d["points"]],[0,1,5,15,30])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-028 prospective sampled price-path outcomes")
  print("[PASS] MFE/MAE labels are sampled only, not continuous and not executable PnL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
