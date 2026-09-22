from pathlib import Path
from .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief
from .oiar_039_trader_temporal_classification import build_temporal_map
OIAR_040_BUILD_ID="OIAR-040";EXECUTION_AUTHORITY=False
def requested_window(query):
 q=" ".join(str(query).lower().split())
 if "tonight" in q or "this evening" in q:return "TONIGHT"
 if "today" in q:return "TODAY"
 if "tomorrow" in q:return "TOMORROW"
 if "upcoming" in q:return "UPCOMING"
 return None
def read_time_filtered_trader_brief(root=None,query="",limit=20):
 root=Path(root or Path.cwd()).resolve();x=read_fast_trader_brief(root,50);tm=build_temporal_map(root);want=requested_window(query);rows=[]
 for raw in x.markets:
  r=dict(raw);t=tm.get(str(r.get("market_id")),{"label":"UNKNOWN","proven":False,"event_time":None});r["time_relevance"]=t
  if want=="TODAY" and t["label"] not in ("TODAY","TONIGHT"):continue
  if want and want!="TODAY" and t["label"]!=want:continue
  rows.append(r)
 return tuple(rows[:max(1,min(int(limit),50))])
def physical_probe(root=None):
 a=read_time_filtered_trader_brief(root,"",50);b=read_time_filtered_trader_brief(root,"plays for today",50)
 return {"all_markets":len(a),"today_markets":len(b),"unknown_all":sum(r["time_relevance"]["label"]=="UNKNOWN" for r in a),"execution_authority":False}
