import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_033_live_opportunity_feed_progression_gate import observe
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=observe(ROOT,3,.25);self.assertFalse(d["execution_authority"])
  print("[CYCLES]",d["cycles"]);print("[NATIVE_ROWS_TOTAL]",d["native_rows_total"]);print("[GMGN_ROWS_TOTAL]",d["gmgn_rows_total"])
  print("[NORMALIZED_EVENTS_TOTAL]",d["normalized_events_total"])
  print("[PHYSICAL_ROWS]",d["feed_has_physical_rows"]);print("[NORMALIZED_FEED]",d["feed_has_normalized_events"])
  if not d["feed_has_physical_rows"]:self.fail("NO_REGISTERED_SOLANA_OR_GMGN_PHYSICAL_ROWS")
  if not d["feed_has_normalized_events"]:self.fail("PHYSICAL_ROWS_PRESENT_BUT_NO_NORMALIZED_OPPORTUNITY_EVENTS")
  print("[PASS] OSI-033 live opportunity feed progression gate")
  print("[TRADER] Dedicated Solana runtime is physically receiving opportunity-grade records")
  print("[SCOPE] Feed progression only; thesis/outcome/learning activation comes next")
if __name__=="__main__":unittest.main()
