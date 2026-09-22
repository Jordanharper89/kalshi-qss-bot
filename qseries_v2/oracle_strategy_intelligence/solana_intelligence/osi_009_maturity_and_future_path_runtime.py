from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_004_continuous_paper_path_outcome_engine import grade

def _dt(v):
 d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
 if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc)

def mature(theses:list[dict],paths:dict[str,list[dict]],now_iso:str,outcome_path:Path)->dict:
 now=_dt(now_iso);out=[]
 for t in theses:
  end=_dt(t["freeze_at"]).timestamp()+int(t["horizon_seconds"])
  if now.timestamp()<end:continue
  path=paths.get(t["thesis_id"],[])
  try:o=grade(t,path)
  except ValueError:continue
  out.append(o)
 outcome_path.parent.mkdir(parents=True,exist_ok=True)
 outcome_path.write_text(json.dumps({"outcomes":out,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
 return {"matured":out,"matured_count":len(out),"execution_authority":False}
