from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_065_fast_lane_continuity_gap_gate.py"
TEST=ROOT/"test_suls_065_fast_lane_continuity_gap_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_062_confirmed_fast_lane_runtime_worker import cycle

def run(root,cycles=4):
 rows=[]
 for _ in range(cycles):
  rows.append(cycle(root));time.sleep(0.15)
 slots=[int(x["capture"]["slot"]) for x in rows]
 monotonic=all(b>=a for a,b in zip(slots,slots[1:]))
 gaps=[b-a for a,b in zip(slots,slots[1:]) if b-a>1]
 d={"revision":"SULS_065","cycles":len(rows),"slots":slots,"monotonic":monotonic,
  "observed_gap_sizes":gaps,"restart_gap_backfill_ready":False,
  "execution_authority":False,"read_only":True,
  "scope":"Detects slot gaps; exact restart/backfill closure remains downstream"}
 p=root/"runtime_state/solana_opportunities/launch_surveillance/fast_lane_continuity_gap_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_065_fast_lane_continuity_gap_gate import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=run(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["monotonic"]:self.fail("FAST_LANE_SLOT_ROLLBACK")
  print("[PASS] SULS-065 fast-lane continuity/gap gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")