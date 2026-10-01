import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_080_event_driven_lifecycle_bridge import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bridge(self):
  d=run(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["executable_pnl_claimed"])
  print("[PASS] SULS-080 event-driven lifecycle bridge")
  print("[SCOPE] Current reserve-ratio outcomes remain observational, not executable PnL")
if __name__=="__main__":unittest.main()
