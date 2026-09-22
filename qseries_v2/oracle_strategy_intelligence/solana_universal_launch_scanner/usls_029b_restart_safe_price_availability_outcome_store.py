from __future__ import annotations
import json,time
from pathlib import Path

def merge(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"pump_sampled_path_outcomes.json").read_text(encoding="utf-8"))
 p=base/"pump_prospective_outcome_store.json"
 old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"revision":"USLS_029B","cases":{}}
 key=src["signature"];case=(old.get("cases") or {}).get(key,{})
 prior={int(x["horizon_seconds"]):x for x in case.get("points") or []}
 for x in src["points"]:prior[int(x["horizon_seconds"])]=x
 case={"signature":key,"token_address":src["token_address"],"quote_mint":src["quote_mint"],
  "anchor_horizon_seconds":src["anchor_horizon_seconds"],
  "points":[prior[h] for h in sorted(prior)],"sampled_mfe":src["sampled_mfe"],
  "sampled_mae":src["sampled_mae"],"price_available_count":src["price_available_count"],
  "price_unavailable_count":src["price_unavailable_count"],
  "pending_horizons":src["remaining_horizons"],"semantics":src["semantics"],
  "updated_unix":time.time(),"profitability_eligible":False,"execution_authority":False}
 old["revision"]="USLS_029B";old["cases"][key]=case;old["execution_authority"]=False;old["read_only"]=True
 p.write_text(json.dumps(old,indent=2,sort_keys=True),encoding="utf-8");return p,old

def write(root):return merge(root)
