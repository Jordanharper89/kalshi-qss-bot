from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable

EXECUTION_AUTHORITY=False
READ_ONLY=True

def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def synchronize(seed:dict,evidence:Iterable[dict],freeze_at:str,lookback_seconds:int=120)->dict:
    freeze=_dt(freeze_at); lower=freeze.timestamp()-lookback_seconds
    rows=[]
    for e in evidence:
        if e.get("asset_key")!=seed.get("asset_key") or not e.get("observed_at") or not e.get("source"): continue
        t=_dt(e["observed_at"])
        if t>freeze or t.timestamp()<lower: continue
        x=dict(e);x["observed_at"]=t.isoformat();rows.append(x)
    rows.sort(key=lambda x:(x["observed_at"],str(x["source"]),str(x.get("evidence_id",""))))
    sources=sorted({str(x["source"]) for x in rows})
    return {
      "opportunity_seed_id":seed["opportunity_seed_id"],"asset_key":seed["asset_key"],
      "freeze_at":freeze.isoformat(),"evidence":rows,"independent_sources":sources,
      "source_count":len(sources),"future_excluded":True,
      "execution_authority":False,"read_only":True
    }
