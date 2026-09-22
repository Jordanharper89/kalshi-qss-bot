from __future__ import annotations
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
