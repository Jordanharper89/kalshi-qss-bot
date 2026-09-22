
from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime,timezone
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief
from .oiar_021_indexed_snapshot_identity_materializer import read_latest_indexed_snapshot_identity
from .oiar_042_fresh_current_cohort_identity_refresh import refresh_current_cohort_identity

OIAR_043_BUILD_ID="OIAR-043"
OIAR_043_REVISION="OIAR_043_CURRENT_TRADER_COHORT_TEMPORAL_BRIDGE_V1"
STAGE="current_trader_cohort_temporal_bridge"
EXECUTION_AUTHORITY=False

def materialize_current_trader_cohort_temporal_bridge(root=None):
    root=Path(root or Path.cwd()).resolve()
    refresh_current_cohort_identity(root)
    identity=read_latest_indexed_snapshot_identity(root)
    trader=read_fast_trader_brief(root,50)
    imap={str(x.get("market_id") or ""):x for x in identity.get("markets",[]) if isinstance(x,dict)}
    rows=[]
    for raw in trader.markets:
        m=dict(raw);mid=str(m.get("market_id") or "")
        ident=imap.get(mid,{})
        m["source_open_time"]=ident.get("source_open_time")
        m["source_close_time"]=ident.get("source_close_time")
        m["identity_observed_at"]=ident.get("identity_observed_at")
        m["temporal_identity_resolved"]=bool(ident)
        rows.append(m)
    body={"schema_version":"OIAR-043","stage":STAGE,"market_count":len(rows),"markets":rows,"execution_authority":False}
    h=stable_hash(body);sid="oiar-043-"+h[:32]
    with connect(root,autocommit=False) as c:
        with c.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,STAGE,"OIAR-043",OIAR_043_BUILD_ID,datetime.now(timezone.utc),len(rows),json.dumps(body,sort_keys=True,default=str),h),
            )
        c.commit()
    return {"snapshot_id":sid,"market_count":len(rows),"resolved_temporal_identity":sum(bool(r["temporal_identity_resolved"]) for r in rows),"execution_authority":False}

def physical_probe(root=None):
    return materialize_current_trader_cohort_temporal_bridge(root)
