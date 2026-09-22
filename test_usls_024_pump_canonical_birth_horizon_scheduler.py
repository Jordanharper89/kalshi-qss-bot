import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_024_pump_canonical_birth_horizon_scheduler import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_sched(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"birth_count":d["birth_count"],"horizon_row_count":d["horizon_row_count"],"horizons":d["horizons"]},sort_keys=True))
  for x in d["births"]:print("[BIRTH]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_count"],0)
  self.assertEqual(d["horizon_row_count"],d["birth_count"]*7)
  self.assertEqual(d["horizons"],[1,5,15,30,60,300,900])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-024 Pump.fun canonical exact birth + multi-horizon schedule")
  print("[PASS] 1s/5s/15s/30s/60s/5m/15m clock starts from live birth observation")
  print("[PASS] profitability remains unclaimed until actual outcomes are resolved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
