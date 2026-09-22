from __future__ import annotations
import json,time
from pathlib import Path
def observe(root:Path,seconds:int=10,interval:float=1.0)->dict:
 p=root/"runtime_state/solana_intelligence/osi_live_child_status.json";samples=[];end=time.time()+seconds
 while time.time()<end:
  if p.is_file():
   try:
    x=json.loads(p.read_text(encoding="utf-8"));samples.append({"cycle_count":int(x.get("cycle_count") or 0),"fresh_opportunities":int(x.get("fresh_opportunities") or 0),"normalized_event_count":int(x.get("normalized_event_count") or 0),"state":x.get("state"),"error":x.get("error")})
   except Exception: pass
  time.sleep(interval)
 cycles=[x["cycle_count"] for x in samples]
 return {"sample_count":len(samples),"cycle_progression":len(set(cycles))>1,"min_cycle":min(cycles) if cycles else 0,"max_cycle":max(cycles) if cycles else 0,"fresh_total":sum(x["fresh_opportunities"] for x in samples),"normalized_event_total":sum(x["normalized_event_count"] for x in samples),"latest_state":samples[-1]["state"] if samples else None,"latest_error":samples[-1]["error"] if samples else None,"execution_authority":False,"read_only":True}
