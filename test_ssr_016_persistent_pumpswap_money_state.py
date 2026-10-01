import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_016_persistent_pumpswap_money_state import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_state(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["family"],"PUMP_SWAP");self.assertGreaterEqual(d["physical_friction_row_count"],1)
  self.assertFalse(d["execution_authority"]);print("[PASS] SSR-016 persistent PumpSwap money state")
if __name__=="__main__":unittest.main()
