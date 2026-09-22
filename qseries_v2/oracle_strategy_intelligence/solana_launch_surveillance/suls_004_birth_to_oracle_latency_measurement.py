from __future__ import annotations
import json,statistics
from datetime import datetime
from pathlib import Path

def _dt(s):return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def measure(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/physical_multi_launcher_discovery.json"
 d=json.loads(src.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  ms=e.get("pair_created_at_ms")
  if ms is None:continue
  observed=_dt(e["oracle_observed_at"]).timestamp()
  created=float(ms)/1000.0
  latency=observed-created
  rows.append({"token_address":e["token_address"],"pair_address":e["pair_address"],
   "launcher_family":e["launcher_family"],"latency_seconds":latency,"nonnegative":latency>=0})
 vals=[x["latency_seconds"] for x in rows if x["nonnegative"]]
 return {"revision":"SULS_004","measured":len(rows),"valid_nonnegative":len(vals),
  "min_seconds":None if not vals else min(vals),"median_seconds":None if not vals else statistics.median(vals),
  "max_seconds":None if not vals else max(vals),"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=measure(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_to_oracle_latency.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
