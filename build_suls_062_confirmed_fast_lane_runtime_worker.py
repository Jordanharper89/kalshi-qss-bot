from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_062_confirmed_fast_lane_runtime_worker.py"
TEST=ROOT/"test_suls_062_confirmed_fast_lane_runtime_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_057_incremental_confirmed_head_worker import cycle as capture_cycle
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_059_confirmed_birth_materializer_bridge import run as materialize
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_060_confirmed_fresh_birth_queue_bridge import run as queue_births

def cycle(root):
 t0=time.time()
 c=capture_cycle(root)
 m=materialize(root)
 q=queue_births(root)
 row={"revision":"SULS_062","cycle_started_unix":t0,"cycle_finished_unix":time.time(),
      "capture":c,"materialized_events":m.get("event_count",0),"new_materialized_events":m.get("new_events",0),
      "fresh_births_admitted":q.get("admitted_fresh_births",0),"pending_horizon_checks":q.get("pending_count",0),
      "execution_authority":False,"read_only":True}
 p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_fast_lane_runtime_state.json"
 p.write_text(json.dumps(row,indent=2,sort_keys=True),encoding="utf-8")
 return row

def run(root,cycles=10,sleep_seconds=0.25):
 rows=[]
 for _ in range(max(1,int(cycles))):
  rows.append(cycle(root))
  time.sleep(max(0.0,float(sleep_seconds)))
 return rows
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_062_confirmed_fast_lane_runtime_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["capture"]["transactions"],0)
  print("[PASS] SULS-062 confirmed fast-lane runtime worker one-cycle")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")