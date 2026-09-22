from __future__ import annotations
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
