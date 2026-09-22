from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_021_indexed_snapshot_identity_materializer import read_latest_indexed_snapshot_identity
from .oiar_037_snapshot_event_time_source_discovery import discover_event_time_sources
OIAR_038_BUILD_ID="OIAR-038";STAGE="trader_event_time_snapshot";EXECUTION_AUTHORITY=False
def materialize_event_time_snapshot(root=None):
 root=Path(root or Path.cwd()).resolve();d=discover_event_time_sources(root);src=read_latest_indexed_snapshot_identity(root)
 markets=[{"market_id":r.get("market_id"),"source_open_time":r.get("source_open_time"),"source_close_time":r.get("source_close_time"),"identity_observed_at":r.get("identity_observed_at"),"time_source":"OIAR-021:indexed_market_snapshot"} for r in src.get("markets",[])]
 body={"schema_version":"OIAR-038","stage":STAGE,"market_count":len(markets),"markets":markets,"source_discovery":d,"execution_authority":False};ph=stable_hash(body);sid="oiar-038-"+ph[:32]
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",(sid,STAGE,"OIAR-038",OIAR_038_BUILD_ID,datetime.now(timezone.utc),len(markets),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),ph))
  c.commit()
 return {"snapshot_id":sid,"market_count":len(markets),"close_times":sum(bool(x["source_close_time"]) for x in markets),"open_times":sum(bool(x["source_open_time"]) for x in markets),"execution_authority":False}
def read_latest_event_time_snapshot(root=None):
 root=Path(root or Path.cwd()).resolve()
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,));row=cur.fetchone()
  c.rollback()
 if not row:return None
 p,h=row
 if isinstance(p,str):p=json.loads(p)
 if stable_hash(p)!=str(h):raise RuntimeError("OIAR-038 snapshot hash mismatch")
 return p
def physical_probe(root=None):return materialize_event_time_snapshot(root)
