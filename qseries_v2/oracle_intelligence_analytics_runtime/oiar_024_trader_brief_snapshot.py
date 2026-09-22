
from __future__ import annotations
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_023_trader_context_snapshot import TRADER_CONTEXT_STAGE,read_latest_trader_context

OIAR_024_BUILD_ID="OIAR-024"
OIAR_024_REVISION="OIAR_024_TRADER_BRIEF_SNAPSHOT_V1"
TRADER_BRIEF_STAGE="trader_brief"

def _plain_reason(m):
    if m["setup_status"]=="WORTH_WATCHING_NOW":
        return "Current evidence has cleared Oracle's research threshold."
    if m["setup_status"]=="SETUP_FORMING":
        return "Oracle sees a setup forming, but it has not fully cleared the research threshold yet."
    if m["historical_strength"]=="STRONG" and m["live_evidence"] in ("WEAK","DEVELOPING"):
        return "Oracle knows this market family well, but current live evidence is not strong enough to confirm an edge."
    return "Current evidence does not justify a directional edge."

def materialize_trader_brief(root=None):
    root=Path(root or Path.cwd()).resolve()
    ctx=read_latest_trader_context(root)
    if ctx is None:raise RuntimeError("OIAR-024 requires OIAR-023 context snapshot")
    markets=[]
    for m in ctx.get("markets",[]):
        takeaway="WORTH WATCHING NOW" if m["setup_status"]=="WORTH_WATCHING_NOW" else "WATCH - SETUP FORMING" if m["setup_status"]=="SETUP_FORMING" else "NO EDGE RIGHT NOW"
        markets.append({
            **m,
            "why":_plain_reason(m),
            "what_would_improve_it":"More live history and a directional setup that clears Oracle's usefulness/candidate thresholds.",
            "trader_takeaway":takeaway,
        })
    body={"schema_version":"OIAR-024","stage":TRADER_BRIEF_STAGE,"source_stage":TRADER_CONTEXT_STAGE,"market_count":len(markets),"markets":markets,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-024-"+h[:32]
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) "
                "VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",
                (sid,TRADER_BRIEF_STAGE,"OIAR-024",OIAR_024_BUILD_ID,len(markets),json.dumps(body,sort_keys=True),h),
            )
    return sid,body

def read_latest_trader_brief(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(TRADER_BRIEF_STAGE,))
            row=cur.fetchone()
        conn.rollback()
    if row is None:return None
    payload,ph=row
    if isinstance(payload,str):payload=json.loads(payload)
    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-024 persisted hash mismatch")
    return payload
