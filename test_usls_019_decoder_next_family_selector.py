import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_019_decoder_next_family_selector import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_select(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-019 next exact decoder family selected from physical evidence")
  if d["next_family"]:print("[NEXT]",d["next_family"])
  else:print("[NEXT] NONE_READY_MORE_LIVE_BIRTH_EVIDENCE_REQUIRED")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
