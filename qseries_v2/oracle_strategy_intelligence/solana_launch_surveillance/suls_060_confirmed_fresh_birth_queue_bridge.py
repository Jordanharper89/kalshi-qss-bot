from __future__ import annotations
import json
H=(1,5,15,30,60,300,900)
MAX_AGE=5.0

def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 ep=b/"confirmed_tradeable_birth_events.json"
 src=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 qp=b/"confirmed_fresh_birth_horizon_queue.json"
 old=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"queue":[]}
 q=list(old.get("queue") or []);keys={(x["event_id"],x["horizon_seconds"]) for x in q};adm=0
 for e in src.get("events",[]):
  age=e.get("trigger_age_seconds")
  if age is None or float(age)>MAX_AGE:continue
  adm+=1
  for h in H:
   k=(e["event_id"],h)
   if k in keys:continue
   q.append({"event_id":e["event_id"],"signature":e["signature"],"horizon_seconds":h,
    "target_unix":float(e["block_time"])+h,"state":"PENDING",
    "token_vault":e["token_vault"],"quote_vault":e["quote_vault"],
    "birth_token_amount":e["initial_token_amount"],"birth_quote_amount":e["initial_quote_amount"],
    "trigger_commitment":"confirmed","execution_authority":False});keys.add(k)
 out={"revision":"SULS_060","admitted_fresh_births":adm,
      "pending_count":sum(x["state"]=="PENDING" for x in q),"queue":q,
      "execution_authority":False,"read_only":True}
 qp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
