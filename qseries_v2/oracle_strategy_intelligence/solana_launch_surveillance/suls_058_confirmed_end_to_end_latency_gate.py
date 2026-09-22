from __future__ import annotations
import json,time
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_057_incremental_confirmed_head_worker import cycle

def run(root,samples=3):
 rows=[]
 for _ in range(samples):
  d=cycle(root);rows.append(d);time.sleep(0.2)
 mx=max(x["cycle_seconds"] for x in rows);avg=sum(x["cycle_seconds"] for x in rows)/len(rows)
 return {"revision":"SULS_058","samples":rows,"max_cycle_seconds":mx,"avg_cycle_seconds":avg,
  "worker_cycle_under_5s":mx<=5.0,"execution_authority":False,"read_only":True,
  "scope":"Measures acquisition+decode worker time, not guaranteed birth age until a birth is observed"}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_end_to_end_latency_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
