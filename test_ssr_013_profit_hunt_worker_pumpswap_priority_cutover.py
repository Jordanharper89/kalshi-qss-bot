import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_013_profit_hunt_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cutover(self):
  d=cycle(ROOT,dry_run=True);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["primary_family"],"PUMP_SWAP");self.assertIn("FOLLOW_PUMPSWAP_FIRST",d["pipeline"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-013 PumpSwap-priority profit-hunt worker")
if __name__=="__main__":unittest.main()
