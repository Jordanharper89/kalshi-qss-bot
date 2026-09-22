from __future__ import annotations
import json,time
HORIZONS=(1,5,15,30,60,300,900)
MAX_ADMISSION_AGE=5.0
def run(root,now=None):
 now=float(time.time() if now is None else now)
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 ep=base/"continuous_tradeable_birth_events.json"
 src=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 qp=base/"fresh_birth_horizon_queue.json"
 old=json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {"queue":[]}
 queue=list(old.get("queue") or []);keys={(x["event_id"],x["horizon_seconds"]) for x in queue};admitted=0
 for e in src.get("events",[]):
  age=max(0.0,now-float(e["block_time"]))
  if age>MAX_ADMISSION_AGE:continue
  admitted+=1
  for h in HORIZONS:
   k=(e["event_id"],h)
   if k in keys:continue
   queue.append({"event_id":e["event_id"],"signature":e["signature"],"horizon_seconds":h,
    "target_unix":float(e["block_time"])+h,"state":"PENDING","token_vault":e["token_vault"],
    "quote_vault":e["quote_vault"],"birth_token_amount":e["initial_token_amount"],
    "birth_quote_amount":e["initial_quote_amount"],"execution_authority":False});keys.add(k)
 out={"revision":"SULS_043","admitted_fresh_births":admitted,"pending_count":sum(x["state"]=="PENDING" for x in queue),
  "queue":queue,"execution_authority":False,"read_only":True}
 qp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
