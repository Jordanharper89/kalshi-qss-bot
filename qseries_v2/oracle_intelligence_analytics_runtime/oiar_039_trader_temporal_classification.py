from datetime import datetime,timezone
from pathlib import Path
from .oiar_038_event_time_snapshot_materializer import read_latest_event_time_snapshot
OIAR_039_BUILD_ID="OIAR-039";EXECUTION_AUTHORITY=False
def _dt(v):
 if not v:return None
 try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(timezone.utc)
 except Exception:return None
def classify_market_time(row,now=None):
 now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);close=_dt(row.get("source_close_time"));open_=_dt(row.get("source_open_time"))
 if close is None:return {"label":"UNKNOWN","proven":False,"event_time":None}
 ln=now.astimezone();lc=close.astimezone()
 if lc.date()==ln.date():label="TONIGHT" if lc.hour>=17 else "TODAY"
 elif (lc.date()-ln.date()).days==1:label="TOMORROW"
 elif close<now:label="PAST"
 else:label="UPCOMING"
 return {"label":label,"proven":True,"event_time":close.isoformat(),"open_time":open_.isoformat() if open_ else None}
def build_temporal_map(root=None,now=None):
 p=read_latest_event_time_snapshot(Path(root or Path.cwd()).resolve())
 if not p:raise RuntimeError("OIAR-039 requires OIAR-038 event-time snapshot")
 return {str(r.get("market_id")):classify_market_time(r,now) for r in p.get("markets",[]) if r.get("market_id")}
def physical_probe(root=None):
 x=build_temporal_map(root);counts={}
 for v in x.values():counts[v["label"]]=counts.get(v["label"],0)+1
 return {"markets":len(x),"classifications":counts,"execution_authority":False}
