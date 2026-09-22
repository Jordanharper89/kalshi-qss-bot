
from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime,timezone
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_039_trader_temporal_classification import classify_market_time
from .oiar_043_current_trader_cohort_temporal_bridge import STAGE as BRIDGE_STAGE

OIAR_044_BUILD_ID="OIAR-044"
OIAR_044_REVISION="OIAR_044_PROVEN_CURRENT_DAY_TRADER_SNAPSHOT_V1"
STAGE="proven_current_day_trader_snapshot"
EXECUTION_AUTHORITY=False

def _latest_bridge(root):
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(BRIDGE_STAGE,))
            row=cur.fetchone()
        c.rollback()
    if not row: raise RuntimeError("OIAR-044 requires OIAR-043 bridge snapshot")
    p,h=row
    if isinstance(p,str): p=json.loads(p)
    if stable_hash(p)!=str(h): raise RuntimeError("OIAR-044 bridge hash mismatch")
    return p

def materialize_proven_current_day_snapshot(root=None,now=None):
    root=Path(root or Path.cwd()).resolve();src=_latest_bridge(root);now=now or datetime.now(timezone.utc)
    rows=[]
    counts={}
    for raw in src.get("markets",[]):
        m=dict(raw);t=classify_market_time(m,now);m["time_relevance"]=t
        counts[t["label"]]=counts.get(t["label"],0)+1
        if t["label"] in ("TODAY","TONIGHT"):
            rows.append(m)
    body={"schema_version":"OIAR-044","stage":STAGE,"market_count":len(rows),"source_market_count":src.get("market_count",0),"classification_counts":counts,"markets":rows,"execution_authority":False}
    h=stable_hash(body);sid="oiar-044-"+h[:32]
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,STAGE,"OIAR-044",OIAR_044_BUILD_ID,now,len(rows),json.dumps(body,sort_keys=True,default=str),h),
            )
        c.commit()
    return {"snapshot_id":sid,"today_markets":len(rows),"classification_counts":counts,"execution_authority":False}

def physical_probe(root=None):
    return materialize_proven_current_day_snapshot(root)
