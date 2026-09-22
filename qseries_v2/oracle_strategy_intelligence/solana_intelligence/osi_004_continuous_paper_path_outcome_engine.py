from __future__ import annotations
from datetime import datetime,timezone
def _dt(v):
 d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
 if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc)

def grade(thesis:dict,path:list[dict])->dict:
 freeze=_dt(thesis["freeze_at"]);end=freeze.timestamp()+int(thesis["horizon_seconds"])
 pts=[]
 for x in path:
  if x.get("price") is None or not x.get("observed_at"):continue
  t=_dt(x["observed_at"])
  if t<freeze or t.timestamp()>end:continue
  pts.append((t,float(x["price"])))
 pts.sort(key=lambda x:x[0])
 if len(pts)<2:raise ValueError("insufficient future path")
 entry=pts[0][1];rets=[p/entry-1 for _,p in pts]
 friction=float((thesis.get("thesis_metadata") or {}).get("friction_bps",200))/10000
 target=(thesis.get("thesis_metadata") or {}).get("target_return")
 stop=(thesis.get("thesis_metadata") or {}).get("economic_stop_return")
 return {
  "thesis_id":thesis["thesis_id"],"horizon_seconds":thesis["horizon_seconds"],
  "entry_price":entry,"exit_price":pts[-1][1],"raw_return":rets[-1],
  "net_return_after_friction":rets[-1]-friction,"mfe":max(rets),"mae":min(rets),
  "target_hit":False if target is None else any(r>=float(target) for r in rets),
  "economic_stop_hit":False if stop is None else any(r<=float(stop) for r in rets),
  "path_points":len(pts),"paper_only":True,"execution_authority":False
 }
