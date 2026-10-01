import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_011_money_hunt_priority import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_policy(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIsNotNone(d["primary_money_hunt_family"],"NO_PHYSICAL_FRICTION_SUPPORTED_FAMILY")
  self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-011 money-hunt priority policy")
  print("[PRIMARY]",d["primary_money_hunt_family"])
if __name__=="__main__":unittest.main()
