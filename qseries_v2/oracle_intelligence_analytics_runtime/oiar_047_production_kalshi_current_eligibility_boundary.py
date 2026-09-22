
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
OIAR_047_BUILD_ID="OIAR-047";OIAR_047_REVISION="OIAR_047_PRODUCTION_KALSHI_CURRENT_ELIGIBILITY_BOUNDARY_V1";EXECUTION_AUTHORITY=False
@dataclass(frozen=True)
class CurrentKalshiMarket:
 ticker:str;event_ticker:str;title:str;status:str;open_time:str|None;close_time:str|None;expiration_time:str|None;expected_expiration_time:str|None;updated_time:str|None;read_only:bool=True;execution_authority:bool=False
def _s(v):
 x=str(v or "").strip();return x or None
def _dt(v):
 if not v:return None
 try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(timezone.utc)
 except Exception:return None
def read_current_kalshi_markets(root=None,max_pages=5,timeout_seconds=15,now=None):
 root=Path(root or Path.cwd()).resolve();now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);creds=load_kalshi_credentials(root=root)
 cursor="";seen={};statuses={};pages=0
 while pages<int(max_pages):
  params={"limit":1000}
  if cursor:params["cursor"]=cursor
  r=kalshi_rest_get(creds,"/markets",params,timeout_seconds)
  if int(r.status_code)!=200:raise RuntimeError(f"Kalshi /markets returned {r.status_code}")
  b=r.body if isinstance(r.body,dict) else {}
  for raw in b.get("markets",()):
   status=str(raw.get("status") or "").strip().lower();statuses[status]=statuses.get(status,0)+1
   ticker=str(raw.get("ticker") or "").strip().upper();event=str(raw.get("event_ticker") or "").strip().upper()
   if not ticker or not event:continue
   opened=_dt(raw.get("open_time"));expected=_dt(raw.get("expected_expiration_time"));close=_dt(raw.get("close_time") or raw.get("expiration_time"))
   # Physical production evidence established ACTIVE as the current/trading state.
   if status!="active":continue
   if opened is not None and opened>now:continue
   relevance_end=expected or close
   if relevance_end is not None and relevance_end<=now:continue
   seen[ticker]=CurrentKalshiMarket(ticker,event,str(raw.get("title") or "").strip(),status,_s(raw.get("open_time")),_s(raw.get("close_time")),_s(raw.get("expiration_time")),_s(raw.get("expected_expiration_time")),_s(raw.get("updated_time")))
  pages+=1;cursor=str(b.get("cursor") or "").strip()
  if not cursor:break
 rows=tuple(sorted(seen.values(),key=lambda x:x.ticker))
 if not rows:raise RuntimeError("OIAR-047 found no production ACTIVE/current Kalshi markets")
 return rows,{"pages":pages,"pagination_complete":not bool(cursor),"statuses":statuses}
def physical_probe(root=None):
 rows,meta=read_current_kalshi_markets(root)
 return {"eligible_current_markets":len(rows),"pages":meta["pages"],"pagination_complete":meta["pagination_complete"],"statuses":meta["statuses"],"with_expected_expiration":sum(bool(x.expected_expiration_time) for x in rows),"execution_authority":False}
