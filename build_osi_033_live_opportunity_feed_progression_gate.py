from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_033_live_opportunity_feed_progression_gate.py"
TEST=ROOT/"test_osi_033_live_opportunity_feed_progression_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_032_lean_live_ingestion_cycle import cycle
def observe(root:Path,cycles:int=3,interval:float=1.0)->dict:
 rows=[]
 for _ in range(cycles):
  rows.append(cycle(root));time.sleep(interval)
 total_norm=sum(x["normalized_events"] for x in rows)
 total_native=sum(x["native_rows"] for x in rows)
 total_gmgn=sum(x["gmgn_rows"] for x in rows)
 return {"revision":"OSI_033","cycles":len(rows),"native_rows_total":total_native,"gmgn_rows_total":total_gmgn,
  "normalized_events_total":total_norm,"feed_has_physical_rows":(total_native+total_gmgn)>0,
  "feed_has_normalized_events":total_norm>0,"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest,json
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
"""
def main():
 print("="*112);print(" OSI-033 LIVE OPPORTUNITY FEED PROGRESSION GATE");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
