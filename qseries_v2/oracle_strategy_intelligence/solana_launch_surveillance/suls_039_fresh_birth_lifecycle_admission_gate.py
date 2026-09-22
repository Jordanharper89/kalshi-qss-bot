from __future__ import annotations
import json,time
MAX_AGE_SECONDS=5.0
def gate(root,now=None):
 now=float(time.time() if now is None else now)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  age=max(0.0,now-float(e["block_time"]))
  rows.append({"event_id":e["event_id"],"age_seconds":age,
   "fresh_birth_admitted":age<=MAX_AGE_SECONDS,"max_age_seconds":MAX_AGE_SECONDS})
 return {"revision":"SULS_039","rows":rows,
  "fresh_birth_count":sum(x["fresh_birth_admitted"] for x in rows),
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/fresh_birth_lifecycle_admission.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
