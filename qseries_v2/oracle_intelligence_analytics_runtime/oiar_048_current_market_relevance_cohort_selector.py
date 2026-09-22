
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_047_production_kalshi_current_eligibility_boundary import read_current_kalshi_markets,_dt
OIAR_048_BUILD_ID="OIAR-048";STAGE="production_current_trader_cohort";EXECUTION_AUTHORITY=False
def select_current_trader_cohort(root=None,limit=100,now=None):
 root=Path(root or Path.cwd()).resolve();now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);rows,meta=read_current_kalshi_markets(root,now=now)
 ranked=[]
 for x in rows:
  expected=_dt(x.expected_expiration_time);close=_dt(x.close_time or x.expiration_time);end=expected or close
  secs=(end-now).total_seconds() if end else 10**15
  ranked.append((secs,x))
 ranked.sort(key=lambda z:(z[0],z[1].ticker));chosen=[x for _,x in ranked[:max(1,min(int(limit),100))]]
 if not chosen:raise RuntimeError("OIAR-048 empty current cohort")
 markets=[{"market_ticker":x.ticker,"event_ticker":x.event_ticker,"market_title":x.title,"status":x.status,"open_time":x.open_time,"close_time":x.close_time,"expiration_time":x.expiration_time,"expected_expiration_time":x.expected_expiration_time,"updated_time":x.updated_time} for x in chosen]
 payload={"schema_version":"OIAR-048","stage":STAGE,"market_count":len(markets),"markets":markets,"ranking_clock":"expected_expiration_time_then_close_time","read_only_source":True,"execution_authority":False}
 h=stable_hash(payload);sid="oiar-048-"+h[:32]
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",(sid,STAGE,"OIAR-048",OIAR_048_BUILD_ID,now,len(markets),json.dumps(payload,sort_keys=True),h))
  c.commit()
 return sid,payload
def physical_probe(root=None):
 sid,p=select_current_trader_cohort(root);return {"snapshot_id":sid,"current_markets":p["market_count"],"active":sum(x["status"]=="active" for x in p["markets"]),"with_expected_expiration":sum(bool(x["expected_expiration_time"]) for x in p["markets"]),"execution_authority":False}
