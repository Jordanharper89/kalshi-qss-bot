from pathlib import Path
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
def _dec(v):
 try:return Decimal(str(v)) if v is not None else None
 except (InvalidOperation,ValueError,TypeError):return None
def _dt(v):
 if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))
 except:return None
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_053_proven_current_market_history import read_latest_current_market_history
OIAR_074_BUILD_ID="OIAR-074"
def build_current_temporal_evidence(root=None):
 x=read_latest_current_market_history(root); 
 if not x:raise RuntimeError("OIAR-053 current history unavailable")
 out=[]
 for m in x["markets"]:
  h=list(m.get("history") or []); prices=[(_dt(r.get("observed_at")),_dec(r.get("last_price_dollars"))) for r in h];prices=[z for z in prices if z[1] is not None]
  chronological=sorted(prices,key=lambda z:z[0] or datetime.min.replace(tzinfo=timezone.utc))
  first=chronological[0][1] if chronological else None;last=chronological[-1][1] if chronological else None;chg=(last-first) if first is not None and last is not None else None
  direction="UP" if chg is not None and chg>0 else "DOWN" if chg is not None and chg<0 else "FLAT_OR_UNKNOWN"
  out.append({"market_id":m["market_ticker"],"history_rows":len(h),"priced_rows":len(prices),"first_price":None if first is None else str(first),"latest_price":None if last is None else str(last),"price_change":None if chg is None else str(chg),"temporal_direction":direction})
 return {"schema_version":"OIAR-074","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}
def physical_probe(root=None):
 x=build_current_temporal_evidence(root);return {"markets":x["market_count"],"repeated_history":sum(m["history_rows"]>=2 for m in x["markets"]),"priced":sum(m["priced_rows"]>=2 for m in x["markets"]),"probability_enabled":False,"execution_authority":False}
