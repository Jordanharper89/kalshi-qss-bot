from __future__ import annotations
import json
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

def probe(root,limit=512):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 d=json.loads((b/"confirmed_tradeable_birth_events.json").read_text(encoding="utf-8"))
 rows=[];covered=0;priced=0
 for e in d.get("events",[]):
  token=e.get("token_address");pair=e.get("pair_address")
  hist=tuple(read_pinned_pool_history(token,root=root,limit=limit)) if token else ()
  hp=[]
  for r in hist:
   pools=tuple((r.payload or {}).get("pools") or ())
   if pair and any(str(p.get("pair_address") or "")==str(pair) and p.get("price_usd") is not None for p in pools):
    hp.append(r)
  if hist:covered+=1
  if hp:priced+=1
  rows.append({"signature":e.get("signature"),"token_address":token,"pair_address":pair,
   "history_records":len(hist),"priced_pair_records":len(hp),
   "first_observed_at":hist[0].observed_at if hist else None,
   "last_observed_at":hist[-1].observed_at if hist else None})
 return {"revision":"SULS_098","event_count":len(rows),"history_covered_events":covered,
  "priced_pair_covered_events":priced,"rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/launch_cohort_temporal_coverage.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
