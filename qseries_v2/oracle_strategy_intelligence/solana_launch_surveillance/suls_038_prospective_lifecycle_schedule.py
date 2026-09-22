from __future__ import annotations
import json
HORIZONS=(1,5,15,30,60,300,900)
def build(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  bt=float(e["block_time"])
  for h in HORIZONS:
   rows.append({"event_id":e["event_id"],"signature":e["signature"],"horizon_seconds":h,
    "target_unix":bt+h,"state":"PENDING","execution_authority":False})
 return {"revision":"SULS_038","horizons":list(HORIZONS),"pending_count":len(rows),"pending":rows,
  "execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/prospective_lifecycle_schedule.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
